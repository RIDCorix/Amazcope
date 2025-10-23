import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Select } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { useTranslation } from '@/hooks/useTranslation';
import { authService } from '@/services/authService';
import {
  notificationService,
  type Notification,
} from '@/services/notificationService';
import { optimizationService } from '@/services/optimizationService';
import { productService } from '@/services/productService';

interface User {
  id: string;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
}

interface DashboardStats {
  totalProducts: number;
  activeAlerts: number;
  priceChanges: number;
  avgPrice: number;
}

// Utility function to format relative time
const formatRelativeTime = (dateString: string, t: any): string => {
  const now = new Date();
  const date = new Date(dateString);
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return t('time.now') || 'Just now';
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return diffInMinutes === 1
      ? t('time.minutesAgo', { count: 1 })
      : t('time.minutesAgo_plural', { count: diffInMinutes });
  }

  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return diffInHours === 1
      ? t('time.hoursAgo', { count: 1 })
      : t('time.hoursAgo_plural', { count: diffInHours });
  }

  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) {
    return diffInDays === 1
      ? t('time.daysAgo', { count: 1 })
      : t('time.daysAgo_plural', { count: diffInDays });
  }

  const diffInWeeks = Math.floor(diffInDays / 7);
  if (diffInWeeks < 4) {
    return diffInWeeks === 1
      ? t('time.weeksAgo', { count: 1 })
      : t('time.weeksAgo_plural', { count: diffInWeeks });
  }

  const diffInMonths = Math.floor(diffInDays / 30);
  return diffInMonths === 1
    ? t('time.monthsAgo', { count: 1 })
    : t('time.monthsAgo_plural', { count: diffInMonths });
};

// Get notification type color
const getNotificationColor = (type: string): string => {
  switch (type) {
    case 'success':
      return 'bg-green-600';
    case 'warning':
      return 'bg-orange-600';
    case 'error':
      return 'bg-red-600';
    default:
      return 'bg-blue-600';
  }
};

export default function DashboardPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { t } = useTranslation();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats>({
    totalProducts: 0,
    activeAlerts: 0,
    priceChanges: 0,
    avgPrice: 0,
  });
  const [showReportDialog, setShowReportDialog] = useState(false);
  const [selectedProductId, setSelectedProductId] = useState<string>('');
  const [products, setProducts] = useState<any[]>([]);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [recentNotifications, setRecentNotifications] = useState<
    Notification[]
  >([]);

  useEffect(() => {
    // Check authentication
    if (!authService.isLoggedIn()) {
      navigate('/login');
      return;
    }

    fetchDashboardData();
  }, [navigate]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);

      // Get user data from auth service
      const userData = authService.getStoredUser();
      setUser(userData);

      // Fetch real products data
      const productsData = await productService.getProducts();
      setProducts(productsData);

      // Calculate real stats from products
      const totalProducts = productsData.length;
      const activeAlerts = productsData.reduce(
        (sum, p) => sum + (p.unread_alerts_count || 0),
        0
      );

      // Calculate price changes in last 24h (products with recent updates)
      const now = new Date();
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      const priceChanges = productsData.filter(p => {
        if (!p.updated_at) return false;
        return new Date(p.updated_at) > yesterday;
      }).length;

      // Calculate average price from denormalized price field
      const pricesWithValues = productsData
        .filter(p => p.price != null && p.price !== '')
        .map(p => parseFloat(String(p.price)));
      const avgPrice =
        pricesWithValues.length > 0
          ? pricesWithValues.reduce((sum, price) => sum + price, 0) /
            pricesWithValues.length
          : 0;

      setStats({
        totalProducts,
        activeAlerts,
        priceChanges,
        avgPrice,
      });

      // Fetch recent notifications
      try {
        const notifications = await notificationService.getNotifications({
          limit: 5,
          status: 'unread',
        });
        setRecentNotifications(notifications);
      } catch (error) {
        console.error('Failed to fetch notifications:', error);
        // Fallback to empty array if notifications fail
        setRecentNotifications([]);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddProduct = () => {
    navigate('/products');
  };

  const handleViewAlerts = () => {
    navigate('/alerts');
  };

  const handleGenerateReportSubmit = async () => {
    if (!selectedProductId) {
      toast({
        title: t('dashboard.noProductSelected') || 'No product selected',
        description:
          t('dashboard.selectProductToGenerate') ||
          'Please select a product to generate a report.',
        variant: 'destructive',
      });
      return;
    }

    try {
      setGeneratingReport(true);
      await optimizationService.generateSuggestions({
        product_id: selectedProductId,
        include_competitors: true,
      });

      toast({
        title:
          t('dashboard.reportGeneratedSuccess') ||
          'Report generated successfully',
        description:
          t('dashboard.suggestionsCreated') ||
          'AI-powered optimization suggestions have been created.',
      });

      setShowReportDialog(false);
      setSelectedProductId('');

      // Navigate to the product detail page to view suggestions
      navigate(`/products/${selectedProductId}`);
    } catch (error: any) {
      toast({
        title:
          t('dashboard.reportGenerationFailed') || 'Failed to generate report',
        description:
          error.message ||
          t('dashboard.reportGenerationError') ||
          'An error occurred while generating the report.',
        variant: 'destructive',
      });
    } finally {
      setGeneratingReport(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">
            {t('dashboard.loadingDashboard') || 'Loading dashboard...'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-foreground mb-2">
            {t('dashboard.welcomeBack', {
              name: user?.full_name || t('dashboard.there') || 'there',
            })}
          </h2>
          <p className="text-muted-foreground">
            {t('dashboard.todayOverview') ||
              "Here's what's happening with your Amazon products today."}
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>{t('dashboard.totalProducts')}</CardDescription>
              <CardTitle className="text-3xl">{stats.totalProducts}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                {t('dashboard.productsMonitored') || 'Products being monitored'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>{t('dashboard.activeAlerts')}</CardDescription>
              <CardTitle className="text-3xl text-orange-600">
                {stats.activeAlerts}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                {t('dashboard.alertsAttention') || 'Alerts requiring attention'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>{t('dashboard.priceChanges')}</CardDescription>
              <CardTitle className="text-3xl text-blue-600">
                {stats.priceChanges}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                {t('dashboard.changesLast24h') || 'Changes in the last 24h'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>{t('dashboard.avgPrice')}</CardDescription>
              <CardTitle className="text-3xl text-green-600">
                ${stats.avgPrice.toFixed(2)}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                {t('dashboard.averagePrice') || 'Average product price'}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>{t('dashboard.quickActions')}</CardTitle>
              <CardDescription>
                {t('dashboard.quickActionsDesc') ||
                  'Common tasks and shortcuts'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                className="w-full justify-start"
                variant="outline"
                onClick={handleAddProduct}
              >
                <svg
                  className="mr-2 h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                {t('dashboard.addNewProduct') || 'Add New Product'}
              </Button>
              <Button
                className="w-full justify-start"
                variant="outline"
                onClick={handleViewAlerts}
              >
                <svg
                  className="mr-2 h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                {t('dashboard.viewAllAlerts') || 'View All Alerts'}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('dashboard.recentActivity')}</CardTitle>
              <CardDescription>
                {t('dashboard.recentActivityDesc') ||
                  'Latest updates from your products'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {recentNotifications.length > 0 ? (
                <div className="space-y-4">
                  {recentNotifications.map(notification => (
                    <div
                      key={notification.id}
                      className="flex items-start gap-3"
                    >
                      <div
                        className={`w-2 h-2 rounded-full mt-2 ${getNotificationColor(notification.type)}`}
                      ></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium">
                          {notification.title}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {notification.message} -{' '}
                          {formatRelativeTime(notification.created_at, t)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-sm text-muted-foreground">
                    {t('notifications.noNotifications') || 'No recent activity'}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Report Generation Dialog */}
      <Dialog open={showReportDialog} onOpenChange={setShowReportDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {t('dashboard.generateReportTitle') ||
                'Generate Optimization Report'}
            </DialogTitle>
            <DialogDescription>
              {t('dashboard.generateReportDesc') ||
                'Select a product to generate AI-powered optimization suggestions and insights.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label htmlFor="product-select" className="text-sm font-medium">
                {t('dashboard.selectProduct') || 'Select Product'}
              </label>
              <Select
                id="product-select"
                value={selectedProductId}
                onChange={e => setSelectedProductId(e.target.value)}
              >
                <option value="">
                  {t('dashboard.chooseProduct') || 'Choose a product...'}
                </option>
                {products.map(product => (
                  <option key={product.id} value={String(product.id)}>
                    {product.title} ({product.asin})
                  </option>
                ))}
              </Select>
            </div>
            <div className="flex justify-end gap-3">
              <Button
                variant="outline"
                onClick={() => {
                  setShowReportDialog(false);
                  setSelectedProductId('');
                }}
                disabled={generatingReport}
              >
                {t('common.cancel')}
              </Button>
              <Button
                onClick={handleGenerateReportSubmit}
                disabled={!selectedProductId || generatingReport}
              >
                {generatingReport ? (
                  <>
                    <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent"></div>
                    {t('dashboard.generating') || 'Generating...'}
                  </>
                ) : (
                  t('dashboard.generateReport') || 'Generate Report'
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
