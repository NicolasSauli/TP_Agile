# TP_Agile Auth Service

Système d'authentification pour le projet TP_Agile avec FastAPI, JWT et SQLite.

## Structure du projet

```
backend/
├── auth/
│   ├── __init__.py
│   ├── models.py         # Modèles Pydantic
│   ├── database.py       # Base de données SQLite
│   ├── hash.py           # Hachage des mots de passe
│   ├── service.py        # Logique métier
│   ├── dependencies.py   # Dépendances FastAPI
│   └── router.py         # Routes API
├── main.py               # Application FastAPI
├── requirements.txt      # Dépendances Python
├── .env.example          # Variables d'environnement
├── .env                  # (à créer) Variables locales
└── tests/
    ├── __init__.py
    └── test_auth.py       # Tests unitaires
```

## Installation

### 1. Cloner le projet

```bash
cd C:/Users/nicol/Downloads/Projet_diego/TP_Agile
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
```

### 3. Activer l'environnement

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Installer les dépendances

```bash
pip install -r backend/requirements.txt
```

### 5. Configurer les variables d'environnement

Copier `.env.example` vers `.env` et modifier les valeurs :

```bash
cp backend/.env.example backend/.env
```

Puis éditer `backend/.env` et générer une clé secrète :

```bash
# Générer une clé secrète (Linux/Mac)
openssl rand -hex 32

# Ou utiliser Python
python -c "import secrets; print(secrets.token_hex(32))"
```

## Lancement du serveur

### Développement

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Production

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

Le serveur sera accessible à : `http://localhost:8000`

## API Documentation

Une fois le serveur lancé, la documentation interactive est disponible à :

- **Swagger UI** : `http://localhost:8000/docs`
- **ReDoc** : `http://localhost:8000/redoc`

## Endpoints disponibles

### Authentification

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/auth/register` | Inscription d'un nouvel utilisateur |
| POST | `/api/auth/login` | Connexion (form-data) |
| POST | `/api/auth/login/json` | Connexion (JSON) |
| POST | `/api/auth/logout` | Déconnexion |
| POST | `/api/auth/refresh` | Rafraîchir le token |
| GET | `/api/auth/me` | Informations de l'utilisateur connecté |

### Gestion des utilisateurs (Superuser requis)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/auth/users` | Lister tous les utilisateurs |
| GET | `/api/auth/users/{id}` | Obtenir un utilisateur |
| PATCH | `/api/auth/users/{id}` | Mettre à jour un utilisateur |
| POST | `/api/auth/users/{id}/change-password` | Changer le mot de passe |
| DELETE | `/api/auth/users/{id}` | Supprimer un utilisateur |

### Endpoints protégés

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/protected/` | Endpoint protégé (auth requis) |
| GET | `/api/protected/admin` | Endpoint admin (superuser requis) |

### Autres

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | Page d'accueil |
| GET | `/health` | Vérification de santé |

## Exemples d'utilisation

### 1. Inscription

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123",
    "full_name": "John Doe"
  }'
```

### 2. Connexion

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=johndoe&password=securepassword123"
```

Réponse :
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2026-10-23T10:00:00"
  },
  "token": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

### 3. Accéder à un endpoint protégé

```bash
curl -X GET "http://localhost:8000/api/protected/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 4. Déconnexion

```bash
curl -X POST "http://localhost:8000/api/auth/logout" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 5. Rafraîchir le token

```bash
curl -X POST "http://localhost:8000/api/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your_refresh_token_here"}'
```

## Configuration de la base de données

La base de données SQLite est automatiquement initialisée au premier lancement.
Les fichiers de la base de données sont stockés dans :

```
backend/data/auth.db
```

### Réinitialiser la base de données

Pour réinitialiser complètement la base de données (attention : toutes les données seront supprimées) :

```python
from backend.auth.database import reset_db
reset_db()
```

## Sécurité

### Bonnes pratiques

1. **Toujours** changer la clé secrète (`SECRET_KEY`) en production
2. Utiliser HTTPS en production
3. Ne pas exposer les endpoints d'authentification sans protection
4. Limiter les origines CORS en production
5. Stocker les mots de passe avec un hachage sécurisé (bcrypt)
6. Utiliser des tokens JWT avec expiration

### Configuration recommandée pour la production

```env
# .env
APP_NAME="TP_Agile Auth Service"
APP_VERSION="1.0.0"
DEBUG=False

SECRET_KEY="votre_clé_sécrète_ chrétée_ici"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

CORS_ORIGINS="https://votredomaine.com"
```

## Tests

### Lancer les tests

```bash
cd backend
python -m pytest tests/test_auth.py -v
```

### Tests disponibles

- Tests de hachage des mots de passe
- Tests d'inscription
- Tests de connexion
- Tests des endpoints protégés
- Tests de gestion des utilisateurs
- Tests de déconnexion

## Intégration avec le frontend

### Configuration CORS

Le service est configuré pour accepter toutes les origines en développement.
En production, configurez les origines autorisées dans `.env` :

```env
CORS_ORIGINS="http://localhost:3000,https://votre-frontend.com"
```

### Exemple de code frontend (React)

```javascript
// Connexion
const login = async (username, password) => {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      username: username,
      password: password
    })
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.token.access_token);
  return data.user;
};

// Accéder à un endpoint protégé
const fetchProtectedData = async () => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('http://localhost:8000/api/protected/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};
```

### Exemple avec Axios

```javascript
import axios from 'axios';

// Configuration de base
axios.defaults.baseURL = 'http://localhost:8000/api/auth';

// Intercepteur pour ajouter le token
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Connexion
export const login = async (username, password) => {
  return axios.post('/login', new URLSearchParams({
    username: username,
    password: password
  }), {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });
};

// Inscription
export const register = async (userData) => {
  return axios.post('/register', userData);
};
```

## Déploiement

### Docker (recommandé)

Créer un `Dockerfile` :

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Puis construire et lancer :

```bash
docker build -t tpagile-auth .
docker run -p 8000:8000 tpagile-auth
```

### Avec Gunicorn

Installer Gunicorn :

```bash
pip install gunicorn
```

Créer un fichier `gunicorn.conf.py` :

```python
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
```

Puis lancer :

```bash
gunicorn -c gunicorn.conf.py main:app
```

## Résolution des problèmes

### Problème : Module non trouvé

```bash
# Installer les dépendances
pip install -r requirements.txt

# Vérifier l'environnement Python
python --version
pip --version
```

### Problème : Erreur de connexion SQLite

Vérifier que le dossier `data` existe :

```bash
mkdir -p backend/data
```

### Problème : Token invalide

1. Vérifier que la clé secrète est correcte dans `.env`
2. Vérifier que le token n'a pas expiré
3. Vérifier que le token n'a pas été révoqué (logout)

### Problème : CORS en développement

Le service accepte toutes les origines en développement. Si vous avez toujours des problèmes :

1. Vérifier que le frontend envoie bien les en-têtes
2. Vérifier qu'il n'y a pas de problème de cache

## Contribution

1. Forker le projet
2. Créer une branche pour votre fonctionnalité (`git checkout -b feature/ma-fonctionnalité`)
3. Commiter vos changements (`git commit -m "Ajout de ma fonctionnalité"`)
4. Pousser vers la branche (`git push origin feature/ma-fonctionnalité`)
5. Ouvrir une Pull Request

## Licence

Ce projet fait partie du TP_Agile et est sous licence MIT.

## Auteurs

- Diego & Nicolas (Équipe TP_Agile)
