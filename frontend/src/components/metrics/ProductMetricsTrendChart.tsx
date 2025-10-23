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

interface ProductMetricsTrendChartProps {
  productId: string;
}

const METRIC_OPTIONS = [
  { value: 'price', label: 'Price', color: '#3b82f6' },
  { value: 'bsr', label: 'Best Seller Rank', color: '#10b981' },
  { value: 'rating', label: 'Rating', color: '#f59e0b' },
  { value: 'reviews', label: 'Review Count', color: '#ef4444' },
] as const;

const TIME_OPTIONS = [
  { value: 7, label: '7 Days' },
  { value: 14, label: '14 Days' },
  { value: 30, label: '30 Days' },
  { value: 60, label: '60 Days' },
  { value: 90, label: '90 Days' },
] as const;

export default function ProductMetricsTrendChart({
  productId,
}: ProductMetricsTrendChartProps) {
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([
    'price',
    'bsr',
  ]);
  const [days, setDays] = useState(30);
  const [showCategoryBaseline, setShowCategoryBaseline] = useState(true);
  const [metricsData, setMetricsData] = useState<
    Record<string, MetricComparisonResponse>
  >({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    if (selectedMetrics.length === 0) {
      setMetricsData({});
      return;
    }

    try {
      setLoading(true);
      setError('');

      // Fetch data for each selected metric
      const dataPromises = selectedMetrics.map(async metric => {
        const data = await metricsService.compareProducts({
          product_ids: [productId],
          metric_type: metric as 'price' | 'bsr' | 'rating' | 'reviews',
          days,
        });
        return { metric, data };
      });

      const results = await Promise.all(dataPromises);
      const newMetricsData: Record<string, MetricComparisonResponse> = {};
      results.forEach(({ metric, data }) => {
        newMetricsData[metric] = data;
      });

      setMetricsData(newMetricsData);
    } catch (err: any) {
      console.error('Failed to load metrics data:', err);
      setError(err.message || 'Failed to load metrics data');
    } finally {
      setLoading(false);
    }
  }, [productId, selectedMetrics, days]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Transform data for the chart - combine all metrics
  const chartData = (() => {
    if (Object.keys(metricsData).length === 0) return [];

    // Get all dates from the first metric
    const firstMetric = Object.values(metricsData)[0];
    if (!firstMetric?.products[0]?.data_points) return [];

    return firstMetric.products[0].data_points.map(
      (point: any, index: number) => {
        const dataPoint: any = {
          date: point.date,
        };

        // Add each metric's value
        Object.entries(metricsData).forEach(([metric, data]) => {
          const productPoint: any = data.products[0]?.data_points[index];
          if (!productPoint) return;

          let value: number | null = null;
          switch (metric) {
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
          dataPoint[metric] = value;

          // Add category baseline if available
          if (showCategoryBaseline && data.category_average?.[index]) {
            dataPoint[`${metric}_baseline`] =
              data.category_average[index].value;
          }
        });

        return dataPoint;
      }
    );
  })();

  const getMetricConfig = (metric: string) => {
    return METRIC_OPTIONS.find(opt => opt.value === metric);
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold mb-2">{formatDate(label)}</p>
          {payload.map((entry: any, index: number) => {
            const config = getMetricConfig(entry.dataKey);
            if (!config) return null;

            let formattedValue = 'N/A';
            if (entry.value !== null) {
              switch (entry.dataKey) {
                case 'price':
                  formattedValue = `$${entry.value.toFixed(2)}`;
                  break;
                case 'rating':
                  formattedValue = entry.value.toFixed(1);
                  break;
                default:
                  formattedValue = entry.value.toLocaleString();
              }
            }

            return (
              <p key={index} style={{ color: entry.color }} className="text-sm">
                {config.label}: {formattedValue}
              </p>
            );
          })}
        </div>
      );
    }
    return null;
  };

  return (
    <Card>
      <CardHeader>
        <div className="space-y-4">
          <CardTitle>Product Metrics Trend</CardTitle>

          {/* Controls */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Metrics Selection */}
            <div className="space-y-2">
              <Label>Select Metrics (Max 4)</Label>
              <ThemedSelect
                isMulti
                options={METRIC_OPTIONS.map(opt => ({
                  label: opt.label,
                  value: opt.value,
                }))}
                value={METRIC_OPTIONS.filter(opt =>
                  selectedMetrics.includes(opt.value)
                ).map(opt => ({ label: opt.label, value: opt.value }))}
                onChange={selected => {
                  const metrics = (
                    (selected as Array<{ label: string; value: string }>) || []
                  ).map(s => s.value);
                  setSelectedMetrics(metrics.slice(0, 4)); // Enforce max 4
                }}
                placeholder="Select metrics to display..."
                isOptionDisabled={() => selectedMetrics.length >= 4}
              />
              {selectedMetrics.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  {selectedMetrics.length} metric
                  {selectedMetrics.length !== 1 ? 's' : ''} selected
                  {selectedMetrics.length >= 4 && ' (maximum reached)'}
                </p>
              )}
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
          </div>

          {/* Category Baseline Toggle */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="show-category-baseline"
              checked={showCategoryBaseline}
              onCheckedChange={setShowCategoryBaseline}
            />
            <label
              htmlFor="show-category-baseline"
              className="text-sm font-medium leading-none cursor-pointer select-none"
            >
              Show Category Baseline
            </label>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {loading ? (
          <div className="h-96 flex items-center justify-center">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Loading metrics data...</span>
            </div>
          </div>
        ) : error ? (
          <div className="h-96 flex items-center justify-center">
            <p className="text-red-500">{error}</p>
          </div>
        ) : selectedMetrics.length === 0 ? (
          <div className="h-96 flex items-center justify-center">
            <p className="text-muted-foreground">
              Select at least one metric to view trend data
            </p>
          </div>
        ) : chartData.length === 0 ? (
          <div className="h-96 flex items-center justify-center">
            <p className="text-muted-foreground">
              No data available for selected metrics
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart
              data={chartData}
              margin={{ top: 5, right: 60, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                stroke="#888888"
                fontSize={12}
              />

              {/* Price axis - Left (Blue) */}
              {selectedMetrics.includes('price') && (
                <YAxis
                  yAxisId="price"
                  stroke="#3b82f6"
                  fontSize={12}
                  tickFormatter={value => `$${value}`}
                  label={{
                    value: 'Price',
                    angle: -90,
                    position: 'insideLeft',
                    style: { fill: '#3b82f6' },
                  }}
                />
              )}

              {/* BSR axis - Right (Green) */}
              {selectedMetrics.includes('bsr') && (
                <YAxis
                  yAxisId="bsr"
                  orientation="right"
                  stroke="#10b981"
                  fontSize={12}
                  reversed
                  label={{
                    value: 'Best Seller Rank',
                    angle: 90,
                    position: 'insideRight',
                    style: { fill: '#10b981' },
                  }}
                />
              )}

              {/* Rating axis - Left (Orange) */}
              {selectedMetrics.includes('rating') && (
                <YAxis
                  yAxisId="rating"
                  stroke="#f59e0b"
                  fontSize={12}
                  domain={[0, 5]}
                  ticks={[0, 1, 2, 3, 4, 5]}
                  label={{
                    value: 'Rating',
                    angle: -90,
                    position: 'insideLeft',
                    style: { fill: '#f59e0b' },
                  }}
                />
              )}

              {/* Review Count axis - Right (Red) */}
              {selectedMetrics.includes('reviews') && (
                <YAxis
                  yAxisId="reviews"
                  orientation="right"
                  stroke="#ef4444"
                  fontSize={12}
                  label={{
                    value: 'Review Count',
                    angle: 90,
                    position: 'insideRight',
                    style: { fill: '#ef4444' },
                  }}
                />
              )}

              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ paddingTop: '20px' }}
                iconType="line"
                formatter={(value: string) => {
                  const config = getMetricConfig(value);
                  return config?.label || value;
                }}
              />

              {/* Metric Lines - each with its own axis */}
              {selectedMetrics.map(metric => {
                const config = getMetricConfig(metric);
                if (!config) return null;

                return (
                  <Line
                    key={metric}
                    type="monotone"
                    dataKey={metric}
                    name={metric}
                    stroke={config.color}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 6 }}
                    connectNulls
                    yAxisId={metric}
                  />
                );
              })}

              {/* Category Baseline Lines */}
              {showCategoryBaseline &&
                selectedMetrics.map(metric => {
                  const config = getMetricConfig(metric);
                  if (!config) return null;

                  const hasBaseline = metricsData[metric]?.category_average;
                  if (!hasBaseline) return null;

                  return (
                    <Line
                      key={`${metric}_baseline`}
                      type="monotone"
                      dataKey={`${metric}_baseline`}
                      name={`${config.label} (Category Avg)`}
                      stroke={config.color}
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={{ r: 2 }}
                      activeDot={{ r: 5 }}
                      connectNulls
                      yAxisId={metric}
                    />
                  );
                })}
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
