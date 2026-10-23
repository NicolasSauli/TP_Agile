import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

/**
 * Hook pour rediriger les utilisateurs non authentifiés
 */
export function useAuthRedirect(to: string = '/login') {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate(to, { state: { from: location }, replace: true });
    }
  }, [isAuthenticated, isLoading, navigate, to, location]);
}

/**
 * Hook pour rediriger les utilisateurs déjà authentifiés
 */
export function useAlreadyAuthenticatedRedirect(to: string = '/') {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      const from = (location.state as { from?: { pathname: string } })?.from?.pathname || to;
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate, to, location]);
}
