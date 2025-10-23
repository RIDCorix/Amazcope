import {
  AlertTriangle,
  Archive,
  Bell,
  CheckCircle2,
  Info,
  Settings,
} from 'lucide-react';
import { useEffect, useState } from 'react';

import { NotificationList, useUnreadCount } from '@/components/notifications';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { useTranslation } from '@/hooks/useTranslation';
import {
  Notification,
  NotificationListParams,
  notificationService,
} from '@/services/notificationService';

export default function NotificationsPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('all');
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const { unreadCount, refreshCount } = useUnreadCount();
  const { toast } = useToast();

  // Notification stats
  const [stats, setStats] = useState({
    total: 0,
    unread: 0,
    read: 0,
    archived: 0,
  });

  const loadNotifications = async (status?: string) => {
    setLoading(true);
    try {
      const params: NotificationListParams = {
        limit: 50,
      };

      if (status && status !== 'all') {
        params.status = status as 'unread' | 'read' | 'archived';
      }

      const data = await notificationService.getNotifications(params);
      setNotifications(data);

      // Calculate stats
      const newStats = {
        total: data.length,
        unread: data.filter(n => n.status === 'unread').length,
        read: data.filter(n => n.status === 'read').length,
        archived: data.filter(n => n.status === 'archived').length,
      };
      setStats(newStats);
    } catch (err: any) {
      toast({
        title: t('common.error'),
        description:
          err.response?.data?.detail || t('notifications.errors.loadFailed'),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationService.markAllAsRead();
      loadNotifications(activeTab);
      refreshCount();
      toast({
        title: t('common.success'),
        description: t('notifications.success.markedAllRead'),
      });
    } catch {
      toast({
        title: t('common.error'),
        description: t('notifications.errors.markAllFailed'),
        variant: 'destructive',
      });
    }
  };

  const handleNotificationUpdate = (updatedNotifications: Notification[]) => {
    setNotifications(updatedNotifications);
    refreshCount();
  };

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    loadNotifications(value);
  };

  useEffect(() => {
    loadNotifications('all');
  }, []);

  const statCards = [
    {
      title: t('notifications.stats.total'),
      value: stats.total,
      icon: Bell,
      color: 'text-gray-600',
      bgColor: 'bg-gray-100',
    },
    {
      title: t('notifications.stats.unread'),
      value: stats.unread,
      icon: AlertTriangle,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: t('notifications.stats.read'),
      value: stats.read,
      icon: CheckCircle2,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: t('notifications.stats.archived'),
      value: stats.archived,
      icon: Archive,
      color: 'text-gray-600',
      bgColor: 'bg-gray-100',
    },
  ];

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {t('notifications.pageTitle')}
          </h1>
          <p className="text-gray-600 mt-1">
            {t('notifications.pageDescription')}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={handleMarkAllAsRead}
            disabled={loading || stats.unread === 0}
          >
            <CheckCircle2 className="mr-2 h-4 w-4" />
            {t('notifications.markAllRead')}
          </Button>

          <Button
            variant="outline"
            onClick={() => (window.location.href = '/settings/notifications')}
          >
            <Settings className="mr-2 h-4 w-4" />
            {t('notifications.settings')}
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(stat => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title} className="relative overflow-hidden">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  {stat.title}
                </CardTitle>
                <div className={`p-2 rounded-full ${stat.bgColor}`}>
                  <Icon className={`h-4 w-4 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">
                  {stat.title === t('notifications.stats.unread') &&
                  stat.value > 0
                    ? t('notifications.stats.requiresAttention')
                    : stat.title === t('notifications.stats.total') &&
                        stat.value === 0
                      ? t('notifications.stats.noNotificationsYet')
                      : t('notifications.stats.allCaughtUp')}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Quick Stats Alert */}
      {stats.unread > 5 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-full">
              <Info className="h-5 w-5 text-blue-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-medium text-blue-900">
                {t('notifications.alerts.manyUnread', {
                  count: stats.unread,
                })}
              </h3>
              <p className="text-sm text-blue-700">
                {t('notifications.alerts.considerMarking')}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleMarkAllAsRead}
              className="border-blue-300 text-blue-700 hover:bg-blue-100"
            >
              {t('notifications.markAllRead')}
            </Button>
          </div>
        </div>
      )}

      {/* Notifications */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                {t('notifications.allNotifications')}
                {unreadCount > 0 && (
                  <Badge
                    variant="secondary"
                    className="bg-blue-100 text-blue-800"
                  >
                    {t('notifications.unreadCount', { count: unreadCount })}
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                {t('notifications.viewAndManage')}
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <Tabs
            value={activeTab}
            onValueChange={handleTabChange}
            className="w-full"
          >
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="all" className="flex items-center gap-2">
                {t('notifications.tabs.all')}
                {stats.total > 0 && (
                  <Badge variant="secondary" className="ml-1">
                    {stats.total}
                  </Badge>
                )}
              </TabsTrigger>

              <TabsTrigger value="unread" className="flex items-center gap-2">
                {t('notifications.tabs.unread')}
                {stats.unread > 0 && (
                  <Badge
                    variant="secondary"
                    className="ml-1 bg-blue-100 text-blue-800"
                  >
                    {stats.unread}
                  </Badge>
                )}
              </TabsTrigger>

              <TabsTrigger value="read" className="flex items-center gap-2">
                {t('notifications.tabs.read')}
                {stats.read > 0 && (
                  <Badge variant="secondary" className="ml-1">
                    {stats.read}
                  </Badge>
                )}
              </TabsTrigger>

              <TabsTrigger value="archived" className="flex items-center gap-2">
                {t('notifications.tabs.archived')}
                {stats.archived > 0 && (
                  <Badge variant="secondary" className="ml-1">
                    {stats.archived}
                  </Badge>
                )}
              </TabsTrigger>
            </TabsList>

            <div className="mt-6">
              <TabsContent value="all" className="mt-0">
                <NotificationList
                  initialNotifications={notifications}
                  showFilters={true}
                  maxHeight="max-h-none"
                  onNotificationUpdate={handleNotificationUpdate}
                />
              </TabsContent>

              <TabsContent value="unread" className="mt-0">
                <NotificationList
                  initialNotifications={notifications.filter(
                    n => n.status === 'unread'
                  )}
                  showFilters={true}
                  maxHeight="max-h-none"
                  onNotificationUpdate={handleNotificationUpdate}
                />
              </TabsContent>

              <TabsContent value="read" className="mt-0">
                <NotificationList
                  initialNotifications={notifications.filter(
                    n => n.status === 'read'
                  )}
                  showFilters={true}
                  maxHeight="max-h-none"
                  onNotificationUpdate={handleNotificationUpdate}
                />
              </TabsContent>

              <TabsContent value="archived" className="mt-0">
                <NotificationList
                  initialNotifications={notifications.filter(
                    n => n.status === 'archived'
                  )}
                  showFilters={true}
                  maxHeight="max-h-none"
                  onNotificationUpdate={handleNotificationUpdate}
                />
              </TabsContent>
            </div>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
