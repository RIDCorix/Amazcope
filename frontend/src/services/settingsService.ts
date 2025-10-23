import apiClient from '@/lib/api';

export interface UserSettings {
  id: string;
  user_id: string;

  // Notification Settings
  email_notifications_enabled: boolean;
  price_alert_emails: boolean;
  bsr_alert_emails: boolean;
  stock_alert_emails: boolean;
  daily_summary_emails: boolean;
  weekly_report_emails: boolean;

  // Alert Thresholds
  default_price_threshold: number;
  default_bsr_threshold: number;

  // Display Preferences
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  date_format: string;
  currency_display: string;

  // Dashboard Preferences
  products_per_page: number;
  default_sort_by: string;
  default_sort_order: 'asc' | 'desc';
  show_inactive_products: boolean;

  // Data Refresh Settings
  auto_refresh_dashboard: boolean;
  refresh_interval_minutes: number;

  // Privacy Settings
  share_analytics: boolean;

  created_at: string;
  updated_at: string;
}

export interface UserSettingsUpdate {
  // Notification Settings
  email_notifications_enabled?: boolean;
  price_alert_emails?: boolean;
  bsr_alert_emails?: boolean;
  stock_alert_emails?: boolean;
  daily_summary_emails?: boolean;
  weekly_report_emails?: boolean;

  // Alert Thresholds
  default_price_threshold?: number;
  default_bsr_threshold?: number;

  // Display Preferences
  theme?: 'light' | 'dark' | 'auto';
  language?: string;
  timezone?: string;
  date_format?: string;
  currency_display?: string;

  // Dashboard Preferences
  products_per_page?: number;
  default_sort_by?: string;
  default_sort_order?: 'asc' | 'desc';
  show_inactive_products?: boolean;

  // Data Refresh Settings
  auto_refresh_dashboard?: boolean;
  refresh_interval_minutes?: number;

  // Privacy Settings
  share_analytics?: boolean;
}

export const settingsService = {
  /**
   * Get current user's settings
   */
  async getSettings(): Promise<UserSettings> {
    const response = await apiClient.get('/api/v1/user/settings');
    return response.data;
  },

  /**
   * Update user settings
   */
  async updateSettings(settings: UserSettingsUpdate): Promise<UserSettings> {
    const response = await apiClient.patch('/api/v1/user/settings', settings);
    return response.data;
  },

  /**
   * Reset settings to defaults
   */
  async resetSettings(): Promise<UserSettings> {
    const response = await apiClient.post('/api/v1/user/settings/reset');
    return response.data;
  },
};
