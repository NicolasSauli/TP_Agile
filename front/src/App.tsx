import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute, PublicOnlyRoute } from './components';
import LoginPage from './pages/LoginPage';
import BoardPage from './pages/BoardPage';

// Composant de chargement
function LoadingScreen() {
  return (
    <div className="loading-screen">
      <div className="spinner" />
      <p>Chargement...</p>
    </div>
  );
}

// Page d'accueil qui redirige vers le board si connecté
function HomePage() {
  return <Navigate to="/board" replace />;
}

// Page 404
function NotFoundPage() {
  return (
    <main className="error-page">
      <h1>404</h1>
      <p>Page non trouvée</p>
      <a href="/">Retour à l'accueil</a>
    </main>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Route publique - Login/Signup */}
          <Route path="/login" element={
            <PublicOnlyRoute>
              <LoginPage />
            </PublicOnlyRoute>
          } />
          
          {/* Route publique - Accueil (redirige vers board si connecté) */}
          <Route path="/" element={<HomePage />} />
          
          {/* Routes protégées - Nécessitent une connexion */}
          <Route 
            path="/board" 
            element={
              <ProtectedRoute>
                <BoardPage />
              </ProtectedRoute>
            }
          />
          <Route 
            path="/chat" 
            element={
              <ProtectedRoute>
                <BoardPage />
              </ProtectedRoute>
            }
          />
          <Route 
            path="/generating" 
            element={
              <ProtectedRoute>
                <BoardPage />
              </ProtectedRoute>
            }
          />
          
          {/* 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
