/**
 * ClaimProductDialog - Dialog for claiming ownership of a product
 */

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import { userProductService } from '@/services/userProductService';
import type { ProductWithOwnership } from '@/types/userProduct';

interface ClaimProductDialogProps {
  product: ProductWithOwnership;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function ClaimProductDialog({
  product,
  open,
  onOpenChange,
  onSuccess,
}: ClaimProductDialogProps) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [isPrimary, setIsPrimary] = useState(true);
  const [priceThreshold, setPriceThreshold] = useState<string>('');
  const [bsrThreshold, setBsrThreshold] = useState<string>('');
  const [notes, setNotes] = useState('');

  const handleClaim = async () => {
    try {
      setLoading(true);

      const response = await userProductService.claimProduct({
        product_id: product.id,
        is_primary: isPrimary,
        price_change_threshold: priceThreshold ? Number(priceThreshold) : null,
        bsr_change_threshold: bsrThreshold ? Number(bsrThreshold) : null,
        notes: notes || null,
      });

      toast({
        title: 'Product Claimed!',
        description: response.message,
      });

      onOpenChange(false);
      onSuccess?.();

      // Reset form
      setPriceThreshold('');
      setBsrThreshold('');
      setNotes('');
      setIsPrimary(true);
    } catch (error: any) {
      toast({
        title: 'Failed to Claim Product',
        description: error.response?.data?.detail || 'An error occurred',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>Claim Product</DialogTitle>
          <DialogDescription>
            Mark this product as yours to enable custom tracking and alerts.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Product Info */}
          <div className="space-y-2">
            <Label>Product</Label>
            <div className="rounded-md border p-3 bg-muted/50">
              <p className="font-medium text-sm">{product.title}</p>
              <p className="text-xs text-muted-foreground mt-1">
                ASIN: {product.asin}
              </p>
              {product.category && (
                <p className="text-xs text-muted-foreground">
                  Category: {product.category}
                </p>
              )}
            </div>
          </div>

          {/* Primary Product */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="is_primary"
              checked={isPrimary}
              onChange={e => setIsPrimary(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300"
            />
            <Label
              htmlFor="is_primary"
              className="text-sm font-normal cursor-pointer"
            >
              This is my primary product
            </Label>
          </div>

          {/* Custom Price Threshold */}
          <div className="space-y-2">
            <Label htmlFor="price_threshold">
              Custom Price Alert Threshold (%)
            </Label>
            <Input
              id="price_threshold"
              type="number"
              step="0.1"
              placeholder="Leave empty to use default"
              value={priceThreshold}
              onChange={e => setPriceThreshold(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Get alerts when price changes by more than this percentage
            </p>
          </div>

          {/* Custom BSR Threshold */}
          <div className="space-y-2">
            <Label htmlFor="bsr_threshold">
              Custom BSR Alert Threshold (%)
            </Label>
            <Input
              id="bsr_threshold"
              type="number"
              step="0.1"
              placeholder="Leave empty to use default"
              value={bsrThreshold}
              onChange={e => setBsrThreshold(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Get alerts when BSR changes by more than this percentage
            </p>
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <Label htmlFor="notes">Notes (Optional)</Label>
            <Textarea
              id="notes"
              placeholder="Add notes about this product..."
              value={notes}
              onChange={e => setNotes(e.target.value)}
              rows={3}
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button onClick={handleClaim} disabled={loading}>
            {loading ? 'Claiming...' : 'Claim Product'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
