/**
 * Competitors Page - View and manage competitor products
 * Shows all products in the system with ownership status
 */

import { Filter, Package, Search, TrendingUp } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import { ProductOwnershipCard } from '@/components/ProductOwnershipCard';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectItem } from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { userProductService } from '@/services/userProductService';
import type { ProductWithOwnership } from '@/types/userProduct';

export default function CompetitorsPage() {
  const { toast } = useToast();
  const [products, setProducts] = useState<ProductWithOwnership[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<
    'all' | 'owned' | 'competitors'
  >('all');
  const [stats, setStats] = useState({
    total: 0,
    owned_count: 0,
    competitor_count: 0,
  });

  const fetchProducts = useCallback(async () => {
    try {
      setLoading(true);
      const response = await userProductService.getCompetitorProducts({
        category: category || undefined,
        limit: 100,
      });

      setProducts(response.products);
      setStats({
        total: response.total,
        owned_count: response.owned_count,
        competitor_count: response.competitor_count,
      });
    } catch (error: any) {
      toast({
        title: 'Failed to Load Products',
        description: error.response?.data?.detail || 'An error occurred',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [category, toast]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  // Filter products based on search and status
  const filteredProducts = products.filter(product => {
    // Search filter
    const matchesSearch =
      !searchQuery ||
      product.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      product.asin.toLowerCase().includes(searchQuery.toLowerCase()) ||
      product.brand?.toLowerCase().includes(searchQuery.toLowerCase());

    // Status filter
    const matchesStatus =
      filterStatus === 'all' ||
      (filterStatus === 'owned' && product.is_owned) ||
      (filterStatus === 'competitors' && !product.is_owned);

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Competitor Analysis</h1>
        <p className="text-muted-foreground">
          Track competitor products and claim ownership of your products
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Package className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.total}</p>
              <p className="text-sm text-muted-foreground">Total Products</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.owned_count}</p>
              <p className="text-sm text-muted-foreground">Your Products</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Filter className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.competitor_count}</p>
              <p className="text-sm text-muted-foreground">Competitors</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border shadow-sm mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="space-y-2">
            <Label htmlFor="search">Search Products</Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                id="search"
                placeholder="Search by title, ASIN, or brand..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Category Filter */}
          <div className="space-y-2">
            <Label htmlFor="category">Category</Label>
            <Input
              id="category"
              placeholder="Filter by category..."
              value={category}
              onChange={e => setCategory(e.target.value)}
            />
          </div>

          {/* Status Filter */}
          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <Select
              id="status"
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value as any)}
            >
              <SelectItem value="all">All Products</SelectItem>
              <SelectItem value="owned">Your Products Only</SelectItem>
              <SelectItem value="competitors">Competitors Only</SelectItem>
            </Select>
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <Button onClick={fetchProducts} variant="outline" size="sm">
            Refresh
          </Button>
        </div>
      </div>

      {/* Products Grid */}
      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : filteredProducts.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border">
          <Package className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Products Found</h3>
          <p className="text-muted-foreground mb-4">
            {searchQuery || category
              ? 'Try adjusting your filters'
              : 'Start by importing products or running bestseller scraping'}
          </p>
        </div>
      ) : (
        <>
          <div className="mb-4 text-sm text-muted-foreground">
            Showing {filteredProducts.length} of {products.length} products
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProducts.map(product => (
              <ProductOwnershipCard
                key={product.id}
                product={product}
                onUpdate={fetchProducts}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
