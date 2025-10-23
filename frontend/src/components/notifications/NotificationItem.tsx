import { formatDistanceToNow } from 'date-fns';
import {
  AlertCircle,
  AlertTriangle,
  Archive,
  CheckCircle,
  ExternalLink,
  Eye,
  Info,
  MoreVertical,
  Trash2,
} from 'lucide-react';

import { DailyReportNotification } from './DailyReportNotification';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { Notification } from '@/services/notificationService';

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead?: (id: string) => void;
  onArchive?: (id: string) => void;
  onDelete?: (id: string) => void;
  onActionClick?: (url: string) => void;
  className?: string;
}

const typeIcons = {
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
  error: AlertCircle,
};

const typeColors = {
  info: 'text-blue-500',
  success: 'text-green-500',
  warning: 'text-yellow-500',
  error: 'text-red-500',
};

const priorityColors = {
  low: 'border-gray-200',
  medium: 'border-blue-200',
  high: 'border-orange-200',
  urgent: 'border-red-200',
};

const priorityBadgeColors = {
  low: 'bg-gray-100 text-gray-800',
  medium: 'bg-blue-100 text-blue-800',
  high: 'bg-orange-100 text-orange-800',
  urgent: 'bg-red-100 text-red-800',
};

export function NotificationItem({
  notification,
  onMarkAsRead,
  onArchive,
  onDelete,
  onActionClick,
  className,
}: NotificationItemProps) {
  const IconComponent = typeIcons[notification.type];
  const isUnread = notification.status === 'unread';

  const handleMarkAsRead = () => {
    if (onMarkAsRead && isUnread) {
      onMarkAsRead(notification.id);
    }
  };

  const handleArchive = () => {
    if (onArchive) {
      onArchive(notification.id);
    }
  };

  const handleDelete = () => {
    if (onDelete) {
      onDelete(notification.id);
    }
  };

  const handleActionClick = () => {
    if (notification.action_url && onActionClick) {
      onActionClick(notification.action_url);
    }
  };

  const formatTimeAgo = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return 'Unknown time';
    }
  };

  // Use specialized component for daily reports
  if (
    notification.category === 'daily_report' ||
    notification.title.toLowerCase().includes('daily report')
  ) {
    return (
      <DailyReportNotification
        notification={notification}
        onMarkAsRead={onMarkAsRead}
        className={className}
      />
    );
  }

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 border-l-4 transition-all duration-200',
        priorityColors[notification.priority],
        isUnread
          ? 'bg-blue-50/50 hover:bg-blue-50'
          : 'bg-white hover:bg-gray-50',
        'border-b border-gray-100',
        className
      )}
    >
      {/* Status indicator dot */}
      {isUnread && (
        <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2" />
      )}

      {/* Icon */}
      <div className="flex-shrink-0">
        <div
          className={cn(
            'flex items-center justify-center w-8 h-8 rounded-full',
            isUnread ? 'bg-white border-2 border-gray-200' : 'bg-gray-100'
          )}
        >
          <IconComponent
            className={cn('w-4 h-4', typeColors[notification.type])}
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-grow min-w-0">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h4
              className={cn(
                'text-sm font-medium text-gray-900 truncate',
                isUnread && 'font-semibold'
              )}
            >
              {notification.title}
            </h4>

            {/* Priority badge */}
            {notification.priority !== 'low' && (
              <Badge
                variant="secondary"
                className={cn(
                  'text-xs',
                  priorityBadgeColors[notification.priority]
                )}
              >
                {notification.priority.toUpperCase()}
              </Badge>
            )}
          </div>

          {/* Actions menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                <MoreVertical className="h-3 w-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {isUnread && (
                <DropdownMenuItem onClick={handleMarkAsRead}>
                  <Eye className="mr-2 h-4 w-4" />
                  Mark as read
                </DropdownMenuItem>
              )}

              <DropdownMenuItem onClick={handleArchive}>
                <Archive className="mr-2 h-4 w-4" />
                Archive
              </DropdownMenuItem>

              <DropdownMenuItem
                onClick={handleDelete}
                className="text-red-600 focus:text-red-600"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Message */}
        <p className="text-sm text-gray-600 mb-2 line-clamp-2">
          {notification.message}
        </p>

        {/* Footer */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-xs text-gray-500">
            <span>{formatTimeAgo(notification.created_at)}</span>

            {notification.category && (
              <>
                <span>•</span>
                <span className="capitalize">{notification.category}</span>
              </>
            )}
          </div>

          {/* Action button */}
          {notification.action_url && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 px-2 text-xs text-blue-600 hover:text-blue-700"
              onClick={handleActionClick}
            >
              View
              <ExternalLink className="ml-1 h-3 w-3" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
