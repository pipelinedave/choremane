# Choremane - Project Requirements Document (PRD)

---

## Overview

Choremane is a Material You–styled PWA for chore management. It allows multiple users to manage shared or private chores with intelligent scheduling, flexible authentication, and a modern, responsive UI. It runs fully offline with PWA capabilities and leverages AI enhancements for smarter interaction.

---

## Core Objectives

- Provide an intuitive, fast, and beautiful experience for managing recurring tasks.
- Support multiple authenticated users.
- Allow for private and shared chores.
- Enable natural language interaction and smart chore suggestions.
- Deliver reliable offline-first experience.
- Maintain clean GitOps-based CI/CD with distinct staging and production workflows.

---

## Target Users

- Individuals
- Households (multiple users)
- Small shared living environments (dorms, flats)

---

## Features

### Chore Management
- View list of chores, sorted by due state.
- Swipe to mark chores as done, edit, or delete.
- Add, edit, and remove chores.
- Set chore recurrence intervals.
- Mark chores as private to a user.

### Log System
- Persistent log overlay showing most recent action.
- Expandable view to browse full history.
- Clicking a log entry reverts the app state to that point.
- Replaces traditional toast notifications.

### Authentication
- Dex-based OAuth2 authentication (Google and GitHub).
- Users authenticated by their email address.
- User-specific data segmentation.

### Notifications
- Configurable push notifications.
- Notify users about soon-due, due, or overdue chores.
- Allow users to configure multiple daily notification times.

### Smart Features
- CopilotKit natural language understanding for:
  - Marking chores.
  - Adding new chores.
  - Adjusting chore intervals based on user behavior.
- Optional DALL-E generated banners based on chore names.

### UI/UX
- Full Material You design.
- Responsive layout (mobile-first but desktop-optimized).
- Smooth animations for all transitions.
- Material Design pills above the chore list for quick due-state filtering.
- Persistent dark mode/light mode syncing based on user system theme.

### PWA Requirements
- Installable on mobile and desktop.
- Fully offline-capable.
- Service worker caching for assets and chore data.

### Import/Export
- Manual export of chores and logs.
- Manual import with validation.

### API
- /api for chore CRUD operations.
- No API access via browser redirects (SPA boundary preserved).

### Deployment
- GitHub Actions:
  - Staging: Triggered on commits to head.
  - Production: Triggered on new `choremane/prod/v.*` tags.
- Deployed via ArgoCD to Kubernetes cluster.
- Namespaced environments (staging vs production).

---

## Non-Goals

- No support for multiple households (beyond multi-user chores within the same app).
- No in-app user registration flows (handled externally by OAuth providers).
- No admin panels or manual database editing from frontend.

---

## Technical Stack

- Vue 3 Composition API
- Pinia
- Vite
- PostgreSQL (backend chore data)
- Kubernetes (K3s cluster)
- GitHub Actions + ArgoCD
- Dex (Authentication)
- CopilotKit (Natural Language Processing)

---

## Success Criteria

- App installable and usable offline.
- Users can authenticate and see their private/public chores.
- Log overlay fully functional with undo ability.
- Chore actions properly logged and persistently stored.
- Push notifications reliably trigger based on user settings.
- Smooth UX with Material You aesthetic.
- Smart features usable via natural language.

---

# End of PRD
