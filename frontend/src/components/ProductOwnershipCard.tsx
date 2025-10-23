/**
 * ProductOwnershipCard - Display product with ownership information
 */

import {
  AlertCircle,
  CheckCircle2,
  Tag,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { useState } from 'react';

import { ClaimProductDialog } from './ClaimProductDialog';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useToast } from '@/components/ui/use-toast';
import { userProductService } from '@/services/userProductService';
import type { ProductWithOwnership } from '@/types/userProduct';

interface ProductOwnershipCardProps {
  product: ProductWithOwnership;
  onUpdate?: () => void;
}

export function ProductOwnershipCard({
  product,
  onUpdate,
}: ProductOwnershipCardProps) {
  const { toast } = useToast();
  const [claimDialogOpen, setClaimDialogOpen] = useState(false);
  const [unclaiming, setUnclaiming] = useState(false);

  const handleUnclaim = async () => {
    if (!confirm('Are you sure you want to unclaim this product?')) {
      return;
    }

    try {
      setUnclaiming(true);
      await userProductService.unclaimProduct(product.id);

      toast({
        title: 'Product Unclaimed',
        description: `${product.title} has been removed from your owned products.`,
      });

      onUpdate?.();
    } catch (error: any) {
      toast({
        title: 'Failed to Unclaim Product',
        description: error.response?.data?.detail || 'An error occurred',
        variant: 'destructive',
      });
    } finally {
      setUnclaiming(false);
    }
  };

  return (
    <>
      <Card className={product.is_owned ? 'border-blue-200 bg-blue-50/50' : ''}>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                {product.is_owned ? (
                  <Badge variant="default" className="bg-blue-600">
                    <CheckCircle2 className="w-3 h-3 mr-1" />
                    Your Product
                  </Badge>
                ) : (
                  <Badge variant="outline">Competitor</Badge>
                )}
                {!product.is_active && (
                  <Badge variant="secondary">Inactive</Badge>
                )}
              </div>
              <CardTitle className="text-lg line-clamp-2">
                {product.title}
              </CardTitle>
              <CardDescription className="mt-1">
                ASIN: {product.asin} • {product.category || 'No category'}
              </CardDescription>
            </div>
            {product.image_url && (
              <img
                src={product.image_url}
                alt={product.title}
                className="w-20 h-20 object-contain rounded ml-4 flex-shrink-0"
              />
            )}
          </div>
        </CardHeader>

        <CardContent>
          {/* Product Metrics */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <p className="text-xs text-muted-foreground">Price</p>
              <p className="text-lg font-bold">
                {product.latest_price
                  ? `$${product.latest_price.toFixed(2)}`
                  : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">BSR</p>
              <p className="text-lg font-bold">
                {product.latest_bsr ? `#${product.latest_bsr}` : 'N/A'}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Rating</p>
              <p className="text-lg font-bold">
                {product.latest_rating
                  ? `${product.latest_rating.toFixed(1)}⭐`
                  : 'N/A'}
              </p>
            </div>
          </div>

          {/* Ownership Details */}
          {product.is_owned && product.ownership && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm font-medium text-blue-900 mb-2">
                Your Settings
              </p>
              <div className="space-y-1 text-xs text-blue-700">
                <div className="flex items-center gap-2">
                  <TrendingDown className="w-3 h-3" />
                  <span>
                    Price Alert:{' '}
                    {product.ownership.price_change_threshold ?? 'Default'}%
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-3 h-3" />
                  <span>
                    BSR Alert:{' '}
                    {product.ownership.bsr_change_threshold ?? 'Default'}%
                  </span>
                </div>
                {product.ownership.is_primary && (
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-3 h-3" />
                    <span>Primary Product</span>
                  </div>
                )}
                {product.ownership.notes && (
                  <p className="mt-2 text-xs italic">
                    {product.ownership.notes}
                  </p>
                )}
                {product.ownership.tags &&
                  product.ownership.tags.length > 0 && (
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {product.ownership.tags.map(tag => (
                        <Badge
                          key={tag}
                          variant="outline"
                          className="text-xs bg-white"
                        >
                          <Tag className="w-3 h-3 mr-1" />
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="mt-4 flex gap-2">
            <a
              href={product.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1"
            >
              <Button variant="outline" size="sm" className="w-full">
                View on Amazon
              </Button>
            </a>
            {product.is_owned ? (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleUnclaim}
                disabled={unclaiming}
              >
                {unclaiming ? 'Unclaiming...' : 'Unclaim'}
              </Button>
            ) : (
              <Button
                variant="default"
                size="sm"
                onClick={() => setClaimDialogOpen(true)}
              >
                Claim Product
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Claim Dialog */}
      <ClaimProductDialog
        product={product}
        open={claimDialogOpen}
        onOpenChange={setClaimDialogOpen}
        onSuccess={onUpdate}
      />
    </>
  );
}
