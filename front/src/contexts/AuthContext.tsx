import React, { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { authService, type User, type LoginCredentials, type RegisterCredentials, type AuthResponse } from '../services/auth';

// Types pour le contexte
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<boolean>;
  register: (credentials: RegisterCredentials) => Promise<boolean>;
  logout: () => Promise<void>;
  clearError: () => void;
}

// Contexte par défaut
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Fournisseur du contexte
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Charger l'utilisateur au démarrage
  useEffect(() => {
    const loadUser = async () => {
      try {
        if (authService.isAuthenticated()) {
          const storedUser = authService.getStoredUser();
          if (storedUser) {
            setUser(storedUser);
            setIsAuthenticated(true);
            
            // Vérifier que le token est toujours valide
            try {
              const currentUser = await authService.getCurrentUser();
              setUser(currentUser);
            } catch (err) {
              // Token expiré, déconnecter
              authService.clearAuthData();
              setIsAuthenticated(false);
              setUser(null);
            }
          }
        }
      } catch (err) {
        console.error('Erreur de chargement utilisateur:', err);
        authService.clearAuthData();
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, []);

  // Fonction de connexion
  const login = useCallback(async (credentials: LoginCredentials): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const authResponse: AuthResponse = await authService.loginWithJson(credentials);
      authService.saveAuthData(authResponse);
      setUser(authResponse.user);
      setIsAuthenticated(true);
      setIsLoading(false);
      return true;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 
                           err.response?.data?.message ||
                           err.message || 
                           'Erreur de connexion';
      setError(errorMessage);
      setIsLoading(false);
      authService.clearAuthData();
      return false;
    }
  }, []);

  // Fonction d'inscription
  const register = useCallback(async (credentials: RegisterCredentials): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const authResponse: AuthResponse = await authService.register(credentials);
      authService.saveAuthData(authResponse);
      setUser(authResponse.user);
      setIsAuthenticated(true);
      setIsLoading(false);
      return true;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 
                           err.response?.data?.message ||
                           err.message || 
                           'Erreur d\'inscription';
      setError(errorMessage);
      setIsLoading(false);
      authService.clearAuthData();
      return false;
    }
  }, []);

  // Fonction de déconnexion
  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch (err) {
      console.error('Erreur lors de la déconnexion:', err);
    } finally {
      authService.clearAuthData();
      setUser(null);
      setIsAuthenticated(false);
    }
  }, []);

  // Effacer l'erreur
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    register,
    logout,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook personnalisé pour utiliser le contexte
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth doit être utilisé dans un AuthProvider');
  }
  return context;
}
