import { ArrowLeft, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function AddProductPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    asin: '',
    price_change_threshold: '10.0',
    bsr_change_threshold: '30.0',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const token = localStorage.getItem('authToken');

      const response = await fetch(
        'http://localhost:8000/api/v1/tracking/products',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            asin: formData.asin.trim().toUpperCase(),
            price_change_threshold: parseFloat(formData.price_change_threshold),
            bsr_change_threshold: parseFloat(formData.bsr_change_threshold),
          }),
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to add product');
      }

      const product = await response.json();
      navigate(`/products/${product.id}`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-2xl">
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </Button>
        <h1 className="text-3xl font-bold">Add Product to Track</h1>
        <p className="text-gray-600 mt-1">
          Enter an Amazon ASIN to start tracking price and BSR changes
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Product Details</CardTitle>
          <CardDescription>
            The product will be automatically scraped after adding
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="asin">
                ASIN <span className="text-red-500">*</span>
              </Label>
              <Input
                id="asin"
                type="text"
                placeholder="B07XJ8C8F5"
                value={formData.asin}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFormData({ ...formData, asin: e.target.value })
                }
                required
                maxLength={10}
                minLength={10}
                pattern="[A-Z0-9]{10}"
                disabled={loading}
                className="font-mono"
              />
              <p className="text-sm text-gray-500">
                Amazon Standard Identification Number (10 characters)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="price_threshold">
                Price Change Alert Threshold (%)
              </Label>
              <Input
                id="price_threshold"
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={formData.price_change_threshold}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFormData({
                    ...formData,
                    price_change_threshold: e.target.value,
                  })
                }
                disabled={loading}
              />
              <p className="text-sm text-gray-500">
                Get notified when price changes by more than this percentage
                (default: 10%)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="bsr_threshold">
                BSR Change Alert Threshold (%)
              </Label>
              <Input
                id="bsr_threshold"
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={formData.bsr_change_threshold}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFormData({
                    ...formData,
                    bsr_change_threshold: e.target.value,
                  })
                }
                disabled={loading}
              />
              <p className="text-sm text-gray-500">
                Get notified when BSR (Best Sellers Rank) changes by more than
                this percentage (default: 30%)
              </p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <h4 className="font-medium text-blue-900 mb-2">
                What happens next?
              </h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Product will be scraped from Amazon via Apify</li>
                <li>• Initial snapshot will be created with current data</li>
                <li>• Daily automatic updates will track changes</li>
                <li>
                  • You&apos;ll receive alerts when thresholds are exceeded
                </li>
              </ul>
            </div>

            <div className="flex gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate(-1)}
                disabled={loading}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Adding Product...
                  </>
                ) : (
                  'Add Product'
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Example ASINs */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-lg">Example ASINs</CardTitle>
          <CardDescription>
            You can try these popular product ASINs for testing
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div
              className="p-3 border rounded-md cursor-pointer hover:bg-gray-50"
              onClick={() => setFormData({ ...formData, asin: 'B07XJ8C8F5' })}
            >
              <div className="font-mono font-medium">B07XJ8C8F5</div>
              <div className="text-sm text-gray-600">Echo Dot (4th Gen)</div>
            </div>
            <div
              className="p-3 border rounded-md cursor-pointer hover:bg-gray-50"
              onClick={() => setFormData({ ...formData, asin: 'B08J5F3G18' })}
            >
              <div className="font-mono font-medium">B08J5F3G18</div>
              <div className="text-sm text-gray-600">Fire TV Stick 4K</div>
            </div>
            <div
              className="p-3 border rounded-md cursor-pointer hover:bg-gray-50"
              onClick={() => setFormData({ ...formData, asin: 'B09B8RXSC5' })}
            >
              <div className="font-mono font-medium">B09B8RXSC5</div>
              <div className="text-sm text-gray-600">Kindle Paperwhite</div>
            </div>
            <div
              className="p-3 border rounded-md cursor-pointer hover:bg-gray-50"
              onClick={() => setFormData({ ...formData, asin: 'B0BDHWDR12' })}
            >
              <div className="font-mono font-medium">B0BDHWDR12</div>
              <div className="text-sm text-gray-600">Ring Video Doorbell</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
