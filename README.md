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
2. Start the development environment using devcontainers:
   ```bash
   code .
   ```
   This launches VSCode with the configured devcontainer.
3. Ensure the frontend and backend services are running:
   ```bash
   npm run dev # Frontend
   uvicorn main:app --reload # Backend
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
