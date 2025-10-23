import { Bell, CheckCircle2, ExternalLink, RefreshCw } from 'lucide-react';
import React, { useEffect, useState } from 'react';

import { NotificationList } from './NotificationList';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { useToast } from '@/components/ui/use-toast';
import { cn } from '@/lib/utils';
import {
  Notification,
  notificationService,
} from '@/services/notificationService';

interface NotificationCenterProps {
  className?: string;
  variant?: 'popover' | 'modal';
  trigger?: React.ReactNode;
  onNotificationClick?: (notification: Notification) => void;
}

export function NotificationCenter({
  variant = 'popover',
  trigger,
}: NotificationCenterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  // Load recent notifications and unread count
  const loadData = async () => {
    setLoading(true);
    try {
      const [notificationsData, unreadCountData] = await Promise.all([
        notificationService.getRecentNotifications(),
        notificationService.getUnreadCount(),
      ]);
      setNotifications(notificationsData);
      setUnreadCount(unreadCountData);
    } catch (error) {
      console.error('Failed to load notification data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load notifications',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Handle notification update
  const handleNotificationUpdate = (updatedNotifications: Notification[]) => {
    setNotifications(updatedNotifications);
    const newUnreadCount = updatedNotifications.filter(
      n => n.status === 'unread'
    ).length;
    setUnreadCount(newUnreadCount);
  };

  // Handle view all notifications
  const handleViewAll = () => {
    setIsOpen(false);
    window.location.href = '/notifications';
  };

  // Handle mark all as read
  const handleMarkAllAsRead = async () => {
    try {
      await notificationService.markAllAsRead();
      setUnreadCount(0);
      setNotifications(prev =>
        prev.map(n => ({
          ...n,
          status: 'read' as const,
          read_at: new Date().toISOString(),
        }))
      );
      toast({
        title: 'Success',
        description: 'All notifications marked as read',
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to load notifications',
        variant: 'destructive',
      });
    }
  };

  // Load data when component opens
  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  // Poll for new notifications every 30 seconds when open
  useEffect(() => {
    if (!isOpen) return;

    const interval = setInterval(() => {
      loadData();
    }, 30000);

    return () => clearInterval(interval);
  }, [isOpen]);

  const defaultTrigger = (
    <Button variant="ghost" size="icon" className="relative">
      <Bell className="h-5 w-5" />
      {unreadCount > 0 && (
        <Badge
          variant="destructive"
          className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
        >
          {unreadCount > 99 ? '99+' : unreadCount}
        </Badge>
      )}
    </Button>
  );

  const content = (
    <div className="w-96 max-w-sm">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2">
          <Bell className="h-5 w-5" />
          <h3 className="font-semibold">Notifications</h3>
          {unreadCount > 0 && (
            <Badge variant="secondary" className="bg-blue-100 text-blue-800">
              {unreadCount} unread
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={loadData}
            disabled={loading}
          >
            <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
          </Button>

          {unreadCount > 0 && (
            <Button variant="ghost" size="sm" onClick={handleMarkAllAsRead}>
              <CheckCircle2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Notifications */}
      <div className="max-h-96 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
            <span className="ml-2 text-gray-600">Loading...</span>
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-gray-500">
            <Bell className="h-12 w-12 text-gray-300 mb-3" />
            <p className="text-sm text-center">
              No new notifications.
              <br />
              You're all caught up!
            </p>
          </div>
        ) : (
          <NotificationList
            initialNotifications={notifications}
            showFilters={false}
            maxHeight="max-h-none"
            onNotificationUpdate={handleNotificationUpdate}
            className="border-none"
          />
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between p-4 border-t bg-gray-50">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleViewAll}
          className="flex items-center gap-2"
        >
          View all notifications
          <ExternalLink className="h-3 w-3" />
        </Button>
      </div>
    </div>
  );

  if (variant === 'modal') {
    return (
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogTrigger asChild>{trigger || defaultTrigger}</DialogTrigger>
        <DialogContent className="max-w-md p-0">
          <DialogHeader className="sr-only">
            <DialogTitle>Notification Center</DialogTitle>
          </DialogHeader>
          {content}
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>{trigger || defaultTrigger}</PopoverTrigger>
      <PopoverContent align="end" className="p-0 w-auto" sideOffset={8}>
        {content}
      </PopoverContent>
    </Popover>
  );
}

// Hook for getting unread count (for use in other components)
export function useUnreadCount() {
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const refreshCount = async () => {
    try {
      const count = await notificationService.getUnreadCount();
      setUnreadCount(count);
    } catch (error) {
      console.error('Failed to get unread count:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshCount();

    // Refresh count every 2 minutes
    const interval = setInterval(refreshCount, 120000);

    return () => clearInterval(interval);
  }, []);

  return { unreadCount, loading, refreshCount };
}
