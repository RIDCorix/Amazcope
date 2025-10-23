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

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { ThemedSelect } from '@/components/ui/themed-select';
import {
  getChartColor,
  getMetricTypeName,
  metricsService,
  type MetricComparisonResponse,
} from '@/services/metricsService';
import { productService } from '@/services/productService';

interface ProductComparisonChartProps {
  // Optional: can still pass available products for better initial UX
  availableProducts?: Array<{ id: string; title: string; asin: string }>;
}

export default function ProductComparisonChart({
  availableProducts: initialProducts,
}: ProductComparisonChartProps) {
  const [availableProducts, setAvailableProducts] = useState<
    Array<{ id: string; title: string; asin: string }>
  >(initialProducts || []);
  const [loadingProducts, setLoadingProducts] = useState(!initialProducts);
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>([]);
  const [metricType, setMetricType] = useState<
    'price' | 'bsr' | 'rating' | 'reviews'
  >('price');
  const [days, setDays] = useState(30);
  const [showCategoryAverage, setShowCategoryAverage] = useState(true);
  const [comparisonData, setComparisonData] =
    useState<MetricComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Load all products if not provided
  useEffect(() => {
    if (!initialProducts) {
      const fetchProducts = async () => {
        try {
          setLoadingProducts(true);
          const products = await productService.getProducts();
          setAvailableProducts(
            products.map(p => ({
              id: p.id.toString(),
              title: p.title || p.asin,
              asin: p.asin,
            }))
          );
        } catch (err: any) {
          console.error('Failed to load products:', err);
          setError(err.message || 'Failed to load products');
        } finally {
          setLoadingProducts(false);
        }
      };
      fetchProducts();
    }
  }, [initialProducts]);

  const loadComparison = useCallback(async () => {
    try {
      setLoading(true);
      const data = await metricsService.compareProducts({
        product_ids: selectedProductIds,
        metric_type: metricType,
        days,
      });
      setComparisonData(data);
      setError('');
    } catch (err: any) {
      console.error('Failed to load comparison:', err);
      setError(err.message || 'Failed to load comparison');
    } finally {
      setLoading(false);
    }
  }, [selectedProductIds, metricType, days]);

  useEffect(() => {
    if (selectedProductIds.length > 0) {
      loadComparison();
    }
  }, [selectedProductIds.length, loadComparison]);

  // const _handleProductToggle = (id: string) => {
  //   if (!selectedProductIds.includes(id) && selectedProductIds.length < 10) {
  //     setSelectedProductIds([...selectedProductIds, id]);
  //   } else {
  //     setSelectedProductIds(selectedProductIds.filter(pid => pid !== id));
  //   }
  // };

  // const _handleRemoveProduct = (productId: string) => {
  //   setSelectedProductIds(selectedProductIds.filter(id => id !== productId));
  // };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const formatValue = (value: number, type: string) => {
    switch (type) {
      case 'price':
        return `$${value.toFixed(2)}`;
      case 'bsr':
        return `#${value.toLocaleString()}`;
      case 'rating':
        return value.toFixed(1);
      case 'reviews':
        return value.toLocaleString();
      default:
        return value.toString();
    }
  };

  // Transform data for Recharts
  const chartData =
    comparisonData?.products[0]?.data_points.map((_, index) => {
      const dataPoint: any = {
        date: comparisonData.products[0].data_points[index].date,
      };

      // Add data for each product
      comparisonData.products.forEach(product => {
        const point = product.data_points[index] as any;

        // Safety check: ensure point exists
        if (!point) {
          dataPoint[`product_${product.product_id}`] = null;
          return;
        }

        let value = null;

        if (metricType === 'price') {
          value = point.price;
        } else if (metricType === 'bsr') {
          value = point.bsr_main;
        } else if (metricType === 'rating') {
          value = point.rating;
        } else if (metricType === 'reviews') {
          value = point.review_count;
        }

        dataPoint[`product_${product.product_id}`] = value;
      });

      // Add category average if available
      if (showCategoryAverage && comparisonData.category_average) {
        const categoryPoint = comparisonData.category_average[index];
        dataPoint.category_average = categoryPoint?.value;
      }

      return dataPoint;
    }) || [];

  // const _selectedProducts = availableProducts.filter(p =>
  //   selectedProductIds.includes(p.id)
  // );

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg max-w-xs">
          <p className="font-semibold mb-2">{formatDate(label)}</p>
          {payload.map((entry: any, index: number) => (
            <p
              key={index}
              style={{ color: entry.color }}
              className="text-sm truncate"
            >
              {entry.name}: {formatValue(entry.value, metricType)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle>Multi-Product Comparison</CardTitle>

        {/* Product Selector */}
        <div className="space-y-4 mt-4">
          <div>
            <Label className="text-sm font-medium mb-2 block">
              Select Products (Max 10)
            </Label>
            <ThemedSelect
              isMulti
              options={availableProducts.map(product => ({
                label: `${product.title} (${product.asin})`,
                value: product.id,
              }))}
              value={availableProducts
                .filter(p => selectedProductIds.includes(p.id))
                .map(p => ({ label: `${p.title} (${p.asin})`, value: p.id }))}
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
              <p className="text-xs text-muted-foreground mt-2">
                {selectedProductIds.length} product
                {selectedProductIds.length !== 1 ? 's' : ''} selected
                {selectedProductIds.length >= 10 && ' (maximum reached)'}
              </p>
            )}
          </div>

          {/* Controls */}
          <div className="flex flex-wrap gap-4">
            {/* Metric Type Selector */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Metric Type
              </label>
              <div className="flex gap-2">
                <Button
                  variant={metricType === 'price' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setMetricType('price')}
                >
                  Price
                </Button>
                <Button
                  variant={metricType === 'bsr' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setMetricType('bsr')}
                >
                  BSR
                </Button>
                <Button
                  variant={metricType === 'rating' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setMetricType('rating')}
                >
                  Rating
                </Button>
                <Button
                  variant={metricType === 'reviews' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setMetricType('reviews')}
                >
                  Reviews
                </Button>
              </div>
            </div>

            {/* Date Range Selector */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Date Range
              </label>
              <div className="flex gap-2">
                <Button
                  variant={days === 7 ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setDays(7)}
                >
                  7D
                </Button>
                <Button
                  variant={days === 30 ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setDays(30)}
                >
                  30D
                </Button>
                <Button
                  variant={days === 90 ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setDays(90)}
                >
                  90D
                </Button>
              </div>
            </div>

            {/* Category Average Toggle */}
            {comparisonData?.category_average && (
              <div>
                <Label className="text-sm font-medium mb-2 block">
                  Display Options
                </Label>
                <div className="flex items-center space-x-2 h-10">
                  <Checkbox
                    id="show-category-avg"
                    checked={showCategoryAverage}
                    onCheckedChange={setShowCategoryAverage}
                  />
                  <label
                    htmlFor="show-category-avg"
                    className="text-sm font-medium leading-none cursor-pointer select-none"
                  >
                    Show Category Average
                  </label>
                </div>
              </div>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {loadingProducts ? (
          <div className="h-96 flex items-center justify-center">
            <div className="animate-pulse text-muted-foreground">
              Loading products...
            </div>
          </div>
        ) : selectedProductIds.length === 0 ? (
          <div className="h-96 flex items-center justify-center">
            <p className="text-muted-foreground">
              Select products to compare their{' '}
              {getMetricTypeName(metricType).toLowerCase()} trends
            </p>
          </div>
        ) : loading ? (
          <div className="h-96 flex items-center justify-center">
            <div className="animate-pulse text-muted-foreground">
              Loading comparison...
            </div>
          </div>
        ) : error ? (
          <div className="h-96 flex items-center justify-center">
            <p className="text-muted-foreground">{error}</p>
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
                tickFormatter={value => formatValue(value, metricType)}
                stroke="#888888"
                fontSize={12}
                reversed={metricType === 'bsr'}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ paddingTop: '20px' }} iconType="line" />

              {/* Product Lines */}
              {comparisonData?.products.map((product, index) => (
                <Line
                  key={product.product_id}
                  type="monotone"
                  dataKey={`product_${product.product_id}`}
                  stroke={getChartColor(index)}
                  strokeWidth={2}
                  name={product.product_title}
                  dot={{ r: 2 }}
                  activeDot={{ r: 5 }}
                />
              ))}

              {/* Category Average Line */}
              {showCategoryAverage && comparisonData?.category_average && (
                <Line
                  type="monotone"
                  dataKey="category_average"
                  stroke="#000000"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="Category Average"
                  dot={{ r: 2 }}
                  activeDot={{ r: 5 }}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
