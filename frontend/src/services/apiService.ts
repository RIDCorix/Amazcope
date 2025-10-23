import { AuthService } from './authService';

// Unified API service that switches between mock and real API
export class ApiService {
  static auth = AuthService;
}

export const apiServices = {
  auth: AuthService,
};

// Default export
export default ApiService;
