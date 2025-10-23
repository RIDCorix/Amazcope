import {
  ArrowLeft,
  BarChart3,
  CheckCircle,
  Loader2,
  MessageSquare,
  RefreshCw,
  Star,
  StarHalf,
  TrendingUp,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import BSRTrendChart from '@/components/metrics/BSRTrendChart';
import DynamicTrendChart from '@/components/metrics/DynamicTrendChart';
import MetricsSummaryCards from '@/components/metrics/MetricsSummaryCards';
import PriceTrendChart from '@/components/metrics/PriceTrendChart';
import ProductComparisonChart from '@/components/metrics/ProductComparisonChart';
import ProductMetricsTrendChart from '@/components/metrics/ProductMetricsTrendChart';
import ReviewTrendChart from '@/components/metrics/ReviewTrendChart';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { UpdateCategoryDialog } from '@/components/UpdateCategoryDialog';
import { useTranslation } from '@/hooks/useTranslation';
import {
  productService,
  type BestsellerSnapshot,
  type Product,
  type Review,
  type ReviewStats,
} from '@/services/productService';

export default function ProductDetailWithTabsPage() {
  const params = useParams();
  const navigate = useNavigate();
  const productId = params?.id as string;
  const { toast } = useToast();
  const { t } = useTranslation();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [product, setProduct] = useState<any>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [reviewStats, setReviewStats] = useState<ReviewStats | null>(null);
  const [bestsellers, setBestsellers] = useState<BestsellerSnapshot | null>(
    null
  );
  const [activeTab, setActiveTab] = useState('overview');
  const [userProducts, setUserProducts] = useState<Product[]>([]);

  const fetchProductDetails = useCallback(async () => {
    try {
      const data = await productService.getProduct(productId);
      setProduct(data);
    } catch (error) {
      console.error('Failed to fetch product:', error);
    } finally {
      setLoading(false);
    }
  }, [productId]);

  const fetchReviews = useCallback(async () => {
    try {
      const data = await productService.getReviews(productId, {
        limit: 50,
      });
      setReviews(data);
    } catch (error) {
      console.error('Failed to fetch reviews:', error);
    }
  }, [productId]);

  const fetchReviewStats = useCallback(async () => {
    try {
      const data = await productService.getReviewStats(productId);
      setReviewStats(data);
    } catch (error) {
      console.error('Failed to fetch review stats:', error);
    }
  }, [productId]);

  const fetchBestsellers = useCallback(async () => {
    try {
      const data = await productService.getBestsellers(productId);
      setBestsellers(data);
    } catch (error) {
      console.error('Failed to fetch bestsellers:', error);
    }
  }, [productId]);

  const fetchUserProducts = useCallback(async () => {
    try {
      const data = await productService.getProducts();
      setUserProducts(data);
    } catch (error) {
      console.error('Failed to fetch user products:', error);
    }
  }, []);

  useEffect(() => {
    if (productId) {
      fetchProductDetails();
      fetchUserProducts();
    }
  }, [productId, fetchProductDetails, fetchUserProducts]);

  useEffect(() => {
    if (activeTab === 'reviews' && reviews.length === 0) {
      fetchReviews();
      fetchReviewStats();
    } else if (activeTab === 'bestsellers' && !bestsellers) {
      fetchBestsellers();
    }
  }, [
    activeTab,
    reviews.length,
    bestsellers,
    fetchReviews,
    fetchReviewStats,
    fetchBestsellers,
  ]);

  const handleRefresh = async () => {
    try {
      setRefreshing(true);

      toast({
        title: t('product.refresh.title'),
        description: t('product.refresh.description'),
      });

      const refreshedProduct = await productService.refreshProduct(
        productId,
        true // update metadata
      );

      setProduct(refreshedProduct);

      toast({
        title: t('product.refresh.complete'),
        description: t('product.refresh.completeDescription'),
      });

      // Re-fetch related data if on those tabs
      if (activeTab === 'reviews') {
        await fetchReviews();
        await fetchReviewStats();
      } else if (activeTab === 'bestsellers') {
        await fetchBestsellers();
      }
    } catch (error: any) {
      console.error('Failed to refresh product:', error);
      toast({
        title: t('product.refresh.failed'),
        description:
          error.response?.data?.detail ||
          error.message ||
          t('product.refresh.failedDescription'),
        variant: 'destructive',
      });
    } finally {
      setRefreshing(false);
    }
  };

  const renderStars = (rating: number) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;

    for (let i = 0; i < fullStars; i++) {
      stars.push(
        <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
      );
    }

    if (hasHalfStar) {
      stars.push(
        <StarHalf
          key="half"
          className="w-4 h-4 fill-yellow-400 text-yellow-400"
        />
      );
    }

    const emptyStars = 5 - stars.length;
    for (let i = 0; i < emptyStars; i++) {
      stars.push(<Star key={`empty-${i}`} className="w-4 h-4 text-gray-300" />);
    }

    return <div className="flex items-center gap-1">{stars}</div>;
  };

  const renderRatingBar = (count: number, total: number) => {
    const percentage = total > 0 ? (count / total) * 100 : 0;
    return (
      <div className="flex items-center gap-2">
        <div className="w-24 bg-gray-200 rounded-full h-2">
          <div
            className="bg-yellow-400 h-2 rounded-full"
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span className="text-sm text-gray-600 w-12">{count}</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="text-center">{t('product.notFound')}</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <Button
        variant="ghost"
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        {t('product.backToProducts')}
      </Button>

      {/* Product Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex items-start gap-4 flex-1">
            {product.image_url && (
              <img
                src={product.image_url}
                alt={product.title}
                className="w-32 h-32 object-cover rounded-lg shadow-md"
              />
            )}
            <div className="flex-1">
              <h1 className="text-2xl font-bold mb-2">{product.title}</h1>
              <div className="flex items-center gap-3 mb-2">
                <Badge variant="secondary">{product.asin}</Badge>
                {product.brand && (
                  <span className="text-gray-600">{product.brand}</span>
                )}
                {product.is_active ? (
                  <Badge className="bg-green-600">{t('product.active')}</Badge>
                ) : (
                  <Badge variant="secondary">{t('product.inactive')}</Badge>
                )}
              </div>
              {product.category && (
                <div className="text-sm text-gray-600 space-y-1">
                  <p>
                    {t('product.category')}: {product.category}
                    {product.small_category && ` > ${product.small_category}`}
                  </p>
                  {product.bsr_category_link && (
                    <a
                      href={product.bsr_category_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      {t('product.viewCategoryBestsellers')} →
                    </a>
                  )}
                </div>
              )}
              <div className="mt-4">
                <a
                  href={`https://www.amazon.com/dp/${product.asin}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  {t('product.viewOnAmazon')} →
                </a>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <Button
              onClick={() => navigate(`/products/${productId}/edit`)}
              variant="outline"
              className="flex items-center gap-2"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
              {t('product.editProduct')}
            </Button>
            <UpdateCategoryDialog
              product={product}
              onUpdate={updatedProduct => setProduct(updatedProduct)}
            />
            <Button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2"
              variant="default"
            >
              <RefreshCw
                className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`}
              />
              {refreshing ? t('product.refreshing') : t('product.refreshData')}
            </Button>
          </div>
        </div>

        {/* Last Updated Info */}
        {product.latest_snapshot?.scraped_at && (
          <div className="text-sm text-gray-500">
            {t('product.lastUpdated')}:{' '}
            {new Date(product.latest_snapshot.scraped_at).toLocaleString()}
          </div>
        )}
      </div>
      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4 mb-6">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            {t('product.tabs.overview')}
          </TabsTrigger>
          <TabsTrigger value="metrics" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            {t('product.tabs.metrics')}
          </TabsTrigger>
          <TabsTrigger value="reviews" className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            {t('product.tabs.reviews')}
            {reviewStats && (
              <Badge variant="secondary" className="ml-1">
                {reviewStats.total_reviews}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="bestsellers" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            {t('product.tabs.bestsellers')}
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <div className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>{t('product.pricing.title')}</CardTitle>
                </CardHeader>
                <CardContent>
                  {product.latest_snapshot ? (
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">
                          {t('product.pricing.price')}:
                        </span>
                        <span className="text-2xl font-bold">
                          ${product.latest_snapshot.price}
                        </span>
                      </div>
                      {product.latest_snapshot.original_price && (
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">
                            {t('product.pricing.original')}:
                          </span>
                          <span className="line-through text-gray-500">
                            ${product.latest_snapshot.original_price}
                          </span>
                        </div>
                      )}
                      {product.latest_snapshot.discount_percentage && (
                        <Badge className="bg-green-600">
                          {product.latest_snapshot.discount_percentage.toFixed(
                            0
                          )}
                          % {t('product.pricing.off')}
                        </Badge>
                      )}
                    </div>
                  ) : (
                    <p className="text-gray-500">
                      {t('product.pricing.noPricing')}
                    </p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>{t('product.bsr.title')}</CardTitle>
                </CardHeader>
                <CardContent>
                  {product.latest_snapshot?.bsr_small_category ? (
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600">
                          {t('product.bsr.rank')}:
                        </span>
                        <span className="text-2xl font-bold">
                          #
                          {product.latest_snapshot.bsr_small_category.toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">
                        {t('product.bsr.in')}{' '}
                        {product.latest_snapshot.small_category_name}
                      </p>
                    </div>
                  ) : (
                    <p className="text-gray-500">{t('product.bsr.noBsr')}</p>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Product Metrics Trend - Multiple metrics for single product */}
            <ProductMetricsTrendChart productId={productId} />
          </div>
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics">
          <div className="space-y-6">
            {/* Summary Cards */}
            <MetricsSummaryCards productId={productId} />

            {/* Reviews & Rating Trend */}
            <ReviewTrendChart productId={productId} />

            {/* Price and BSR Charts Side by Side */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <PriceTrendChart productId={productId} />
              <BSRTrendChart productId={productId} />
            </div>

            {/* Dynamic Trend Analysis Chart */}
            <DynamicTrendChart
              availableProducts={userProducts
                .filter(p => p.title && p.asin)
                .map(p => ({ id: p.id, title: p.title!, asin: p.asin }))}
              defaultProductId={productId}
            />

            {/* Product Comparison Chart - Now fetches all products from backend */}
            <ProductComparisonChart />
          </div>
        </TabsContent>

        {/* Reviews Tab */}
        <TabsContent value="reviews">
          {reviewStats && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Review Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <div className="flex items-center gap-4 mb-4">
                      <div className="text-4xl font-bold">
                        {reviewStats.average_rating.toFixed(1)}
                      </div>
                      <div>
                        {renderStars(reviewStats.average_rating)}
                        <p className="text-sm text-gray-600 mt-1">
                          {reviewStats.total_reviews}{' '}
                          {t('product.reviews.reviews')}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      <span>
                        {reviewStats.verified_purchases}{' '}
                        {t('product.reviews.verifiedPurchases')}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm w-12">5 star</span>
                      {renderRatingBar(
                        reviewStats.rating_distribution['5_star'],
                        reviewStats.total_reviews
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm w-12">4 star</span>
                      {renderRatingBar(
                        reviewStats.rating_distribution['4_star'],
                        reviewStats.total_reviews
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm w-12">3 star</span>
                      {renderRatingBar(
                        reviewStats.rating_distribution['3_star'],
                        reviewStats.total_reviews
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm w-12">2 star</span>
                      {renderRatingBar(
                        reviewStats.rating_distribution['2_star'],
                        reviewStats.total_reviews
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm w-12">1 star</span>
                      {renderRatingBar(
                        reviewStats.rating_distribution['1_star'],
                        reviewStats.total_reviews
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="space-y-4">
            {reviews.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-gray-500">
                  {t('product.reviews.noReviews')}
                </CardContent>
              </Card>
            ) : (
              reviews.map(review => (
                <Card key={review.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          {renderStars(review.rating)}
                          <span className="text-sm font-semibold">
                            {review.title}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <span>{review.reviewer_name || 'Anonymous'}</span>
                          {review.verified_purchase && (
                            <Badge variant="secondary" className="text-xs">
                              {t('product.reviews.verifiedPurchase')}
                            </Badge>
                          )}
                          {review.is_vine_voice && (
                            <Badge className="text-xs bg-green-600">
                              {t('product.reviews.vineVoice')}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <span className="text-sm text-gray-500">
                        {new Date(review.review_date).toLocaleDateString()}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {review.text}
                    </p>
                    {review.helpful_count > 0 && (
                      <p className="text-sm text-gray-500 mt-2">
                        {review.helpful_count}{' '}
                        {t('product.reviews.peopleFoundHelpful')}
                      </p>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        {/* Bestsellers Tab */}
        <TabsContent value="bestsellers">
          {bestsellers ? (
            <>
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>{bestsellers.category_name}</CardTitle>
                  <CardDescription>
                    Snapshot from{' '}
                    {new Date(bestsellers.snapshot_date).toLocaleString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {bestsellers.product_rank ? (
                    <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                      <div className="flex items-center gap-3">
                        <TrendingUp className="w-6 h-6 text-blue-600" />
                        <div>
                          <p className="font-semibold">
                            {t('product.bestsellers.yourProductRanks')} #
                            {bestsellers.product_rank}
                          </p>
                          <p className="text-sm text-gray-600">
                            {t('product.bestsellers.inThisCategory')}
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-500">
                      {t('product.bestsellers.notInTop100')}
                    </p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>{t('product.bestsellers.top10Title')}</CardTitle>
                  <CardDescription>
                    {t('product.bestsellers.competitiveAnalysis')}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {bestsellers.top_10?.map((item, index) => (
                      <div
                        key={index}
                        className={`p-3 border rounded-md ${
                          item.asin === product.asin
                            ? 'bg-blue-50 border-blue-300'
                            : ''
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="text-2xl font-bold text-gray-400 w-8">
                            #{item.rank}
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-sm mb-1">
                              {item.title}
                            </p>
                            <div className="flex items-center gap-3 text-sm text-gray-600">
                              <span className="font-mono">{item.asin}</span>
                              <span className="font-semibold">
                                ${item.price}
                              </span>
                              <div className="flex items-center gap-1">
                                <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                                <span>{item.rating}</span>
                                <span className="text-gray-400">
                                  ({item.review_count.toLocaleString()})
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-gray-500">
                {t('product.bestsellers.noBestsellers')}
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
