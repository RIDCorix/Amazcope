"""Service for generating product listing optimization suggestions using OpenAI."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from optimization.models import Suggestion
from products.models import Product, ProductSnapshot
from schemas.optimization import OptimizationReport, SuggestionResponse

logger = logging.getLogger(__name__)


class OptimizationService:
    """Service for AI-powered listing optimization suggestions."""

    def __init__(self) -> None:
        """Initialize optimization service with OpenAI client."""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")

        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"  # Use GPT-4 for better analysis

    async def generate_suggestions(
        self,
        db: AsyncSession,
        product: Product,
        include_competitors: bool = True,
        suggestion_types: list[str] | None = None,
    ) -> OptimizationReport:
        """Generate optimization suggestions for a product.

        Args:
            product: Product to analyze
            include_competitors: Include competitor analysis
            suggestion_types: Specific types to generate (None = all types)

        Returns:
            OptimizationReport with suggestions
        """
        logger.info(f"Generating optimization suggestions for product {product.asin}")

        # Check cache first
        cached_report = await self._get_cached_suggestions(db, product.id)
        if cached_report:
            logger.info(f"Using cached suggestions for product {product.asin}")
            return cached_report

        # Prepare product data for analysis
        product_data = await self._prepare_product_data(db, product, include_competitors)

        # Generate suggestions using OpenAI
        suggestions = await self._call_openai_for_suggestions(product_data, suggestion_types)

        # Calculate overall score
        overall_score = self._calculate_overall_score(suggestions)

        # Determine top priority
        top_priority = self._determine_top_priority(suggestions)

        # Create report
        report = OptimizationReport(
            product_id=product.id,
            product_title=product.title,
            generated_at=datetime.utcnow(),
            suggestions=suggestions,
            overall_score=overall_score,
            top_priority=top_priority,
            cache_hit=False,
        )

        # Save suggestions to database
        await self._save_suggestions(db, product, suggestions)

        # Cache the report
        await self._cache_suggestions(product.id, report)

        return report

    async def _prepare_product_data(
        self, db: AsyncSession, product: Product, include_competitors: bool
    ) -> dict[str, Any]:
        """Prepare product data for AI analysis."""
        # Fetch latest snapshot
        from products.models import Review

        stmt = (
            select(ProductSnapshot)
            .where(ProductSnapshot.product_id == product.id)
            .order_by(ProductSnapshot.scraped_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        snapshot = result.scalar_one_or_none()

        # Fetch recent reviews
        stmt_reviews = (
            select(Review)
            .where(Review.product_id == product.id)
            .order_by(Review.review_date.desc())
            .limit(10)
        )
        result_reviews = await db.execute(stmt_reviews)
        reviews = result_reviews.scalars().all()

        # Fetch competitor data if requested
        competitors: list[Any] = []
        if include_competitors and snapshot and snapshot.price:
            # Get products in same category with similar price range
            price_range = (float(snapshot.price) * 0.8, float(snapshot.price) * 1.2)
            stmt_competitors = (
                select(ProductSnapshot)
                .join(Product)
                .where(
                    Product.category == product.category,
                    ProductSnapshot.price >= price_range[0],
                    ProductSnapshot.price <= price_range[1],
                    Product.id != product.id,
                )
                .order_by(ProductSnapshot.scraped_at.desc())
                .limit(5)
            )
            result_competitors = await db.execute(stmt_competitors)
            competitor_snapshots = result_competitors.scalars().all()

            # Get competitor products
            competitor_product_ids = [cs.product_id for cs in competitor_snapshots]
            if competitor_product_ids:
                stmt_comp_products = select(Product).where(Product.id.in_(competitor_product_ids))
                result_comp_products = await db.execute(stmt_comp_products)
                competitors = result_comp_products.scalars().all()

        return {
            "product": {
                "asin": product.asin,
                "title": product.title,
                "brand": product.brand,
                "price": float(snapshot.price) if snapshot and snapshot.price else None,
                "original_price": float(snapshot.original_price)
                if snapshot and snapshot.original_price
                else None,
                "rating": snapshot.rating if snapshot else None,
                "review_count": snapshot.review_count if snapshot else 0,
                "main_category": product.category,
                "small_category": product.small_category,
                "in_stock": snapshot.in_stock if snapshot else False,
                "image_url": product.image_url,
            },
            "snapshot": {
                "bsr_main": snapshot.bsr_main_category if snapshot else None,
                "bsr_small": snapshot.bsr_small_category if snapshot else None,
            },
            "reviews": [
                {
                    "rating": review.rating,
                    "title": review.title,
                    "text": (review.text[:200] if review.text else ""),  # Truncate for API limits
                    "verified": review.verified_purchase,
                }
                for review in reviews
            ],
            "competitors": [
                {
                    "title": comp.title,
                    "price": None,  # Would need to fetch latest snapshot for each competitor
                    "rating": None,
                    "review_count": None,
                }
                for comp in competitors
            ],
        }

    async def _call_openai_for_suggestions(
        self, product_data: dict[str, Any], suggestion_types: list[str] | None
    ) -> list[SuggestionResponse]:
        """Call OpenAI API to generate suggestions."""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(product_data, suggestion_types)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000,
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("OpenAI returned None content")
            result = json.loads(content)

            # Parse suggestions from response
            suggestions = []
            for suggestion_data in result.get("suggestions", []):
                suggestions.append(
                    SuggestionResponse(
                        suggestion_type=suggestion_data.get("type", "general"),
                        priority=suggestion_data.get("priority", "medium"),
                        title=suggestion_data.get("title", ""),
                        description=suggestion_data.get("description", ""),
                        reasoning=suggestion_data.get("reasoning", ""),
                        current_value=suggestion_data.get("current_value"),
                        suggested_value=suggestion_data.get("suggested_value"),
                        expected_impact=suggestion_data.get("expected_impact"),
                        impact_score=suggestion_data.get("impact_score", 50.0),
                        effort_score=suggestion_data.get("effort_score", 50.0),
                        confidence_score=suggestion_data.get("confidence_score", 70.0),
                        metadata=suggestion_data.get("metadata", {}),
                    )
                )

            # Sort by impact score (highest first)
            suggestions.sort(key=lambda x: x.impact_score, reverse=True)

            return suggestions

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            # Return fallback suggestions
            return self._get_fallback_suggestions(product_data)

    def _build_system_prompt(self) -> str:
        """Build system prompt for OpenAI."""
        return """You are an expert Amazon product listing optimization consultant with deep knowledge of:
- Amazon SEO and keyword optimization
- Competitive pricing strategies
- Conversion rate optimization
- Product photography best practices
- Amazon A9 algorithm ranking factors

Your task is to analyze product listings and provide actionable, prioritized optimization suggestions.

For each suggestion, provide:
1. Type: title, pricing, description, images, or keywords
2. Priority: low, medium, high, or critical
3. Title: Short, actionable title (max 60 chars)
4. Description: Detailed explanation of what to change
5. Reasoning: Why this matters (data-driven if possible)
6. Current Value: What the listing currently has
7. Suggested Value: Your recommended improvement
8. Expected Impact: Quantifiable expected improvement (e.g., "10-15% conversion increase")
9. Impact Score: 0-100 (how much this will improve performance)
10. Effort Score: 0-100 (lower = easier to implement)
11. Confidence Score: 0-100 (your confidence in this recommendation)

Return your analysis as a JSON object with a "suggestions" array."""

    def _build_user_prompt(
        self, product_data: dict[str, Any], suggestion_types: list[str] | None
    ) -> str:
        """Build user prompt with product data."""
        types_filter = (
            f"Focus only on these suggestion types: {', '.join(suggestion_types)}"
            if suggestion_types
            else "Analyze all aspects of the listing."
        )

        return f"""Analyze this Amazon product listing and provide optimization suggestions:

Product Data:
{json.dumps(product_data, indent=2)}

{types_filter}

Provide 3-7 high-impact suggestions ranked by priority. Consider:
- Title optimization (keywords, character count, clarity)
- Pricing strategy (compared to competitors)
- Product description gaps
- Image quality/quantity issues
- Missing critical information

Return your analysis in this JSON format:
{{
    "suggestions": [
        {{
            "type": "title",
            "priority": "high",
            "title": "Add High-Volume Keywords to Title",
            "description": "Current title is missing key search terms...",
            "reasoning": "Products with these keywords rank 30% higher...",
            "current_value": "Current title text",
            "suggested_value": "Improved title with keywords",
            "expected_impact": "15-20% increase in organic visibility",
            "impact_score": 85,
            "effort_score": 20,
            "confidence_score": 90,
            "metadata": {{"keywords": ["keyword1", "keyword2"]}}
        }}
    ]
}}"""

    def _get_fallback_suggestions(self, product_data: dict[str, Any]) -> list[SuggestionResponse]:
        """Return basic suggestions if OpenAI fails."""
        product = product_data["product"]
        suggestions = []

        # Title length check
        if len(product["title"]) < 80:
            suggestions.append(
                SuggestionResponse(
                    suggestion_type="title",
                    priority="high",
                    title="Expand Title Length",
                    description="Your title is shorter than optimal. Amazon allows up to 200 characters.",
                    reasoning="Longer titles with relevant keywords improve discoverability.",
                    current_value=product["title"],
                    suggested_value=f"{product['title']} [Add relevant keywords here]",
                    expected_impact="10-15% increase in search visibility",
                    impact_score=75.0,
                    effort_score=20.0,
                    confidence_score=85.0,
                )
            )

        # Review count check
        if product["review_count"] < 50:
            suggestions.append(
                SuggestionResponse(
                    suggestion_type="reviews",
                    priority="high",
                    title="Increase Review Count",
                    description="Low review count impacts conversion rate significantly.",
                    reasoning="Products with 50+ reviews convert 20% better on average.",
                    current_value=f"{product['review_count']} reviews",
                    suggested_value="Target 50+ reviews through follow-up campaigns",
                    expected_impact="15-25% conversion increase",
                    impact_score=80.0,
                    effort_score=70.0,
                    confidence_score=90.0,
                )
            )

        return suggestions

    def _calculate_overall_score(self, suggestions: list[SuggestionResponse]) -> float:
        """Calculate overall listing quality score based on suggestions."""
        if not suggestions:
            return 85.0  # Default good score

        # Average of (100 - impact_score) for all suggestions
        # Higher impact scores mean more room for improvement
        total_impact = sum(s.impact_score for s in suggestions)
        avg_impact = total_impact / len(suggestions)

        # Invert: high impact suggestions = lower current quality
        score = 100 - (avg_impact * 0.8)
        return max(0.0, min(100.0, score))

    def _determine_top_priority(self, suggestions: list[SuggestionResponse]) -> str:
        """Determine the most impactful improvement area."""
        if not suggestions:
            return "No immediate improvements needed"

        # Find suggestion with highest impact score
        top_suggestion = max(suggestions, key=lambda x: x.impact_score)
        return top_suggestion.title

    async def _save_suggestions(
        self, db: AsyncSession, product: Product, suggestions: list[SuggestionResponse]
    ) -> None:
        """Save suggestions to database."""
        for suggestion in suggestions:
            opt_suggestion = Suggestion(
                product_id=product.id,
                user_id=product.user_id,
                suggestion_type=suggestion.suggestion_type,
                priority=suggestion.priority,
                title=suggestion.title,
                description=suggestion.description,
                reasoning=suggestion.reasoning,
                current_value=suggestion.current_value,
                suggested_value=suggestion.suggested_value,
                expected_impact=suggestion.expected_impact,
                impact_score=suggestion.impact_score,
                effort_score=suggestion.effort_score,
                confidence_score=suggestion.confidence_score,
                extra_metadata=suggestion.metadata,
            )
            db.add(opt_suggestion)
        await db.commit()

    async def _get_cached_suggestions(
        self, db: AsyncSession, product_id: int
    ) -> OptimizationReport | None:
        """Get cached suggestions if recent enough (24 hours)."""
        # Get most recent suggestions for this product
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        stmt = (
            select(Suggestion)
            .where(
                Suggestion.product_id == product_id,
                Suggestion.created_at >= cutoff_time,
            )
            .order_by(Suggestion.created_at.desc())
        )
        result = await db.execute(stmt)
        recent_suggestions = result.scalars().all()

        if not recent_suggestions:
            return None

        # Group by created_at to get latest batch
        latest_batch = []
        batch_time = recent_suggestions[0].created_at

        for suggestion in recent_suggestions:
            if (suggestion.created_at - batch_time).total_seconds() < 60:  # Within 1 minute
                latest_batch.append(suggestion)
            else:
                break

        if not latest_batch:
            return None

        # Convert to SuggestionResponse objects
        suggestions = [
            SuggestionResponse(
                suggestion_type=s.suggestion_type,
                priority=s.priority,
                title=s.title,
                description=s.description,
                reasoning=s.reasoning,
                current_value=s.current_value,
                suggested_value=s.suggested_value,
                expected_impact=s.expected_impact,
                impact_score=s.impact_score,
                effort_score=s.effort_score,
                confidence_score=s.confidence_score,
                metadata=s.extra_metadata or {},
            )
            for s in latest_batch
        ]

        # Get product
        stmt_product = select(Product).where(Product.id == product_id)
        result_product = await db.execute(stmt_product)
        product = result_product.scalar_one()

        return OptimizationReport(
            product_id=product_id,
            product_title=product.title,
            generated_at=batch_time,
            suggestions=suggestions,
            overall_score=self._calculate_overall_score(suggestions),
            top_priority=self._determine_top_priority(suggestions),
            cache_hit=True,
        )

    async def _cache_suggestions(self, product_id: UUID, report: OptimizationReport) -> None:
        """Cache suggestions (already saved to DB, this is a placeholder for Redis)."""
        # TODO: Implement Redis caching for faster retrieval
        # For now, DB serves as cache with 24-hour check
        pass
