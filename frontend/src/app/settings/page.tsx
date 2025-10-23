import {
  ArrowLeft,
  Bell,
  DollarSign,
  Eye,
  Loader2,
  RefreshCw,
  RotateCcw,
  Save,
  Shield,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useTheme } from '@/components/theme-provider';
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
import { Select, SelectItem } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { useTranslation } from '@/hooks/useTranslation';
import { setLocaleCookie, type Locale } from '@/i18n/config';
import {
  settingsService,
  type UserSettings,
  type UserSettingsUpdate,
} from '@/services/settingsService';

export default function SettingsPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { setTheme } = useTheme();
  const { t } = useTranslation();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState<UserSettings | null>(null);

  const fetchSettings = useCallback(async () => {
    try {
      setLoading(true);
      const data = await settingsService.getSettings();
      setSettings(data);
    } catch (error: any) {
      toast({
        title: t('common.error'),
        description: error.message || t('settings.error'),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleSave = async () => {
    if (!settings) return;

    try {
      setSaving(true);

      const updateData: UserSettingsUpdate = {
        // Notification Settings
        email_notifications_enabled: settings.email_notifications_enabled,
        price_alert_emails: settings.price_alert_emails,
        bsr_alert_emails: settings.bsr_alert_emails,
        stock_alert_emails: settings.stock_alert_emails,
        daily_summary_emails: settings.daily_summary_emails,
        weekly_report_emails: settings.weekly_report_emails,

        // Thresholds
        default_price_threshold: settings.default_price_threshold,
        default_bsr_threshold: settings.default_bsr_threshold,

        // Display
        theme: settings.theme,
        language: settings.language,
        timezone: settings.timezone,
        date_format: settings.date_format,
        currency_display: settings.currency_display,

        // Dashboard
        products_per_page: settings.products_per_page,
        default_sort_by: settings.default_sort_by,
        default_sort_order: settings.default_sort_order,
        show_inactive_products: settings.show_inactive_products,

        // Refresh
        auto_refresh_dashboard: settings.auto_refresh_dashboard,
        refresh_interval_minutes: settings.refresh_interval_minutes,

        // Privacy
        share_analytics: settings.share_analytics,
      };

      const updated = await settingsService.updateSettings(updateData);
      setSettings(updated);

      // Update locale cookie if language changed
      if (
        settings.language &&
        ['en', 'zh', 'es', 'fr', 'de', 'ja'].includes(settings.language)
      ) {
        setLocaleCookie(settings.language as Locale);
      }

      // Apply theme change immediately using ThemeProvider
      if (settings.theme) {
        setTheme(settings.theme);
        // Also save to cookie for SSR
        document.cookie = `amazcope-theme=${settings.theme}; path=/; max-age=31536000; SameSite=Lax`;
      }

      toast({
        title: t('common.success'),
        description: t('settings.saved'),
      });

      // Refresh page to apply language change
      navigate(0);
    } catch (error: any) {
      toast({
        title: t('common.error'),
        description: error.message || t('settings.error'),
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (
      !confirm(
        t('settings.resetConfirm') ||
          'Are you sure you want to reset all settings to defaults?'
      )
    ) {
      return;
    }

    try {
      setSaving(true);
      const defaults = await settingsService.resetSettings();
      setSettings(defaults);

      toast({
        title: t('common.success'),
        description: t('settings.resetSuccess') || 'Settings reset to defaults',
      });
    } catch (error: any) {
      toast({
        title: t('common.error'),
        description:
          error.message ||
          t('settings.resetError') ||
          'Failed to reset settings',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="text-center">
          <p className="text-red-600">{t('settings.error')}</p>
          <Button onClick={fetchSettings} className="mt-4">
            {t('common.retry') || 'Retry'}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          {t('common.back')}
        </Button>
        <h1 className="text-3xl font-bold">{t('settings.title')}</h1>
        <p className="text-gray-600 mt-2">
          {t('settings.subtitle') ||
            'Manage your account settings and preferences'}
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="notifications" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="notifications">
            <Bell className="w-4 h-4 mr-2" />
            {t('settings.notificationsTab')}
          </TabsTrigger>
          <TabsTrigger value="display">
            <Eye className="w-4 h-4 mr-2" />
            {t('settings.displayTab')}
          </TabsTrigger>
          <TabsTrigger value="thresholds">
            <DollarSign className="w-4 h-4 mr-2" />
            {t('settings.alertsTab')}
          </TabsTrigger>
          <TabsTrigger value="dashboard">
            <RefreshCw className="w-4 h-4 mr-2" />
            {t('settings.dashboardTab')}
          </TabsTrigger>
          <TabsTrigger value="privacy">
            <Shield className="w-4 h-4 mr-2" />
            {t('settings.privacyTab')}
          </TabsTrigger>
        </TabsList>

        {/* Notifications Tab */}
        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle>{t('settings.notifications.title')}</CardTitle>
              <CardDescription>
                {t('settings.notifications.description') ||
                  'Control how and when you receive notifications'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between py-3">
                <div className="space-y-0.5">
                  <Label
                    htmlFor="email-notifications"
                    className="text-base font-medium"
                  >
                    {t('settings.notifications.emailNotifications')}
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    {t('settings.notifications.emailDescription') ||
                      'Enable or disable all email notifications'}
                  </p>
                </div>
                <Switch
                  id="email-notifications"
                  checked={settings.email_notifications_enabled}
                  onCheckedChange={checked =>
                    setSettings({
                      ...settings,
                      email_notifications_enabled: checked,
                    })
                  }
                />
              </div>

              <div className="border-t pt-4 space-y-4">
                <div className="flex items-center justify-between py-2">
                  <Label htmlFor="price-alerts" className="font-normal">
                    {t('settings.notifications.priceAlerts')}
                  </Label>
                  <Switch
                    id="price-alerts"
                    checked={settings.price_alert_emails}
                    onCheckedChange={checked =>
                      setSettings({
                        ...settings,
                        price_alert_emails: checked,
                      })
                    }
                    disabled={!settings.email_notifications_enabled}
                  />
                </div>

                <div className="flex items-center justify-between py-2">
                  <Label htmlFor="bsr-alerts" className="font-normal">
                    {t('settings.notifications.bsrAlerts')}
                  </Label>
                  <Switch
                    id="bsr-alerts"
                    checked={settings.bsr_alert_emails}
                    onCheckedChange={checked =>
                      setSettings({
                        ...settings,
                        bsr_alert_emails: checked,
                      })
                    }
                    disabled={!settings.email_notifications_enabled}
                  />
                </div>

                <div className="flex items-center justify-between py-2">
                  <Label htmlFor="stock-alerts" className="font-normal">
                    {t('settings.notifications.stockAlerts')}
                  </Label>
                  <Switch
                    id="stock-alerts"
                    checked={settings.stock_alert_emails}
                    onCheckedChange={checked =>
                      setSettings({
                        ...settings,
                        stock_alert_emails: checked,
                      })
                    }
                    disabled={!settings.email_notifications_enabled}
                  />
                </div>

                <div className="flex items-center justify-between py-2">
                  <Label htmlFor="daily-summary" className="font-normal">
                    {t('settings.notifications.dailySummary')}
                  </Label>
                  <Switch
                    id="daily-summary"
                    checked={settings.daily_summary_emails}
                    onCheckedChange={checked =>
                      setSettings({
                        ...settings,
                        daily_summary_emails: checked,
                      })
                    }
                    disabled={!settings.email_notifications_enabled}
                  />
                </div>

                <div className="flex items-center justify-between py-2">
                  <Label htmlFor="weekly-report" className="font-normal">
                    {t('settings.notifications.weeklyReport')}
                  </Label>
                  <Switch
                    id="weekly-report"
                    checked={settings.weekly_report_emails}
                    onCheckedChange={checked =>
                      setSettings({
                        ...settings,
                        weekly_report_emails: checked,
                      })
                    }
                    disabled={!settings.email_notifications_enabled}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Display Tab */}
        <TabsContent value="display">
          <Card>
            <CardHeader>
              <CardTitle>{t('settings.display.title')}</CardTitle>
              <CardDescription>
                {t('settings.display.description') ||
                  'Customize how information is displayed'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="theme" className="text-base font-medium">
                    {t('settings.display.theme')}
                  </Label>
                  <Select
                    value={settings.theme}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                      setSettings({
                        ...settings,
                        theme: e.target.value as 'light' | 'dark' | 'auto',
                      })
                    }
                  >
                    <SelectItem value="light">
                      {t('settings.display.light')}
                    </SelectItem>
                    <SelectItem value="dark">
                      {t('settings.display.dark')}
                    </SelectItem>
                    <SelectItem value="auto">
                      {t('settings.display.auto')}
                    </SelectItem>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="language" className="text-base font-medium">
                    {t('settings.display.language')}
                  </Label>
                  <Select
                    id="language"
                    value={settings.language}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                      setSettings({ ...settings, language: e.target.value })
                    }
                  >
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="zh">中文</SelectItem>
                    <SelectItem value="es">Español</SelectItem>
                    <SelectItem value="fr">Français</SelectItem>
                    <SelectItem value="de">Deutsch</SelectItem>
                    <SelectItem value="ja">日本語</SelectItem>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="currency" className="text-base font-medium">
                    {t('settings.display.currency')}
                  </Label>
                  <Select
                    id="currency"
                    value={settings.currency_display}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                      setSettings({
                        ...settings,
                        currency_display: e.target.value,
                      })
                    }
                  >
                    <SelectItem value="USD">USD ($)</SelectItem>
                    <SelectItem value="EUR">EUR (€)</SelectItem>
                    <SelectItem value="GBP">GBP (£)</SelectItem>
                    <SelectItem value="JPY">JPY (¥)</SelectItem>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="timezone" className="text-base font-medium">
                    {t('settings.display.timezone')}
                  </Label>
                  <Input
                    id="timezone"
                    value={settings.timezone}
                    onChange={e =>
                      setSettings({ ...settings, timezone: e.target.value })
                    }
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Thresholds Tab */}
        <TabsContent value="thresholds">
          <Card>
            <CardHeader>
              <CardTitle>{t('settings.alerts.title')}</CardTitle>
              <CardDescription>
                {t('settings.alerts.description') ||
                  'Default thresholds for new products'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label
                  htmlFor="price-threshold"
                  className="text-base font-medium"
                >
                  {t('settings.alerts.priceThreshold')}
                </Label>
                <Input
                  id="price-threshold"
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={settings.default_price_threshold}
                  onChange={e =>
                    setSettings({
                      ...settings,
                      default_price_threshold: parseFloat(e.target.value),
                    })
                  }
                  className="max-w-xs"
                />
                <p className="text-sm text-muted-foreground">
                  {t('settings.alerts.priceDescription') ||
                    'Alert when price changes by this percentage'}
                </p>
              </div>

              <div className="space-y-2">
                <Label
                  htmlFor="bsr-threshold"
                  className="text-base font-medium"
                >
                  {t('settings.alerts.bsrThreshold')}
                </Label>
                <Input
                  id="bsr-threshold"
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={settings.default_bsr_threshold}
                  onChange={e =>
                    setSettings({
                      ...settings,
                      default_bsr_threshold: parseFloat(e.target.value),
                    })
                  }
                  className="max-w-xs"
                />
                <p className="text-sm text-muted-foreground">
                  {t('settings.alerts.bsrDescription') ||
                    'Alert when BSR rank changes by this percentage'}
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard">
          <Card>
            <CardHeader>
              <CardTitle>{t('settings.dashboard.title')}</CardTitle>
              <CardDescription>
                {t('settings.dashboard.description') ||
                  'Customize your dashboard experience'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label
                    htmlFor="products-per-page"
                    className="text-base font-medium"
                  >
                    {t('settings.dashboard.productsPerPage')}
                  </Label>
                  <Input
                    id="products-per-page"
                    type="number"
                    min="10"
                    max="100"
                    value={settings.products_per_page}
                    onChange={e =>
                      setSettings({
                        ...settings,
                        products_per_page: parseInt(e.target.value),
                      })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="sort-order" className="text-base font-medium">
                    {t('settings.dashboard.defaultSortOrder')}
                  </Label>
                  <Select
                    id="sort-order"
                    value={settings.default_sort_order}
                    onChange={e =>
                      setSettings({
                        ...settings,
                        default_sort_order: e.target.value as 'asc' | 'desc',
                      })
                    }
                  >
                    <SelectItem value="asc">
                      {t('settings.dashboard.ascending')}
                    </SelectItem>
                    <SelectItem value="desc">
                      {t('settings.dashboard.descending')}
                    </SelectItem>
                  </Select>
                </div>
              </div>

              <div className="flex items-center justify-between py-3 border-t">
                <div className="space-y-0.5">
                  <Label
                    htmlFor="show-inactive"
                    className="text-base font-medium"
                  >
                    {t('settings.dashboard.showInactive')}
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    {t('settings.dashboard.showInactiveDescription') ||
                      'Display inactive products in the list'}
                  </p>
                </div>
                <Switch
                  id="show-inactive"
                  checked={settings.show_inactive_products}
                  onCheckedChange={checked =>
                    setSettings({
                      ...settings,
                      show_inactive_products: checked,
                    })
                  }
                />
              </div>

              <div className="border-t pt-6">
                <div className="flex items-center justify-between py-3 mb-4">
                  <div className="space-y-0.5">
                    <Label
                      htmlFor="auto-refresh"
                      className="text-base font-medium"
                    >
                      {t('settings.dashboard.autoRefresh')}
                    </Label>
                    <p className="text-sm text-muted-foreground">
                      {t('settings.dashboard.autoRefreshDescription') ||
                        'Automatically refresh data'}
                    </p>
                  </div>
                  <Switch
                    id="auto-refresh"
                    checked={settings.auto_refresh_dashboard}
                    onCheckedChange={checked =>
                      setSettings({
                        ...settings,
                        auto_refresh_dashboard: checked,
                      })
                    }
                  />
                </div>

                {settings.auto_refresh_dashboard && (
                  <div className="space-y-2 ml-0">
                    <Label
                      htmlFor="refresh-interval"
                      className="text-base font-medium"
                    >
                      {t('settings.dashboard.refreshInterval')}
                    </Label>
                    <Input
                      id="refresh-interval"
                      type="number"
                      min="1"
                      max="60"
                      value={settings.refresh_interval_minutes}
                      onChange={e =>
                        setSettings({
                          ...settings,
                          refresh_interval_minutes: parseInt(e.target.value),
                        })
                      }
                      className="max-w-xs"
                    />
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Privacy Tab */}
        <TabsContent value="privacy">
          <Card>
            <CardHeader>
              <CardTitle>{t('settings.privacy.title')}</CardTitle>
              <CardDescription>
                {t('settings.privacy.description') ||
                  'Control your data and privacy preferences'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between py-3">
                <div className="space-y-0.5">
                  <Label
                    htmlFor="share-analytics"
                    className="text-base font-medium"
                  >
                    {t('settings.privacy.shareAnalytics')}
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    {t('settings.privacy.shareAnalyticsDescription') ||
                      'Help improve the service by sharing anonymous analytics'}
                  </p>
                </div>
                <Switch
                  id="share-analytics"
                  checked={settings.share_analytics}
                  onCheckedChange={checked =>
                    setSettings({
                      ...settings,
                      share_analytics: checked,
                    })
                  }
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Action Buttons */}
      <div className="flex gap-3 justify-end mt-6">
        <Button variant="outline" onClick={handleReset} disabled={saving}>
          <RotateCcw className="w-4 h-4 mr-2" />
          {t('settings.resetToDefaults') || 'Reset to Defaults'}
        </Button>
        <Button onClick={handleSave} disabled={saving}>
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              {t('settings.saving')}
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              {t('settings.saveChanges') || 'Save Changes'}
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
