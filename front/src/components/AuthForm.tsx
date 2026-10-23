import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

type AuthFormProps = {
  isSignup?: boolean;
  onSwitch: () => void;
};

function Icon({ name, size = 18 }: { name: string; size?: number }) {
  const paths: Record<string, React.ReactNode> = {
    spark: <><path d="m12 3-1.2 4.2L7 9l3.8 1.8L12 15l1.2-4.2L17 9l-3.8-1.8L12 3Z"/><path d="m5 15-.7 2.3L2 18l2.3.7L5 21l.7-2.3L8 18l-2.3-.7L5 15Z"/></>,
    send: <><path d="m22 2-7 20-4-9-9-4 20-7Z"/><path d="M22 2 11 13"/></>,
    check: <path d="m5 12 4 4L19 6"/>
    arrow: <path d="m9 18 6-6-6-6"/>
    plus: <path d="M12 5v14M5 12h14"/>
    google: <><path d="M21.4 12.2c0-.7-.1-1.4-.2-2H12v3.8h5.3a4.5 4.5 0 0 1-2 3v2.5h3.2c1.9-1.8 2.9-4.3 2.9-7.3Z"/><path d="M12 22c2.7 0 5-.9 6.6-2.4l-3.2-2.5c-.9.6-2 1-3.4 1-2.6 0-4.8-1.8-5.6-4.2H3.1v2.6A10 10 0 0 0 12 22Z"/><path d="M6.4 13.9a6 6 0 0 1 0-3.8V7.5H3.1a10 10 0 0 0 0 9l3.3-2.6Z"/><path d="M12 5.9c1.5 0 2.8.5 3.8 1.5l2.9-2.8A9.7 9.7 0 0 0 3.1 7.5l3.3 2.6C7.2 7.7 9.4 5.9 12 5.9Z"/></>,
    eye: <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>
    eyeOff: <><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}

function Brand() {
  return <div className="brand"><span className="logo"><Icon name="spark" size={18}/></span><span>Planora</span></div>;
}

interface FormErrors {
  email?: string;
  password?: string;
  username?: string;
  full_name?: string;
  confirm_password?: string;
}

export default function AuthForm({ isSignup = false, onSwitch }: AuthFormProps) {
  const { login, register, isLoading, error, clearError } = useAuth();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    confirm_password: '',
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  // Effacer l'erreur quand on change de formulaire
  useEffect(() => {
    clearError();
    setErrors({});
  }, [isSignup, clearError]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Effacer l'erreur pour ce champ
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    
    if (!formData.email) {
      newErrors.email = 'L\'adresse e-mail est requise';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Adresse e-mail invalide';
    }
    
    if (!formData.username) {
      newErrors.username = 'Le nom d\'utilisateur est requis';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Le nom d\'utilisateur doit faire au moins 3 caractères';
    }
    
    if (!formData.password) {
      newErrors.password = 'Le mot de passe est requis';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Le mot de passe doit faire au moins 8 caractères';
    }
    
    if (isSignup) {
      if (!formData.full_name) {
        newErrors.full_name = 'Le nom complet est requis';
      }
      
      if (formData.password !== formData.confirm_password) {
        newErrors.confirm_password = 'Les mots de passe ne correspondent pas';
      } else if (!formData.confirm_password) {
        newErrors.confirm_password = 'Veuillez confirmer votre mot de passe';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    const credentials = {
      username: formData.username,
      email: formData.email,
      password: formData.password,
      full_name: formData.full_name || undefined,
    };
    
    try {
      const success = isSignup 
        ? await register(credentials)
        : await login({ username: formData.username, password: formData.password });
      
      if (success) {
        // Rediriger vers le tableau Kanban après connexion
        navigate('/board');
      }
    } catch (err) {
      console.error('Erreur:', err);
    }
  };

  return (
    <main className="auth-page">
      <header>
        <Brand />
        <button className="text-button" onClick={onSwitch}>
          {isSignup ? "Se connecter" : "Créer un compte"}
        </button>
      </header>
      
      <section className="auth-card">
        <span className="auth-mark"><Icon name="spark" size={22} /></span>
        <h1>{isSignup ? "Créez votre espace projet" : "Bienvenue"}</h1>
        <p>{isSignup ? "Commencez à construire vos projets avec votre Scrum Master IA." : "Connectez-vous à votre espace projet."}</p>
        
        {error && (
          <div className="error-message">
            <Icon name="check" size={16} />
            <span>{error}</span>
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          {isSignup && (
            <label>
              Nom
              <input
                name="full_name"
                placeholder="Votre nom"
                value={formData.full_name}
                onChange={handleChange}
                required
              />
              {errors.full_name && <span className="error-text">{errors.full_name}</span>}
            </label>
          )}
          
          <label>
            Nom d'utilisateur
            <input
              name="username"
              placeholder="votre_nom"
              value={formData.username}
              onChange={handleChange}
              required
            />
            {errors.username && <span className="error-text">{errors.username}</span>}
          </label>
          
          <label>
            Adresse e-mail
            <input
              type="email"
              name="email"
              placeholder="nom@entreprise.com"
              value={formData.email}
              onChange={handleChange}
              required
            />
            {errors.email && <span className="error-text">{errors.email}</span>}
          </label>
          
          <label>
            <div className="password-header">
              <span>Mot de passe</span>
              <button
                type="button"
                className="eye-button"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <Icon name="eyeOff" size={16} /> : <Icon name="eye" size={16} />}
              </button>
            </div>
            <input
              type={showPassword ? "text" : "password"}
              name="password"
              placeholder="8 caractères minimum"
              value={formData.password}
              onChange={handleChange}
              required
            />
            {errors.password && <span className="error-text">{errors.password}</span>}
          </label>
          
          {isSignup && (
            <label>
              <div className="password-header">
                <span>Confirmation du mot de passe</span>
                <button
                  type="button"
                  className="eye-button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                >
                  {showConfirmPassword ? <Icon name="eyeOff" size={16} /> : <Icon name="eye" size={16} />}
                </button>
              </div>
              <input
                type={showConfirmPassword ? "text" : "password"}
                name="confirm_password"
                placeholder="Confirmez votre mot de passe"
                value={formData.confirm_password}
                onChange={handleChange}
                required
              />
              {errors.confirm_password && <span className="error-text">{errors.confirm_password}</span>}
            </label>
          )}
          
          {!isSignup && (
            <div className="form-row">
              <label className="checkbox">
                <input type="checkbox" />
                Se souvenir de moi
              </label>
              <button type="button" className="link-button">
                Mot de passe oublié ?
              </button>
            </div>
          )}
          
          <button 
            className="primary full" 
            type="submit" 
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="loading-spinner" />
            ) : (
              <>
                {isSignup ? "Créer mon compte" : "Se connecter"}
                <Icon name="arrow" size={16} />
              </>
            )}
          </button>
        </form>
        
        <div className="divider"><span>ou</span></div>
        <button className="google-button">
          <Icon name="google" size={18} />
          Continuer avec Google
        </button>
        
        <p className="auth-switch">
          {isSignup ? "Vous avez déjà un compte ?" : "Vous n'avez pas encore de compte ?"}{' '}
          <button onClick={onSwitch}>
            {isSignup ? "Se connecter" : "Créer un compte"}
          </button>
        </p>
      </section>
    </main>
  );
}
