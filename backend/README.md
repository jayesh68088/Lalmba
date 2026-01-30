# Mama Akinyi Chatbot Backend

Python + Flask API that powers the Matoso React chatbot interacting with a local Ollama LLM. The service keeps track of user sessions, chat history, profile information, and learning milestones.

## Features
- `/auth/register` creates a secure account, hashes the supplied PIN/password, and stores optional profile details.
- `/auth/login` authenticates existing users and restores their session.
- `/chat` stores conversations and forwards prompts to the local Ollama model at `http://localhost:11434/api/generate`.
- `/progress` persists learning milestones and notes for each user.
- `/auth/logout` clears the active session.
- `/health` confirms the API is reachable.
- `/ollama/health` pings the local Ollama daemon and lists available models for troubleshooting.
- SQLite database managed with SQLAlchemy ORM (`User`, `UserProfile`, `Chat`, `Progress` tables).

## Setup
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python server.py  # runs on http://localhost:5000
```

Quick health check:
```powershell
curl http://localhost:5000/health
```

The first launch auto-creates `lalmba_chat.db`. Configure via environment variables:
- `FLASK_SECRET_KEY` - session signing key.
- `DATABASE_URL` - alternate database URI (e.g., `sqlite:///my.db`).
- `CORS_ORIGINS` - comma-separated list of allowed frontend origins.
- `OLLAMA_BASE_URL` - override the Ollama host/port (default `http://localhost:11434`).
- `OLLAMA_DEFAULT_MODEL` - default model name when the frontend does not provide one.
- `OLLAMA_MAX_ATTEMPTS` - number of times the backend retries a generation call before failing.

Ensure Ollama is running locally with the desired model (defaults to `llama2`):
```powershell
ollama run llama2
```

If you switch to another model, update the frontend selection or set `OLLAMA_DEFAULT_MODEL`.

## Frontend Setup
```powershell
cd matoso-chatbot
npm install
npm start  # runs on http://localhost:3000
```

## Creating a User
1. Start the Flask server and the React frontend (see `matoso-chatbot/README.md`).
2. On the login screen, click **Create one here**, fill in your name, username, PIN/password, and any helpful details, then submit. A successful registration automatically signs you in.
3. If you prefer scripting, call the `/auth/register` endpoint directly:
   ```http
   POST /auth/register
   Content-Type: application/json

   {
     "name": "Jane Matoso",
     "username": "jane",
     "password": "secret-pin",
     "details": "Community savings lead"
   }
   ```
   The API returns the created user and sets the session cookie.

## Example Requests
### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "jane",
  "password": "secret-pin"
}
```

### Send a Chat Message
```http
POST /chat
Content-Type: application/json

{
  "message": "Mama Akinyi, how can I support my community group?"
}
```

### Record Progress
```http
POST /progress
Content-Type: application/json

{
  "milestone": "Completed first savings group meeting",
  "notes": "Mama Akinyi suggested a rotating leadership structure."
}
```

## Testing Tips
- Call `GET /chat?limit=20` to retrieve recent history (oldest first).
- Use `GET /progress` to view past milestones.
- `GET /auth/session` checks the active user and confirms that registration/login succeeded.
- `GET /ollama/health` reports whether the local LLM endpoint is reachable and which models are downloaded. Pair this with the Flask logs for full error traces if you see "Mama Akinyi is offline."
