import { CheckCircle2, RefreshCw, Search } from 'lucide-react';
import { useEffect, useState } from 'react';

import { NotificationItem } from './NotificationItem';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { useTranslation } from '@/hooks/useTranslation';
import { cn } from '@/lib/utils';
import {
  Notification,
  NotificationListParams,
  notificationService,
} from '@/services/notificationService';

interface NotificationListProps {
  initialNotifications?: Notification[];
  showFilters?: boolean;
  maxHeight?: string;
  onNotificationUpdate?: (notifications: Notification[]) => void;
  className?: string;
}

export function NotificationList({
  initialNotifications = [],
  showFilters = true,
  maxHeight = 'max-h-96',
  onNotificationUpdate,
  className,
}: NotificationListProps) {
  const { t } = useTranslation();
  const [notifications, setNotifications] =
    useState<Notification[]>(initialNotifications);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedNotifications, setSelectedNotifications] = useState<string[]>(
    []
  );
  const { toast } = useToast();

  // Extract unique categories from notifications
  const categories = Array.from(
    new Set(notifications.map(n => n.category).filter(Boolean))
  );

  // Filter notifications based on search and filters
  const filteredNotifications = notifications.filter(notification => {
    const matchesSearch =
      searchQuery === '' ||
      notification.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      notification.message.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus =
      selectedStatus === 'all' || notification.status === selectedStatus;

    const matchesCategory =
      selectedCategory === 'all' || notification.category === selectedCategory;

    return matchesSearch && matchesStatus && matchesCategory;
  });

  // Load notifications
  const loadNotifications = async (params?: NotificationListParams) => {
    setLoading(true);
    try {
      const data = await notificationService.getNotifications(params);
      setNotifications(data);
      onNotificationUpdate?.(data);
    } catch (error) {
      console.error('Failed to load notifications:', error);
      toast({
        title: t('common.error'),
        description: t('notifications.errors.loadFailed'),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Handle mark as read
  const handleMarkAsRead = async (id: string) => {
    try {
      await notificationService.markAsRead(id);
      setNotifications(prev =>
        prev.map(n =>
          n.id === id
            ? {
                ...n,
                status: 'read' as const,
                read_at: new Date().toISOString(),
              }
            : n
        )
      );
      toast({
        title: t('common.success'),
        description: t('notifications.success.markedAsRead'),
      });
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      toast({
        title: t('common.error'),
        description: t('notifications.errors.markAsReadFailed'),
        variant: 'destructive',
      });
    }
  };

  // Handle archive
  const handleArchive = async (id: string) => {
    try {
      await notificationService.archiveNotification(id);
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, status: 'archived' as const } : n))
      );
      toast({
        title: t('common.success'),
        description: t('notifications.success.archived'),
      });
    } catch (error) {
      console.error('Failed to archive notification:', error);
      toast({
        title: t('common.error'),
        description: t('notifications.errors.archiveFailed'),
        variant: 'destructive',
      });
    }
  };

  // Handle delete
  const handleDelete = async (id: string) => {
    try {
      await notificationService.deleteNotification(id);
      setNotifications(prev => prev.filter(n => n.id !== id));
      toast({
        title: t('common.success'),
        description: t('notifications.success.deleted'),
      });
    } catch (err) {
      console.error('Failed to delete notification:', err);
      toast({
        title: t('common.error'),
        description: t('notifications.errors.deleteFailed'),
        variant: 'destructive',
      });
    }
  };

  // Handle action click
  const handleActionClick = (url: string) => {
    if (url.startsWith('http')) {
      window.open(url, '_blank');
    } else {
      window.location.href = url;
    }
  };

  // Handle bulk mark as read
  const handleMarkAllAsRead = async () => {
    if (selectedNotifications.length === 0) {
      try {
        await notificationService.markAllAsRead();
        setNotifications(prev =>
          prev.map(n =>
            n.status === 'unread'
              ? {
                  ...n,
                  status: 'read' as const,
                  read_at: new Date().toISOString(),
                }
              : n
          )
        );
        toast({
          title: t('common.success'),
          description: t('notifications.success.markedAllRead'),
        });
      } catch (error) {
        toast({
          title: t('common.error'),
          description: t('notifications.errors.markAllFailed'),
          variant: 'destructive',
        });
      }
    } else {
      // Mark selected as read
      try {
        await Promise.all(
          selectedNotifications.map(id => notificationService.markAsRead(id))
        );
        setNotifications(prev =>
          prev.map(n =>
            selectedNotifications.includes(n.id)
              ? {
                  ...n,
                  status: 'read' as const,
                  read_at: new Date().toISOString(),
                }
              : n
          )
        );
        setSelectedNotifications([]);
        toast({
          title: t('common.success'),
          description: t('notifications.success.markedSelectedRead', {
            count: selectedNotifications.length,
          }),
        });
      } catch (error) {
        toast({
          title: t('common.error'),
          description: t('notifications.errors.markSelectedFailed'),
          variant: 'destructive',
        });
      }
    }
  };

  // Load notifications on mount
  useEffect(() => {
    if (initialNotifications.length === 0) {
      loadNotifications();
    }
  }, []);

  // Get unread count
  const unreadCount = filteredNotifications.filter(
    n => n.status === 'unread'
  ).length;

  return (
    <div className={cn('flex flex-col space-y-4', className)}>
      {/* Filters */}
      {showFilters && (
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder={t('notifications.searchPlaceholder')}
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Status filter */}
          <Select
            value={selectedStatus}
            onChange={e => setSelectedStatus(e.target.value)}
            className="w-32"
          >
            <option value="all">{t('notifications.allStatus')}</option>
            <option value="unread">{t('notifications.tabs.unread')}</option>
            <option value="read">{t('notifications.tabs.read')}</option>
            <option value="archived">{t('notifications.tabs.archived')}</option>
          </Select>

          {/* Category filter */}
          <Select
            value={selectedCategory}
            onChange={e => setSelectedCategory(e.target.value)}
            className="w-36"
          >
            <option value="all">{t('notifications.allCategories')}</option>
            {categories.map(category => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </Select>

          {/* Actions */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleMarkAllAsRead}
              disabled={loading}
            >
              <CheckCircle2 className="mr-2 h-4 w-4" />
              {selectedNotifications.length > 0
                ? t('notifications.markSelected')
                : t('notifications.markAll')}{' '}
              {t('notifications.read')}
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => loadNotifications()}
              disabled={loading}
            >
              <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
            </Button>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>
            {t('notifications.notificationsCount', {
              count: filteredNotifications.length,
            })}
          </span>
          {unreadCount > 0 && (
            <Badge variant="secondary" className="bg-blue-100 text-blue-800">
              {t('notifications.unreadCount', { count: unreadCount })}
            </Badge>
          )}
        </div>
      </div>

      {/* Notifications list */}
      <div
        className={cn(
          'border rounded-lg overflow-hidden',
          maxHeight,
          'overflow-y-auto'
        )}
      >
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
            <span className="ml-2 text-gray-600">
              {t('notifications.loading')}
            </span>
          </div>
        ) : filteredNotifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-gray-500">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle2 className="h-8 w-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium mb-2">
              {t('notifications.noNotificationsFound')}
            </h3>
            <p className="text-sm text-center max-w-sm">
              {searchQuery ||
              selectedStatus !== 'all' ||
              selectedCategory !== 'all'
                ? t('notifications.adjustFilters')
                : t('notifications.allCaughtUpMessage')}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filteredNotifications.map(notification => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                onMarkAsRead={handleMarkAsRead}
                onArchive={handleArchive}
                onDelete={handleDelete}
                onActionClick={handleActionClick}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
