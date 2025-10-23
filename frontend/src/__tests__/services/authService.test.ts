import apiClient from '@/lib/api';
import { AuthService } from '@/services/authService';
import { LoginRequest, RegisterRequest } from '@/types/api';

// Mock the apiClient
jest.mock('@/lib/api');
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('AuthService', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    // Clear localStorage
    localStorage.clear();
  });

  describe('login', () => {
    it('should login successfully and store tokens', async () => {
      const mockLoginData: LoginRequest = {
        email: 'test@example.com',
        password: 'password123',
      };

      const mockResponse = {
        data: {
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          user: {
            id: 1,
            email: 'test@example.com',
            username: 'testuser',
          },
        },
      };

      mockedApiClient.post.mockResolvedValueOnce(mockResponse);

      const result = await AuthService.login(mockLoginData);

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/v1/auth/login', {
        email_or_username: mockLoginData.email,
        password: mockLoginData.password,
      });

      expect(localStorage.getItem('authToken')).toBe('mock-access-token');
      expect(localStorage.getItem('refreshToken')).toBe('mock-refresh-token');
      expect(localStorage.getItem('user')).toBe(
        JSON.stringify(mockResponse.data.user)
      );

      expect(result).toEqual({
        token: 'mock-access-token',
        refreshToken: 'mock-refresh-token',
        user: mockResponse.data.user,
      });
    });

    it('should handle login failure', async () => {
      const mockLoginData: LoginRequest = {
        email: 'test@example.com',
        password: 'wrong-password',
      };

      mockedApiClient.post.mockRejectedValueOnce(
        new Error('Invalid credentials')
      );

      await expect(AuthService.login(mockLoginData)).rejects.toThrow(
        'Invalid credentials'
      );
    });
  });

  describe('register', () => {
    it('should register successfully and login user', async () => {
      const mockRegisterData: RegisterRequest = {
        email: 'newuser@example.com',
        username: 'newuser',
        password: 'password123',
      };

      const mockRegisterResponse = { data: { message: 'User created' } };
      const mockLoginResponse = {
        data: {
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          user: {
            id: 1,
            email: 'newuser@example.com',
            username: 'newuser',
          },
        },
      };

      mockedApiClient.post
        .mockResolvedValueOnce(mockRegisterResponse)
        .mockResolvedValueOnce(mockLoginResponse);

      const result = await AuthService.register(mockRegisterData);

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/api/v1/auth/register',
        mockRegisterData
      );
      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/v1/auth/login', {
        email_or_username: mockRegisterData.email,
        password: mockRegisterData.password,
      });

      expect(result.user.email).toBe('newuser@example.com');
    });

    it('should handle registration failure', async () => {
      const mockRegisterData: RegisterRequest = {
        email: 'existing@example.com',
        username: 'existing',
        password: 'password123',
      };

      mockedApiClient.post.mockRejectedValueOnce(
        new Error('User already exists')
      );

      await expect(AuthService.register(mockRegisterData)).rejects.toThrow(
        'User already exists'
      );
    });
  });

  describe('logout', () => {
    it('should logout successfully and clear storage', async () => {
      // Set up localStorage
      localStorage.setItem('authToken', 'mock-token');
      localStorage.setItem('refreshToken', 'mock-refresh-token');
      localStorage.setItem('user', JSON.stringify({ id: 1 }));

      mockedApiClient.post.mockResolvedValueOnce({ data: {} });

      await AuthService.logout();

      expect(mockedApiClient.post).toHaveBeenCalledWith('/api/v1/auth/logout');
      expect(localStorage.getItem('authToken')).toBeNull();
      expect(localStorage.getItem('refreshToken')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
    });

    it('should clear storage even if API call fails', async () => {
      localStorage.setItem('authToken', 'mock-token');

      mockedApiClient.post.mockRejectedValueOnce(new Error('Network error'));

      await AuthService.logout();

      expect(localStorage.getItem('authToken')).toBeNull();
    });
  });

  describe('getCurrentUser', () => {
    it('should fetch and update current user', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockUser });

      const result = await AuthService.getCurrentUser();

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/v1/auth/profile');
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockUser));
      expect(result).toEqual(mockUser);
    });

    it('should handle user fetch failure', async () => {
      mockedApiClient.get.mockRejectedValueOnce(new Error('Unauthorized'));

      await expect(AuthService.getCurrentUser()).rejects.toThrow(
        'Unauthorized'
      );
    });
  });

  describe('refreshToken', () => {
    it('should refresh access token successfully', async () => {
      localStorage.setItem('refreshToken', 'old-refresh-token');

      const mockResponse = {
        data: {
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token',
        },
      };

      mockedApiClient.post.mockResolvedValueOnce(mockResponse);

      const result = await AuthService.refreshToken();

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/api/v1/auth/refresh',
        { refresh_token: 'old-refresh-token' }
      );
      expect(localStorage.getItem('authToken')).toBe('new-access-token');
      expect(localStorage.getItem('refreshToken')).toBe('new-refresh-token');
      expect(result).toBe('new-access-token');
    });

    it('should throw error if no refresh token available', async () => {
      await expect(AuthService.refreshToken()).rejects.toThrow(
        'No refresh token available'
      );
    });
  });

  describe('isLoggedIn', () => {
    it('should return true when auth token exists', () => {
      localStorage.setItem('authToken', 'mock-token');
      expect(AuthService.isLoggedIn()).toBe(true);
    });

    it('should return false when no auth token', () => {
      expect(AuthService.isLoggedIn()).toBe(false);
    });
  });

  describe('getStoredUser', () => {
    it('should return stored user data', () => {
      const mockUser = { id: 1, email: 'test@example.com' };
      localStorage.setItem('user', JSON.stringify(mockUser));

      const result = AuthService.getStoredUser();
      expect(result).toEqual(mockUser);
    });

    it('should return null when no user stored', () => {
      expect(AuthService.getStoredUser()).toBeNull();
    });
  });
});
