import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthForm from '../components/AuthForm';

export default function LoginPage() {
  const [isSignup, setIsSignup] = useState(false);
  const navigate = useNavigate();

  // Pour l'instant, on garde la navigation locale
  // plus tard on peut rediriger vers /signup si besoin
  const handleSwitch = () => {
    setIsSignup(!isSignup);
  };

  return (
    <AuthForm 
      isSignup={isSignup} 
      onSwitch={handleSwitch} 
    />
  );
}
