import { AlertCircle, Link as LinkIcon, RefreshCw, Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/components/ui/use-toast';
import { useTranslation } from '@/hooks/useTranslation';
import { productService, type Product } from '@/services/productService';

export default function ProductsPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { t } = useTranslation();

  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const data = await productService.getProducts();
      setProducts(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch products');
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = products.filter(
    product =>
      product.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.asin.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.brand?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatPrice = (price: string | undefined) => {
    if (!price) return 'N/A';
    return `$${parseFloat(price).toFixed(2)}`;
  };

  const formatNumber = (num: number | null | undefined) => {
    if (num === undefined || num === null) return 'N/A';
    return num.toLocaleString();
  };

  const handleBatchRefresh = async () => {
    const productsToRefresh =
      selectedProducts.length > 0
        ? selectedProducts
        : products.filter(p => p.is_active).map(p => p.id);

    if (productsToRefresh.length === 0) {
      toast({
        title: t('products.noProductsSelected') || 'No Products Selected',
        description:
          t('products.selectProductsToRefresh') ||
          'Please select products to refresh or activate some products.',
        variant: 'destructive',
      });
      return;
    }

    try {
      setRefreshing(true);

      toast({
        title: t('products.batchRefreshStarted') || 'Batch Refresh Started',
        description:
          t('products.refreshingCount', { count: productsToRefresh.length }) ||
          `Refreshing ${productsToRefresh.length} product(s)...`,
      });

      const result = await productService.batchRefreshProducts(
        productsToRefresh,
        true // update metadata
      );

      // Refresh the product list
      await fetchProducts();

      // Clear selection
      setSelectedProducts([]);

      toast({
        title: t('products.batchRefreshComplete') || 'Batch Refresh Complete',
        description:
          t('products.refreshSuccess', {
            success: result.success,
            total: productsToRefresh.length,
            failed: result.failed,
          }) ||
          `Successfully refreshed ${result.success} out of ${productsToRefresh.length} products. ${result.failed > 0 ? `${result.failed} failed.` : ''}`,
        variant: result.failed > 0 ? 'destructive' : 'default',
      });
    } catch (error: any) {
      console.error('Failed to batch refresh:', error);
      toast({
        title: t('products.batchRefreshFailed') || 'Batch Refresh Failed',
        description:
          error.response?.data?.detail ||
          error.message ||
          t('products.refreshError') ||
          'Failed to refresh products',
        variant: 'destructive',
      });
    } finally {
      setRefreshing(false);
    }
  };

  const toggleProductSelection = (productId: string) => {
    setSelectedProducts(prev =>
      prev.includes(productId)
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    );
  };

  const toggleAllProducts = () => {
    if (selectedProducts.length === filteredProducts.length) {
      setSelectedProducts([]);
    } else {
      setSelectedProducts(filteredProducts.map(p => p.id));
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">{t('products.title')}</h1>
          <p className="text-gray-600 mt-1">
            {t('products.subtitle') ||
              'Monitor Amazon products for price and BSR changes'}
          </p>
        </div>
        <div className="flex gap-2">
          {selectedProducts.length > 0 && (
            <Button
              onClick={handleBatchRefresh}
              disabled={refreshing}
              className="flex items-center gap-2"
              variant="secondary"
            >
              <RefreshCw
                className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`}
              />
              {refreshing
                ? t('products.refreshing') || 'Refreshing...'
                : t('products.refreshSelected', {
                    count: selectedProducts.length,
                  }) || `Refresh ${selectedProducts.length} Selected`}
            </Button>
          )}
          <Button
            onClick={handleBatchRefresh}
            disabled={
              refreshing || products.filter(p => p.is_active).length === 0
            }
            className="flex items-center gap-2"
            variant="outline"
          >
            <RefreshCw
              className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`}
            />
            {refreshing
              ? t('products.refreshing') || 'Refreshing...'
              : t('products.refreshAllActive') || 'Refresh All Active'}
          </Button>
          <Button
            onClick={() => navigate('/products/import')}
            className="flex items-center gap-2"
            variant="default"
          >
            <LinkIcon className="w-4 h-4" />
            {t('products.importFromUrl') || 'Import from URL'}
          </Button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <Input
            type="text"
            placeholder={t('products.searchPlaceholder')}
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>
              {t('products.totalProducts') || 'Total Products'}
            </CardDescription>
            <CardTitle className="text-2xl">{products.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>
              {t('products.active') || 'Active'}
            </CardDescription>
            <CardTitle className="text-2xl">
              {products.filter(p => p.is_active).length}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>
              {t('products.totalAlerts') || 'Total Alerts'}
            </CardDescription>
            <CardTitle className="text-2xl">
              {products.reduce(
                (sum, p) => sum + (p.unread_alerts_count || 0),
                0
              )}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>
              {t('products.inStock') || 'In Stock'}
            </CardDescription>
            <CardTitle className="text-2xl">
              {products.filter(p => p.in_stock).length}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Products Table */}
      <Card>
        <CardHeader>
          <CardTitle>{t('products.products') || 'Products'}</CardTitle>
          <CardDescription>
            {t('products.clickToView') ||
              'Click on a product to view detailed tracking information'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">
              {t('products.loading') || 'Loading products...'}
            </div>
          ) : error ? (
            <div className="text-center py-8 text-red-600">{error}</div>
          ) : filteredProducts.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {searchTerm
                ? t('products.noProductsFound') ||
                  'No products found matching your search'
                : t('products.noProducts') ||
                  'No products yet. Add your first product to start tracking!'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <input
                        type="checkbox"
                        checked={
                          selectedProducts.length === filteredProducts.length &&
                          filteredProducts.length > 0
                        }
                        onChange={toggleAllProducts}
                        className="rounded border-gray-300 cursor-pointer"
                      />
                    </TableHead>
                    <TableHead>
                      {t('products.table.product') || 'Product'}
                    </TableHead>
                    <TableHead>{t('products.table.asin') || 'ASIN'}</TableHead>
                    <TableHead>
                      {t('products.table.price') || 'Price'}
                    </TableHead>
                    <TableHead>{t('products.table.bsr') || 'BSR'}</TableHead>
                    <TableHead>
                      {t('products.table.rating') || 'Rating'}
                    </TableHead>
                    <TableHead>
                      {t('products.table.stock') || 'Stock'}
                    </TableHead>
                    <TableHead>
                      {t('products.table.alerts') || 'Alerts'}
                    </TableHead>
                    <TableHead>
                      {t('products.table.status') || 'Status'}
                    </TableHead>
                    <TableHead>
                      {t('products.table.actions') || 'Actions'}
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredProducts.map(product => (
                    <TableRow
                      key={product.id}
                      className="cursor-pointer hover:bg-gray-50"
                    >
                      <TableCell onClick={e => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={selectedProducts.includes(product.id)}
                          onChange={() => toggleProductSelection(product.id)}
                          className="rounded border-gray-300 cursor-pointer"
                        />
                      </TableCell>
                      <TableCell
                        onClick={() => navigate(`/products/${product.id}`)}
                      >
                        <div className="flex items-center gap-3">
                          {product.image_url && (
                            <img
                              src={product.image_url}
                              alt={product.title || product.asin}
                              className="w-12 h-12 object-cover rounded-md"
                            />
                          )}
                          <div>
                            <div className="font-medium line-clamp-1">
                              {product.title}
                            </div>
                            {product.brand && (
                              <div className="text-sm text-gray-500">
                                {product.brand}
                              </div>
                            )}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell
                        className="font-mono text-sm"
                        onClick={() => navigate(`/products/${product.id}`)}
                      >
                        {product.asin}
                      </TableCell>
                      <TableCell
                        onClick={() => navigate(`/products/${product.id}`)}
                      >
                        {formatPrice(product.price)}
                      </TableCell>
                      <TableCell
                        onClick={() => navigate(`/products/${product.id}`)}
                      >
                        {formatNumber(product.current_bsr)}
                      </TableCell>
                      <TableCell
                        onClick={() => navigate(`/products/${product.id}`)}
                      >
                        <div className="flex items-center gap-1">
                          <span>{product.rating?.toFixed(1) || 'N/A'}</span>
                          <span className="text-xs text-gray-500">
                            ({formatNumber(product.review_count)})
                          </span>
                        </div>
                      </TableCell>
                      <TableCell
                        onClick={() => navigate(`/products/${product.id}`)}
                      >
                        {product.in_stock ? (
                          <Badge variant="default" className="bg-green-500">
                            In Stock
                          </Badge>
                        ) : (
                          <Badge variant="destructive">Out of Stock</Badge>
                        )}
                      </TableCell>
                      <TableCell
                        onClick={() => navigate(`/products/${product.id}`)}
                      >
                        {product.unread_alerts_count ? (
                          <Badge
                            variant="destructive"
                            className="flex items-center gap-1 w-fit"
                          >
                            <AlertCircle className="w-3 h-3" />
                            {product.unread_alerts_count}
                          </Badge>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </TableCell>
                      <TableCell
                        onClick={() => navigate(`/products/${product.id}`)}
                      >
                        {product.is_active ? (
                          <Badge variant="default">Active</Badge>
                        ) : (
                          <Badge variant="secondary">Inactive</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={e => {
                            e.stopPropagation();
                            navigate(`/products/${product.id}`);
                          }}
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
