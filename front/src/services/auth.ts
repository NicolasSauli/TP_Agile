import api, { API_URLS } from './api';

// Types pour les données d'authentification
interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

interface LoginCredentials {
  username: string;
  password: string;
}

interface RegisterCredentials {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

interface AuthResponse {
  user: User;
  token: {
    access_token: string;
    token_type: string;
  };
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

// Service d'authentification
export const authService = {
  // Inscription d'un nouvel utilisateur
  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>(API_URLS.auth.register, credentials);
    return response.data;
  },

  // Connexion avec form-data (comme dans Swagger)
  async loginWithForm(credentials: LoginCredentials): Promise<AuthResponse> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await api.post<AuthResponse>(API_URLS.auth.login, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  // Connexion avec JSON
  async loginWithJson(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>(`${API_URLS.auth.login}/json`, credentials);
    return response.data;
  },

  // Déconnexion
  async logout(): Promise<void> {
    await api.post(API_URLS.auth.logout);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  },

  // Rafraîchir le token
  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>(API_URLS.auth.refresh, {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  // Obtenir les informations de l'utilisateur connecté
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>(API_URLS.auth.me);
    return response.data;
  },

  // Stocker les informations de connexion
  saveAuthData(authResponse: AuthResponse): void {
    localStorage.setItem('access_token', authResponse.token.access_token);
    localStorage.setItem('user', JSON.stringify(authResponse.user));
  },

  // Effacer les informations de connexion
  clearAuthData(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },

  // Vérifier si l'utilisateur est connecté
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },

  // Obtenir l'utilisateur depuis le stockage local
  getStoredUser(): User | null {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  // Obtenir le token
  getToken(): string | null {
    return localStorage.getItem('access_token');
  },
};

export type { User, LoginCredentials, RegisterCredentials, AuthResponse };
