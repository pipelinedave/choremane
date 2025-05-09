# Choremane

Choremane is a Progressive Web App (PWA) designed to simplify household chore management. It allows users to organize, assign, and track chores efficiently with a clean and modern interface.

## Features
- 📅 **Smart Chore Scheduling** - Automatically assigns due dates based on intervals
- 🔒 **Authentication** - Login with GitHub and Google via Dex
- 🎨 **Customizable UI** - Material You design with dynamic theming
- 📱 **PWA Support** - Installable on mobile and desktop for quick access
- 🔄 **Swipe Actions** - Swipe gestures using Hammer.js for intuitive interactions
- 📊 **Log System** - Tracks all actions with undo capability
- 🚀 **CI/CD Workflow** - GitOps with GitHub Actions and ArgoCD
- ☁️ **Cloud-Synced** - PostgreSQL backend with FastAPI
- 🔔 **Push Notifications** - Configurable daily reminders
- 🎯 **Smart Filtering** - Filter chores by overdue, today, and upcoming
- 🔐 **Private Chores** - User-specific private chore support
- 🔄 **Offline Support** - Full functionality without internet

## Deployment
Choremane uses a GitOps workflow with ArgoCD managing deployments to a K3s cluster. The backend uses FastAPI with PostgreSQL, while the frontend is a Vue 3 PWA.

### Local Development
1. Clone the repository:
   ```bash
   git clone https://github.com/pipelinedave/choremane.git
   cd choremane
   ```

2. Using VS Code Tasks (recommended):
   - Open the project in VS Code
   - Press `Ctrl+Shift+P` and select `Tasks: Run Task`
   - Select `Start PostgreSQL` to start the database
   - Select `Run Backend Dev Server` to start the API server
   - Select `Run Frontend Dev Server` to start the UI

   > **Note:** For local development, a mock authentication system is used by default (since May 2025) 
   > due to issues with the external Dex OIDC provider. This allows you to sign in with test credentials
   > without requiring access to the production authentication service. See [AUTH_README.md](AUTH_README.md) 
   > for more details.

3. Using VS Code Debugging:
   - Open the Debug panel in VS Code (`Ctrl+Shift+D`)
   - Select `Full Stack Debug` from the dropdown
   - Click the green play button to start PostgreSQL, backend, and frontend with debugging

4. Manual startup:
   ```bash
   # Terminal 1: Start PostgreSQL
   docker-compose up -d postgres
   
   # Terminal 2: Run backend
   cd /home/dave/src/choremane/backend
   export OAUTH_CLIENT_ID=choremane
   export OAUTH_CLIENT_SECRET=choremane-secret
   export DEX_ISSUER_URL=https://dex.stillon.top
   export SESSION_SECRET=local-dev-secret
   export FRONTEND_URL=http://localhost:5000
   export POSTGRES_HOST=localhost
   export POSTGRES_DB=choresdb
   export POSTGRES_USER=admin
   export POSTGRES_PASSWORD=password
   python -m uvicorn app.main:app --reload --port 8090
   
   # Terminal 3: Run frontend
   cd /home/dave/src/choremane/frontend
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
