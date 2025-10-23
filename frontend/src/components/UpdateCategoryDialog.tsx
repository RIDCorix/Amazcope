import { Loader2, Tags } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from '@/components/ui/use-toast';
import { Product, productService } from '@/services/productService';

interface UpdateCategoryDialogProps {
  product: Product;
  onUpdate: (updatedProduct: Product) => void;
  children?: React.ReactNode;
}

export function UpdateCategoryDialog({
  product,
  onUpdate,
  children,
}: UpdateCategoryDialogProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    category_url: product.bsr_category_link || '',
    manual_category: product.category || '',
    manual_small_category: product.small_category || '',
    trigger_bestsellers_scrape: true,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const updatedProduct = await productService.updateProductCategory(
        product.id,
        {
          category_url: formData.category_url.trim() || null,
          manual_category: formData.manual_category.trim() || null,
          manual_small_category: formData.manual_small_category.trim() || null,
          trigger_bestsellers_scrape: formData.trigger_bestsellers_scrape,
        }
      );

      toast({
        title: 'Category Updated',
        description: 'Product category has been updated successfully.',
      });

      onUpdate(updatedProduct);
      setOpen(false);
    } catch (err: any) {
      toast({
        title: 'Update Failed',
        description: err.message || 'Failed to update product category.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {children || (
          <Button variant="outline" size="sm">
            <Tags className="w-4 h-4 mr-2" />
            Update Category
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Update Product Category</DialogTitle>
            <DialogDescription>
              Manually set or override category information for this product.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="category_url">Category URL</Label>
              <Input
                id="category_url"
                type="url"
                placeholder="https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics"
                value={formData.category_url}
                onChange={e =>
                  setFormData({ ...formData, category_url: e.target.value })
                }
                disabled={loading}
              />
              <p className="text-sm text-gray-500">
                Amazon category URL for bestseller tracking
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="manual_category">Category Name</Label>
              <Input
                id="manual_category"
                type="text"
                placeholder="Electronics"
                value={formData.manual_category}
                onChange={e =>
                  setFormData({ ...formData, manual_category: e.target.value })
                }
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="manual_small_category">Subcategory</Label>
              <Input
                id="manual_small_category"
                type="text"
                placeholder="Headphones"
                value={formData.manual_small_category}
                onChange={e =>
                  setFormData({
                    ...formData,
                    manual_small_category: e.target.value,
                  })
                }
                disabled={loading}
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="trigger_bestsellers_scrape"
                checked={formData.trigger_bestsellers_scrape}
                onChange={e =>
                  setFormData({
                    ...formData,
                    trigger_bestsellers_scrape: e.target.checked,
                  })
                }
                disabled={loading}
                className="w-4 h-4"
              />
              <Label
                htmlFor="trigger_bestsellers_scrape"
                className="cursor-pointer"
              >
                Trigger bestsellers scraping immediately
              </Label>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
              <p className="text-sm text-blue-800">
                💡 Manual categories override auto-detected values. Leave blank
                to use scraped data.
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : (
                'Update Category'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
