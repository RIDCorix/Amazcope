import {
  Award,
  DollarSign,
  MessageSquare,
  Star,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  formatBSR,
  formatCurrency,
  formatPercentageChange,
  formatRating,
  getChangeColor,
  metricsService,
  type MetricsSummary,
} from '@/services/metricsService';

interface MetricsSummaryCardsProps {
  productId: string;
}

export default function MetricsSummaryCards({
  productId,
}: MetricsSummaryCardsProps) {
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadSummary = useCallback(async () => {
    try {
      setLoading(true);
      const data = await metricsService.getMetricsSummary(productId);
      setSummary(data);
      setError('');
    } catch (err: any) {
      console.error('Failed to load metrics summary:', err);
      setError(err.message || 'Failed to load metrics');
    } finally {
      setLoading(false);
    }
  }, [productId]);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => (
          <Card key={i} className="animate-pulse">
            <CardHeader>
              <div className="h-4 bg-gray-200 rounded w-24"></div>
            </CardHeader>
            <CardContent>
              <div className="h-8 bg-gray-200 rounded w-32 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-20"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-yellow-800">
          {error ||
            'No metrics data available. Data will be collected during the next daily scraping.'}
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Price Card */}
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Current Price</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {formatCurrency(summary.current_price)}
          </div>
          <div className="mt-2 space-y-1">
            <div
              className={`text-xs flex items-center gap-1 ${getChangeColor(summary.price_change_7d)}`}
            >
              {summary.price_change_7d !== null && (
                <>
                  {summary.price_change_7d > 0 ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : (
                    <TrendingDown className="h-3 w-3" />
                  )}
                  <span>
                    7d: {formatPercentageChange(summary.price_change_7d)}
                  </span>
                </>
              )}
            </div>
            <div
              className={`text-xs flex items-center gap-1 ${getChangeColor(summary.price_change_30d)}`}
            >
              {summary.price_change_30d !== null && (
                <>
                  {summary.price_change_30d > 0 ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : (
                    <TrendingDown className="h-3 w-3" />
                  )}
                  <span>
                    30d: {formatPercentageChange(summary.price_change_30d)}
                  </span>
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* BSR Card */}
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            Best Seller Rank
          </CardTitle>
          <Award className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {formatBSR(summary.current_bsr)}
          </div>
          <div className="mt-2 space-y-1">
            <div
              className={`text-xs flex items-center gap-1 ${getChangeColor(summary.bsr_change_7d, true)}`}
            >
              {summary.bsr_change_7d !== null && (
                <>
                  {summary.bsr_change_7d < 0 ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : (
                    <TrendingDown className="h-3 w-3" />
                  )}
                  <span>
                    7d: {formatPercentageChange(summary.bsr_change_7d)}
                  </span>
                </>
              )}
            </div>
            <div
              className={`text-xs flex items-center gap-1 ${getChangeColor(summary.bsr_change_30d, true)}`}
            >
              {summary.bsr_change_30d !== null && (
                <>
                  {summary.bsr_change_30d < 0 ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : (
                    <TrendingDown className="h-3 w-3" />
                  )}
                  <span>
                    30d: {formatPercentageChange(summary.bsr_change_30d)}
                  </span>
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Rating Card */}
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Rating</CardTitle>
          <Star className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {formatRating(summary.current_rating)}
          </div>
          <div className="mt-2 space-y-1">
            <div
              className={`text-xs flex items-center gap-1 ${getChangeColor(summary.rating_change_7d)}`}
            >
              {summary.rating_change_7d !== null && (
                <>
                  {summary.rating_change_7d > 0 ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : (
                    <TrendingDown className="h-3 w-3" />
                  )}
                  <span>
                    7d: {formatPercentageChange(summary.rating_change_7d)}
                  </span>
                </>
              )}
            </div>
            <div
              className={`text-xs flex items-center gap-1 ${getChangeColor(summary.rating_change_30d)}`}
            >
              {summary.rating_change_30d !== null && (
                <>
                  {summary.rating_change_30d > 0 ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : (
                    <TrendingDown className="h-3 w-3" />
                  )}
                  <span>
                    30d: {formatPercentageChange(summary.rating_change_30d)}
                  </span>
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Reviews Card */}
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Reviews</CardTitle>
          <MessageSquare className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {summary.review_count.toLocaleString()}
          </div>
          <div className="mt-2 space-y-1">
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              {summary.review_growth_7d !== null && (
                <>
                  <TrendingUp className="h-3 w-3 text-green-600" />
                  <span className="text-green-600">
                    +{summary.review_growth_7d} last 7 days
                  </span>
                </>
              )}
            </div>
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              {summary.review_growth_30d !== null && (
                <>
                  <TrendingUp className="h-3 w-3 text-green-600" />
                  <span className="text-green-600">
                    +{summary.review_growth_30d} last 30 days
                  </span>
                </>
              )}
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Updated: {new Date(summary.last_updated).toLocaleDateString()}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
