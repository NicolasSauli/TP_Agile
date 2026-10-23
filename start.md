# Démarrer le projet Scrum IA

Ce projet contient deux applications à lancer dans **deux terminaux PowerShell distincts** :

- `backend` : API FastAPI, agents IA et base SQLite ;
- `front` : interface React/Vite.

## 1. Prérequis

Installez au préalable :

- Python 3.10 ou plus récent ;
- Node.js LTS (avec npm) ;
- une clé API Gemini, nécessaire uniquement pour les fonctions IA.

Vérifiez les installations :

```powershell
python --version
node --version
npm --version
```

> Si `python` ne fonctionne pas sous Windows, essayez `py --version`. Installez Python depuis [python.org](https://www.python.org/downloads/) si les deux commandes échouent.

## 2. Configurer et lancer le backend

Ouvrez un premier terminal PowerShell et exécutez :

```powershell
cd "C:\Users\FABIE\Desktop\Nouveau dossier (5)\TP_Agile\backend"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Ouvrez ensuite le fichier `.env` et remplacez la valeur de `GEMINI_API_KEY` :

```env
GEMINI_API_KEY=votre-cle-api-gemini
AGENT_MODEL=gemini-2.5-flash
DATABASE_URL=sqlite:///./scrum_ai.db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Lancez enfin l’API :

```powershell
uvicorn app.main:app --reload
```

Le backend est prêt lorsque le terminal affiche que le serveur écoute sur `http://127.0.0.1:8000`.

Pages utiles :

- API : [http://127.0.0.1:8000](http://127.0.0.1:8000)
- État de santé : [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- Documentation interactive Swagger : [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

La base de données `scrum_ai.db` est créée automatiquement dans le dossier `backend` au premier lancement. Ne commitez ni cette base ni le fichier `.env`.

### Si l’activation PowerShell est bloquée

Exécutez cette commande uniquement dans le terminal courant, puis relancez la commande d’activation :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 3. Lancer le frontend

Ouvrez un **second** terminal PowerShell :

```powershell
cd "C:\Users\FABIE\Desktop\Nouveau dossier (5)\TP_Agile\front"
npm install
Copy-Item .env.example .env
npm run dev
```

Vite affiche une URL, normalement [http://localhost:5173](http://localhost:5173). Ouvrez-la dans votre navigateur.

## 4. Tester le parcours IA via Swagger

Dans [Swagger](http://127.0.0.1:8000/docs), utilisez les routes dans cet ordre :

1. `POST /api/v1/projects` : créez un projet avec un nom et une description détaillée.
2. `POST /api/v1/projects/{project_id}/clarifications/start` : obtenez la première question du Product Owner.
3. `POST /api/v1/projects/{project_id}/clarifications` : envoyez chaque réponse et répétez jusqu’à ce que le projet soit prêt.
4. `POST /api/v1/projects/{project_id}/generate` : lance les agents Product Owner, User Stories, Backlog et Scrum.
5. `GET /api/v1/projects/{project_id}` : consultez les Stories, tâches, dépendances et sprints créés.

Pour enregistrer une modification manuelle de tâche (priorité, statut Kanban, sprint, dépendances…), utilisez :

```text
PATCH /api/v1/projects/{project_id}/tasks/{task_id}
```

Une tâche modifiée manuellement est protégée lors d’une régénération du plan.

## 5. Personnaliser les agents

Les prompts sont des fichiers indépendants dans `backend/prompts` :

- `agent_product_owner_prompt.txt`
- `agent_user_stories_prompt.txt`
- `agent_backlog_prompt.txt`
- `agent_scrum_prompt.txt`
- `agent_orchestrator_prompt.txt`

Modifiez le prompt de l’agent voulu directement. Les fichiers sont relus à chaque appel IA : aucun redémarrage du serveur n’est nécessaire après une modification de prompt.

Pour modifier le modèle, changez `AGENT_MODEL` dans `.env`, puis redémarrez FastAPI. Le modèle par défaut est `gemini-2.5-flash`.

## 6. Tester le backend

Avec l’environnement virtuel activé :

```powershell
pip install -r requirements-dev.txt
pytest -q
```

## 7. Connexion frontend / backend

Le frontend est connecté au backend FastAPI. Son fichier `front/.env` définit l’URL utilisée :

```env
VITE_API_URL=http://127.0.0.1:8000/api/v1
```

L’interface appelle réellement l’API pour créer un projet, répondre aux clarifications IA, générer le plan et sauvegarder les déplacements de cartes Kanban. Démarrez donc toujours le backend avant le frontend.

## Dépannage rapide

| Symptôme | Solution |
| --- | --- |
| Réponse `503` des routes IA | Vérifiez que `GEMINI_API_KEY` est renseignée dans `backend/.env`, puis redémarrez le backend. |
| Réponse `502` des routes IA | Consultez `GET /api/v1/projects/{project_id}/agent-runs` pour voir l’agent et l’erreur concernés. |
| Port 8000 déjà utilisé | Lancez `uvicorn app.main:app --reload --port 8001`. |
| Le frontend ne démarre pas | Supprimez `front/node_modules`, puis exécutez à nouveau `npm install`. |
| Le navigateur bloque l’API | Vérifiez que le frontend utilise `http://localhost:5173` ou ajoutez son origine à `CORS_ORIGINS` dans `.env`. |
