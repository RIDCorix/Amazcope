"""API endpoints for product listing optimization suggestions.

DEPRECATED: This file contains endpoints for ABTest and OptimizationSuggestion models
which were removed in migration eb872cb36cdb. These endpoints are no longer functional.

For AI-powered suggestions, use the /suggestions endpoints which use the Suggestion model.
"""

from fastapi import APIRouter

# NOTE: All endpoints in this file have been deprecated.
# The ABTest and OptimizationSuggestion models were removed.
# Use /api/v1/suggestions endpoints for AI-powered product optimization.

router = APIRouter()
