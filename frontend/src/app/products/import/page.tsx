import { ArrowLeft, CheckCircle2, Clock, Link2, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { CategoryURLGuide } from '@/components/CategoryURLGuide';
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
import { Label } from '@/components/ui/label';
import { useTranslation } from '@/hooks/useTranslation';
import { productService } from '@/services/productService';

interface BackgroundJob {
  name: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  icon: React.ReactNode;
}

export default function AddProductFromUrlPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [productAdded, setProductAdded] = useState(false);
  const [productId, setProductId] = useState<string | null>(null);
  const [backgroundJobs, setBackgroundJobs] = useState<BackgroundJob[]>([]);

  const [formData, setFormData] = useState({
    url: '',
    price_change_threshold: '10.0',
    bsr_change_threshold: '30.0',
    scrape_reviews: true,
    scrape_bestsellers: true,
    category_url: '',
    manual_category: '',
    manual_small_category: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const product = await productService.importFromUrl({
        url: formData.url.trim(),
        price_change_threshold: parseFloat(formData.price_change_threshold),
        bsr_change_threshold: parseFloat(formData.bsr_change_threshold),
        scrape_reviews: formData.scrape_reviews,
        scrape_bestsellers: formData.scrape_bestsellers,
        category_url: formData.category_url.trim() || null,
        manual_category: formData.manual_category.trim() || null,
        manual_small_category: formData.manual_small_category.trim() || null,
      });

      setProductId(product.id);
      setProductAdded(true);

      // Initialize background jobs status
      const jobs: BackgroundJob[] = [
        {
          name: 'Product Details',
          status: 'queued',
          icon: <Clock className="w-4 h-4" />,
        },
      ];

      if (formData.scrape_reviews) {
        jobs.push({
          name: 'Product Reviews',
          status: 'queued',
          icon: <Clock className="w-4 h-4" />,
        });
      }

      if (formData.scrape_bestsellers) {
        jobs.push({
          name: 'Category Bestsellers',
          status: 'queued',
          icon: <Clock className="w-4 h-4" />,
        });
      }

      setBackgroundJobs(jobs);

      // Simulate job status updates (in production, use WebSocket or polling)
      setTimeout(() => {
        setBackgroundJobs(prev =>
          prev.map((job, idx) =>
            idx === 0 ? { ...job, status: 'running' } : job
          )
        );
      }, 2000);

      setTimeout(() => {
        setBackgroundJobs(prev =>
          prev.map((job, idx) =>
            idx === 0 ? { ...job, status: 'completed' } : job
          )
        );
      }, 5000);

      // Auto redirect after 8 seconds
      setTimeout(() => {
        navigate(`/products/${product.id}`);
      }, 8000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const extractAsinFromUrl = (url: string): string | null => {
    const patterns = [
      /\/dp\/([A-Z0-9]{10})/i,
      /\/gp\/product\/([A-Z0-9]{10})/i,
      /\/product\/([A-Z0-9]{10})/i,
      /[?&]asin=([A-Z0-9]{10})/i,
    ];

    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) {
        return match[1].toUpperCase();
      }
    }
    return null;
  };

  const handleUrlChange = (url: string) => {
    setFormData({ ...formData, url });

    // Try to extract ASIN for preview
    const asin = extractAsinFromUrl(url);
    if (asin) {
      // Show visual feedback that URL is valid
      setError('');
    }
  };

  const getJobBadge = (status: BackgroundJob['status']) => {
    switch (status) {
      case 'queued':
        return (
          <Badge variant="secondary">{t('import.jobQueued') || 'Queued'}</Badge>
        );
      case 'running':
        return (
          <Badge className="bg-blue-600">
            {t('import.jobRunning') || 'Running'}
          </Badge>
        );
      case 'completed':
        return (
          <Badge className="bg-green-600">
            {t('import.jobCompleted') || 'Completed'}
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive">
            {t('import.jobFailed') || 'Failed'}
          </Badge>
        );
    }
  };

  if (productAdded) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-2xl">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3 mb-2">
              <CheckCircle2 className="w-8 h-8 text-green-600" />
              <CardTitle>
                {t('import.productAddedSuccess') ||
                  'Product Added Successfully!'}
              </CardTitle>
            </div>
            <CardDescription>
              {t('import.backgroundJobsProcessing') ||
                'Background jobs are processing product data...'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-md p-4">
              <p className="text-sm text-green-800">
                ✅{' '}
                {t('import.productAddedToTracking') ||
                  'Product has been added to your tracking list'}
              </p>
              <p className="text-sm text-green-800 mt-1">
                🚀{' '}
                {t('import.collectingData') ||
                  'Background jobs are collecting data from Amazon'}
              </p>
            </div>

            <div className="space-y-3">
              <h4 className="font-medium">
                {t('import.backgroundJobsStatus') || 'Background Jobs Status:'}:
              </h4>
              {backgroundJobs.map((job, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 border rounded-md"
                >
                  <div className="flex items-center gap-2">
                    {job.status === 'running' ? (
                      <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                    ) : job.status === 'completed' ? (
                      <CheckCircle2 className="w-4 h-4 text-green-600" />
                    ) : (
                      job.icon
                    )}
                    <span className="text-sm font-medium">{job.name}</span>
                  </div>
                  {getJobBadge(job.status)}
                </div>
              ))}
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <p className="text-sm text-blue-800">
                💡{' '}
                {t('import.navigateAway') ||
                  'You can navigate away - jobs will continue running in the background'}
              </p>
              <p className="text-sm text-blue-800 mt-1">
                ⏱️{' '}
                {t('import.redirecting') ||
                  'Redirecting to product page in a few seconds...'}
              </p>
            </div>

            <div className="flex gap-3">
              <Button
                onClick={() => navigate('/products')}
                variant="outline"
                className="flex-1"
              >
                {t('import.viewAllProducts') || 'View All Products'}
              </Button>
              <Button
                onClick={() => navigate(`/products/${productId}`)}
                className="flex-1"
              >
                {t('import.viewProductDetails') || 'View Product Details'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-2xl">
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          {t('common.back') || 'Back'}
        </Button>
        <div className="flex items-center gap-3 mb-2">
          <Link2 className="w-8 h-8 text-primary" />
          <h1 className="text-3xl font-bold">
            {t('import.title') || 'Import from Amazon URL'}
          </h1>
        </div>
        <p className="text-gray-600">
          {t('import.subtitle') ||
            "Just paste an Amazon product link and we'll handle the rest"}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('import.productUrl') || 'Product URL'}</CardTitle>
          <CardDescription>
            {t('import.productUrlDesc') ||
              "Paste any Amazon product URL - we'll automatically extract the ASIN and start tracking"}
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
              <Label htmlFor="url">
                {t('import.amazonProductUrl') || 'Amazon Product URL'}{' '}
                <span className="text-red-500">*</span>
              </Label>
              <Input
                id="url"
                type="url"
                placeholder={
                  t('import.amazonUrlPlaceholder') ||
                  'https://www.amazon.com/dp/B07XJ8C8F5'
                }
                value={formData.url}
                onChange={e => handleUrlChange(e.target.value)}
                required
                disabled={loading}
              />
              <p className="text-sm text-gray-500">
                {t('import.supportsFormats') ||
                  'Supports: /dp/, /gp/product/, ?asin= formats'}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="price_threshold">
                  {t('import.priceThreshold') || 'Price Alert Threshold (%)'}
                </Label>
                <Input
                  id="price_threshold"
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  value={formData.price_change_threshold}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      price_change_threshold: e.target.value,
                    })
                  }
                  disabled={loading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="bsr_threshold">
                  {t('import.bsrThreshold') || 'BSR Alert Threshold (%)'}
                </Label>
                <Input
                  id="bsr_threshold"
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  value={formData.bsr_change_threshold}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      bsr_change_threshold: e.target.value,
                    })
                  }
                  disabled={loading}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="category_url">
                {t('import.categoryUrl') || 'Category URL (Optional)'}
              </Label>
              <Input
                id="category_url"
                type="url"
                placeholder="https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics"
                value={formData.category_url}
                onChange={e =>
                  setFormData({
                    ...formData,
                    category_url: e.target.value,
                  })
                }
                disabled={loading}
              />
              <p className="text-sm text-gray-500">
                {t('import.categoryUrlHelp') ||
                  'Custom category URL for bestseller tracking (overrides auto-detected)'}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="manual_category">
                  {t('import.categoryName') || 'Category Name (Optional)'}
                </Label>
                <Input
                  id="manual_category"
                  type="text"
                  placeholder={t('import.categoryPlaceholder') || 'Electronics'}
                  value={formData.manual_category}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      manual_category: e.target.value,
                    })
                  }
                  disabled={loading}
                />
                <p className="text-sm text-gray-500">
                  {t('import.manualCategoryHelp') ||
                    'Manually specify category'}
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="manual_small_category">
                  {t('import.subcategory') || 'Subcategory (Optional)'}
                </Label>
                <Input
                  id="manual_small_category"
                  type="text"
                  placeholder={
                    t('import.subcategoryPlaceholder') || 'Headphones'
                  }
                  value={formData.manual_small_category}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      manual_small_category: e.target.value,
                    })
                  }
                  disabled={loading}
                />
                <p className="text-sm text-gray-500">
                  {t('import.manualSubcategoryHelp') ||
                    'Manually specify subcategory'}
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <Label>Additional Data Collection</Label>
              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.scrape_reviews}
                    onChange={e =>
                      setFormData({
                        ...formData,
                        scrape_reviews: e.target.checked,
                      })
                    }
                    disabled={loading}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">
                    {t('import.scrapeReviews') ||
                      'Scrape Product Reviews (up to 100 most recent)'}
                  </span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.scrape_bestsellers}
                    onChange={e =>
                      setFormData({
                        ...formData,
                        scrape_bestsellers: e.target.checked,
                      })
                    }
                    disabled={loading}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">
                    {t('import.scrapeBestsellers') ||
                      'Scrape Category Bestsellers (for competitive analysis)'}
                  </span>
                </label>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <h4 className="font-medium text-blue-900 mb-2">
                {t('import.whatHappens') || 'What happens after import?'}
              </h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>
                  ✅{' '}
                  {t('import.asinExtracted') ||
                    'ASIN extracted automatically from URL'}
                </li>
                <li>
                  ✅{' '}
                  {t('import.productAdded') ||
                    'Product added to database immediately'}
                </li>
                <li>
                  🚀{' '}
                  {t('import.scrapesDetails') ||
                    'Background job scrapes full product details'}
                </li>
                {formData.scrape_reviews && (
                  <li>
                    🚀{' '}
                    {t('import.scrapesReviews') ||
                      'Background job scrapes up to 100 reviews'}
                  </li>
                )}
                {formData.scrape_bestsellers && (
                  <li>
                    🚀{' '}
                    {t('import.scrapesBestsellers') ||
                      'Background job scrapes category bestsellers'}
                  </li>
                )}
                <li>
                  📊{' '}
                  {t('import.dailyUpdates') ||
                    'Daily automatic updates track all changes'}
                </li>
                <li>
                  🔔{' '}
                  {t('import.alertsTriggered') ||
                    'Alerts triggered when thresholds exceeded'}
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
                {t('common.cancel') || 'Cancel'}
              </Button>
              <Button
                type="submit"
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    {t('import.importingProduct') || 'Importing Product...'}
                  </>
                ) : (
                  <>
                    <Link2 className="w-4 h-4" />
                    {t('import.importProduct') || 'Import Product'}
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Category URL Guide */}
      <div className="mt-6">
        <CategoryURLGuide />
      </div>

      {/* Example URLs */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-lg">
            {t('import.exampleUrls') || 'Example Amazon URLs'}
          </CardTitle>
          <CardDescription>
            {t('import.clickToTry') ||
              'Click any URL to try the import feature'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[
              {
                url: 'https://www.amazon.com/dp/B07XJ8C8F5',
                name: 'Echo Dot (4th Gen)',
              },
              {
                url: 'https://www.amazon.com/dp/B08J5F3G18',
                name: 'Fire TV Stick 4K',
              },
              {
                url: 'https://www.amazon.com/dp/B09B8RXSC5',
                name: 'Kindle Paperwhite',
              },
            ].map((example, idx) => (
              <div
                key={idx}
                className="p-3 border rounded-md cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => setFormData({ ...formData, url: example.url })}
              >
                <div className="text-sm font-medium mb-1">{example.name}</div>
                <div className="text-xs text-gray-600 font-mono truncate">
                  {example.url}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
