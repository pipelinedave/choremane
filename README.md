# Choremane

Choremane is a Progressive Web App (PWA) designed to simplify household chore management. It allows users to organize, assign, and track chores efficiently with a clean and modern interface.

## Features

- 📅 **Smart Chore Scheduling** - Automatically assigns due dates based on intervals
- 🔒 **Authentication** - Dex login with optional mock auth for local development
- 🎨 **Customizable UI** - Material You design with dynamic theming
- 📱 **PWA Support** - Installable on mobile and desktop for quick access
- 🎮 **Gesture Controls** - Native pointer-driven swipe actions on chore cards
- 🎯 **Chore Filter Pills** - Overhauled pills with API-driven counts for overdue, today, upcoming, and custom views
- 🔐 **Private Chores** - User-scoped chores stay hidden from the shared household list unless explicitly shared
- 🧭 **Household Health** - Backend-calculated score rendered as a performance bar in the chore list
- 🧾 **Activity Log Overlay** - Persistent chore log with inline undo/archive controls
- ☁️ **Cloud-Synced** - PostgreSQL backend with FastAPI
- 🔔 **Push Notifications** - Configurable daily reminders
- 🔄 **Offline Support** - Version-aware service worker with cache-busting

## Deployment

Choremane uses a GitOps workflow with ArgoCD managing deployments to a K3s cluster. The backend uses FastAPI with PostgreSQL, while the frontend is a Vue 3 PWA.

### Local Development

1. Clone the repository:

   ```bash
   git clone https://github.com/pipelinedave/choremane.git
   cd choremane
   ```

2. Install dependencies:
   - Backend (from `backend/`):

     ```bash
     python -m venv .venv
     source .venv/bin/activate
     pip install -r requirements.txt
     ```

   - Frontend (from `frontend/`):

     ```bash
     npm install
     ```

3. Using VS Code Tasks (recommended):
   - Open the project in VS Code
   - Press `Ctrl+Shift+P` and select `Tasks: Run Task`
   - Select `Start PostgreSQL` to start the database
   - Select `Run Backend Dev Server` to start the API server
   - Select `Run Frontend Dev Server` to start the UI

   > **Note:** For local development, set `USE_MOCK_AUTH=true` to use the built-in mock login flow.
   > This avoids Dex downtime while still exercising the full auth pipeline. See
   > [AUTH_README.md](AUTH_README.md) for more details.
   >
   > If you encounter any authentication issues, check the backend logs for detailed information
   > and refer to the troubleshooting section in [AUTH_README.md](AUTH_README.md).

4. Using VS Code Debugging:
   - Open the Debug panel in VS Code (`Ctrl+Shift+D`)
   - Select `Full Stack Debug` from the dropdown
   - Click the green play button to start PostgreSQL, backend, and frontend with debugging

5. Manual startup:

   ```bash
   # Terminal 1: Start PostgreSQL
   docker-compose up -d postgres

   # Terminal 2: Run backend
   cd backend
   export OAUTH_CLIENT_ID=choremane
   export OAUTH_CLIENT_SECRET=choremane-secret
   export DEX_ISSUER_URL=https://dex.stillon.top
   export SESSION_SECRET=local-dev-secret
   export FRONTEND_URL=http://localhost:5000
   export USE_MOCK_AUTH=true  # Use the built-in mock auth flow for local dev
   export POSTGRES_HOST=localhost
   export POSTGRES_DB=choresdb
   export POSTGRES_USER=admin
   export POSTGRES_PASSWORD=password
   python -m uvicorn app.main:app --reload --port 8090

   # Terminal 3: Run frontend (Vite dev server with API proxy to port 8090)
   cd frontend
   npm run serve
   ```

## CI/CD Pipeline

- **Staging Deployment**: Auto-deploys on commits to the main branch
- **Production Deployment**: Triggered by `choremane/prod/v.*` tags
- **Environment Separation**: Distinct staging and production namespaces

## Roadmap

- ✅ **Basic chore management**
- ✅ **GitHub Actions CI/CD**
- ✅ **PWA core features**
- 🔄 **Dex authentication integration**
- 🔄 **Advanced chore filters & smart suggestions**
- 🔄 **DALL-E generated chore banners**
- 🔄 **Multi-language support**
- 🔄 **Performance optimizations**

## Contributing

Contributions welcome! Please read our contributing guidelines and submit PRs for review.
