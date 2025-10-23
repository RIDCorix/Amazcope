import { Loader2 } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { ThemedSelect } from '@/components/ui/themed-select';
import {
  metricsService,
  type MetricComparisonResponse,
} from '@/services/metricsService';

interface DynamicTrendChartProps {
  availableProducts: Array<{ id: string; title: string; asin: string }>;
  defaultProductId?: string;
}

const METRIC_OPTIONS = [
  { value: 'price', label: 'Price' },
  { value: 'bsr', label: 'Best Seller Rank' },
  { value: 'rating', label: 'Rating' },
  { value: 'reviews', label: 'Review Count' },
] as const;

const TIME_OPTIONS = [
  { value: 7, label: '7 Days' },
  { value: 14, label: '14 Days' },
  { value: 30, label: '30 Days' },
  { value: 60, label: '60 Days' },
  { value: 90, label: '90 Days' },
] as const;

const COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#f97316', // orange
];

export default function DynamicTrendChart({
  availableProducts,
  defaultProductId,
}: DynamicTrendChartProps) {
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>(
    defaultProductId ? [defaultProductId.toString()] : []
  );
  const [metricType, setMetricType] = useState<
    'price' | 'bsr' | 'rating' | 'reviews'
  >('price');
  const [days, setDays] = useState(30);
  const [showCategoryBaseline, setShowCategoryBaseline] = useState(true);
  const [data, setData] = useState<MetricComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    if (selectedProductIds.length === 0) {
      setData(null);
      return;
    }

    try {
      setLoading(true);
      setError('');
      const comparisonData = await metricsService.compareProducts({
        product_ids: selectedProductIds,
        metric_type: metricType,
        days,
      });
      setData(comparisonData);
    } catch (err: any) {
      console.error('Failed to load trend data:', err);
      setError(err.message || 'Failed to load trend data');
    } finally {
      setLoading(false);
    }
  }, [selectedProductIds, metricType, days]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // const _toggleProduct = (productId: string) => {
  //   setSelectedProductIds(prev =>
  //     prev.includes(productId)
  //       ? prev.filter(id => id !== productId)
  //       : [...prev, productId]
  //   );
  // };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getMetricLabel = () => {
    switch (metricType) {
      case 'price':
        return 'Price ($)';
      case 'bsr':
        return 'Best Seller Rank';
      case 'rating':
        return 'Rating (0-5)';
      case 'reviews':
        return 'Review Count';
    }
  };

  // Transform data for the chart
  const chartData =
    data?.products[0]?.data_points?.map((point: any, index: number) => {
      const dataPoint: any = {
        date: point.date,
      };

      // Add data for each selected product
      data.products.forEach(product => {
        const productPoint: any = product.data_points[index];
        let value: number | null = null;

        switch (metricType) {
          case 'price':
            value = productPoint.price;
            break;
          case 'bsr':
            value = productPoint.bsr_small || productPoint.bsr_main;
            break;
          case 'rating':
            value = productPoint.rating;
            break;
          case 'reviews':
            value = productPoint.review_count;
            break;
        }

        dataPoint[`product_${product.product_id}`] = value;
      });

      // Add category baseline
      if (
        showCategoryBaseline &&
        data.category_average &&
        data.category_average[index]
      ) {
        dataPoint.category_baseline = data.category_average[index].value;
      }

      return dataPoint;
    }) || [];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold mb-2">{formatDate(label)}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }} className="text-sm">
              {entry.name}:{' '}
              {entry.value !== null
                ? metricType === 'price'
                  ? `$${entry.value.toFixed(2)}`
                  : metricType === 'rating'
                    ? entry.value.toFixed(1)
                    : entry.value.toLocaleString()
                : 'N/A'}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <Card>
      <CardHeader>
        <div className="space-y-4">
          <CardTitle>Product Comparison</CardTitle>
          <p className="text-sm text-muted-foreground">
            Compare the same metric across multiple products
          </p>

          {/* Controls */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Metric Type Selection */}
            <div className="space-y-2">
              <Label htmlFor="metric-type">Metric Type</Label>
              <Select
                id="metric-type"
                value={metricType}
                onChange={e => setMetricType(e.target.value as any)}
              >
                {METRIC_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>

            {/* Time Range Selection */}
            <div className="space-y-2">
              <Label htmlFor="time-range">Time Range</Label>
              <Select
                id="time-range"
                value={days.toString()}
                onChange={e => setDays(Number(e.target.value))}
              >
                {TIME_OPTIONS.map(option => (
                  <option key={option.value} value={option.value.toString()}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>

            {/* Category Baseline Toggle */}
            <div className="space-y-2">
              <Label>Display Options</Label>
              <div className="flex items-center space-x-2 h-10">
                <Checkbox
                  id="category-baseline"
                  checked={showCategoryBaseline}
                  onCheckedChange={setShowCategoryBaseline}
                />
                <label
                  htmlFor="category-baseline"
                  className="text-sm font-medium leading-none cursor-pointer select-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Show Category Baseline
                </label>
              </div>
            </div>
          </div>

          {/* Product Selection */}
          <div className="space-y-2">
            <Label>Select Products (Max 10)</Label>
            <ThemedSelect
              isMulti
              options={availableProducts.map(product => ({
                label: product.title,
                value: product.id,
              }))}
              value={availableProducts
                .filter(p => selectedProductIds.includes(p.id))
                .map(p => ({ label: p.title, value: p.id }))}
              onChange={selected => {
                const ids = (
                  (selected as Array<{ label: string; value: string }>) || []
                ).map(s => s.value);
                setSelectedProductIds(ids.slice(0, 10)); // Enforce max 10
              }}
              placeholder="Add product to compare..."
              isOptionDisabled={() => selectedProductIds.length >= 10}
            />
            {selectedProductIds.length > 0 && (
              <p className="text-xs text-muted-foreground">
                {selectedProductIds.length} product
                {selectedProductIds.length !== 1 ? 's' : ''} selected
                {selectedProductIds.length >= 10 && ' (maximum reached)'}
              </p>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {loading ? (
          <div className="h-96 flex items-center justify-center">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Loading chart data...</span>
            </div>
          </div>
        ) : error ? (
          <div className="h-96 flex items-center justify-center">
            <p className="text-red-500">{error}</p>
          </div>
        ) : selectedProductIds.length === 0 ? (
          <div className="h-96 flex items-center justify-center">
            <p className="text-muted-foreground">
              Select at least one product to view trend data
            </p>
          </div>
        ) : chartData.length === 0 ? (
          <div className="h-96 flex items-center justify-center">
            <p className="text-muted-foreground">
              No data available for selected products
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={500}>
            <LineChart
              data={chartData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                stroke="#888888"
                fontSize={12}
              />
              <YAxis
                stroke="#888888"
                fontSize={12}
                label={{
                  value: getMetricLabel(),
                  angle: -90,
                  position: 'insideLeft',
                }}
                domain={metricType === 'rating' ? [0, 5] : undefined}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ paddingTop: '20px' }}
                iconType="line"
                formatter={(value: string) => {
                  if (value === 'category_baseline') {
                    return 'Category Average';
                  }
                  const productId = parseInt(value.replace('product_', ''));
                  const product = data?.products.find(
                    p => p.product_id === productId.toString()
                  );
                  return product?.product_title || value;
                }}
              />

              {/* Product Lines */}
              {data?.products.map((product, index) => (
                <Line
                  key={product.product_id}
                  type="monotone"
                  dataKey={`product_${product.product_id}`}
                  name={`product_${product.product_id}`}
                  stroke={COLORS[index % COLORS.length]}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 6 }}
                  connectNulls
                />
              ))}

              {/* Category Baseline */}
              {showCategoryBaseline && data?.category_average && (
                <Line
                  type="monotone"
                  dataKey="category_baseline"
                  name="category_baseline"
                  stroke="#94a3b8"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  connectNulls
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
