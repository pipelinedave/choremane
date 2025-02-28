# Choremane

Choremane is a Progressive Web App (PWA) designed to simplify household chore management. It allows users to organize, assign, and track chores efficiently with a clean and modern interface.

## Features
- 📅 **Smart Chore Scheduling** - Automatically assigns due dates based on intervals.
- 🔒 **Authentication** - Login with GitHub and Google via Dex.
- 🎨 **Customizable UI** - Material Design-style UI with chore filtering by due date.
- 📱 **PWA Support** - Installable on mobile and desktop for quick access.
- 🔄 **Swipe Actions** - Intuitive chore management with swipe-to-complete and swipe-to-edit.
- 📊 **Log System** - Tracks chore actions with an undo feature.
- 🚀 **CI/CD Workflow** - Staging and production deployments via GitHub Actions.
- ☁️ **Cloud-Synced** - Data stored in PostgreSQL with API access via Kubernetes.
- 🔔 **Push Notifications** - Get reminders for due and overdue chores.

## Deployment
Choremane runs on a Kubernetes cluster with ArgoCD managing deployments. The backend is built with FastAPI, while the frontend is a Vue-based PWA.

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
- **Staging Deployment**: Auto-deploys on commits to the main branch.
- **Production Deployment**: Triggered by `*prod*` tags.

## Roadmap
- ✅ **Basic chore management**
- ✅ **GitHub Actions CI/CD**
- 🔄 **PWA enhancements**
- 🔄 **Dex authentication integration**
- 🔄 **Advanced chore filters & smart suggestions**

## Contributing
Contributions are welcome! Open an issue or submit a pull request to suggest improvements.
