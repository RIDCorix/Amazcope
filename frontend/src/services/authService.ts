import apiClient from '@/lib/api';
import { AuthResponse, LoginRequest, RegisterRequest } from '@/types/api';

export class AuthService {
  // Login user
  static async login(credentials: LoginRequest): Promise<AuthResponse> {
    // Use FastAPI token endpoint
    const response = await apiClient.post('/api/v1/auth/login', {
      email_or_username: credentials.email, // Backend expects email_or_username field
      password: credentials.password,
    });

    const tokenData = response.data;

    // Store token in localStorage (backend returns access_token and refresh_token)
    if (typeof window !== 'undefined' && tokenData.access_token) {
      localStorage.setItem('authToken', tokenData.access_token);
      localStorage.setItem('refreshToken', tokenData.refresh_token);
    }

    // User data is included in the login response
    const authData: AuthResponse = {
      token: tokenData.access_token,
      refreshToken: tokenData.refresh_token,
      user: tokenData.user,
    };

    // Store user data
    if (typeof window !== 'undefined') {
      localStorage.setItem('user', JSON.stringify(authData.user));
    }

    return authData;
  }

  // Register user
  static async register(userData: RegisterRequest): Promise<AuthResponse> {
    await apiClient.post('/api/v1/auth/register', userData);

    // After registration, log the user in
    return this.login({
      email: userData.email,
      password: userData.password,
    });
  }

  // Logout user
  static async logout(): Promise<void> {
    try {
      // Call logout endpoint (for any server-side cleanup)
      await apiClient.post('/api/v1/auth/logout');
    } catch (error) {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed:', error);
    } finally {
      // Clear local storage
      if (typeof window !== 'undefined') {
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
      }
    }
  }

  // Get current user
  static async getCurrentUser(): Promise<AuthResponse['user']> {
    const response = await apiClient.get('/api/v1/auth/profile');
    const userData = response.data;

    // Update stored user data
    if (typeof window !== 'undefined') {
      localStorage.setItem('user', JSON.stringify(userData));
    }

    return userData;
  }

  // Refresh access token
  static async refreshToken(): Promise<string> {
    const refreshToken =
      typeof window !== 'undefined'
        ? localStorage.getItem('refreshToken')
        : null;
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await apiClient.post('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });

    const tokenData = response.data;
    const newAccessToken = tokenData.access_token;
    const newRefreshToken = tokenData.refresh_token;

    if (typeof window !== 'undefined') {
      localStorage.setItem('authToken', newAccessToken);
      localStorage.setItem('refreshToken', newRefreshToken);
    }

    return newAccessToken;
  }

  // Check if user is logged in
  static isLoggedIn(): boolean {
    if (typeof window === 'undefined') return false;
    return !!localStorage.getItem('authToken');
  }

  // Get stored user data
  static getStoredUser(): AuthResponse['user'] | null {
    if (typeof window === 'undefined') return null;
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }
}

// Export an instance for easy use
export const authService = AuthService;
