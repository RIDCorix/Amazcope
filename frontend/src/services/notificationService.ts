import apiClient from '@/lib/api';

export interface Notification {
  id: string;
  user_id: string;
  product_id: string | null;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'unread' | 'read' | 'archived' | 'deleted';
  category: string;
  action_url: string | null;
  created_at: string;
  read_at: string | null;
  updated_at: string;
}

export interface NotificationListParams {
  skip?: number;
  limit?: number;
  status?: 'unread' | 'read' | 'archived' | 'deleted';
  category?: string;
  unread_only?: boolean;
}

export interface UnreadCountResponse {
  count: number;
}

export interface MarkAllReadResponse {
  updated: number;
}

export const notificationService = {
  /**
   * Get user's notifications with optional filtering
   */
  async getNotifications(
    params?: NotificationListParams
  ): Promise<Notification[]> {
    const response = await apiClient.get('/api/v1/notifications', { params });
    return response.data;
  },

  /**
   * Get a single notification by ID
   */
  async getNotification(id: string): Promise<Notification> {
    const response = await apiClient.get(`/api/v1/notifications/${id}`);
    return response.data;
  },

  /**
   * Get count of unread notifications
   */
  async getUnreadCount(): Promise<number> {
    const response = await apiClient.get<UnreadCountResponse>(
      '/api/v1/notifications/unread-count'
    );
    return response.data.count;
  },

  /**
   * Mark a notification as read
   */
  async markAsRead(id: string): Promise<Notification> {
    const response = await apiClient.patch(`/api/v1/notifications/${id}`, {
      status: 'read',
    });
    return response.data;
  },

  /**
   * Archive a notification
   */
  async archiveNotification(id: string): Promise<Notification> {
    const response = await apiClient.patch(`/api/v1/notifications/${id}`, {
      status: 'archived',
    });
    return response.data;
  },

  /**
   * Mark all notifications as read
   */
  async markAllAsRead(): Promise<number> {
    const response = await apiClient.post<MarkAllReadResponse>(
      '/api/v1/notifications/mark-all-read'
    );
    return response.data.updated;
  },

  /**
   * Delete a notification
   */
  async deleteNotification(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/notifications/${id}`);
  },

  /**
   * Get recent notifications (last 10 unread)
   */
  async getRecentNotifications(): Promise<Notification[]> {
    return this.getNotifications({
      limit: 10,
      unread_only: true,
    });
  },
};
