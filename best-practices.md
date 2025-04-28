# Choremane - Best Practices

This document defines coding standards, architecture guidelines, and design principles to follow for the Choremane project.

---

## Coding Standards

- **Language:** JavaScript/TypeScript (future optional migration)
- **Framework:** Vue 3 Composition API
- **State Management:** Pinia
- **Style:**
  - Use Composition API with `script setup` syntax.
  - Prefer **explicit imports** over default imports where possible.
  - Group related composables, stores, and components logically by feature.
- **Naming Conventions:**
  - Stores: `somethingStore.js`
  - Components: `PascalCase.vue`
  - Files and Folders: `kebab-case`
- **Commits:** Follow conventional commits (`fix:`, `feat:`, `chore:`, etc.)
- **Formatting:** Prettier, default settings.

---

## Architecture Guidelines

- **Component-Driven Development**
  - Keep components **small and focused**.
  - Use slots and scoped props to maximize reusability.
- **State Management**
  - Use Pinia stores for all global/shared reactive data.
  - Each major feature should have its own store if needed.
- **Persistence**
  - Use `localStorage` for lightweight persistence of user-specific UI state.
  - Backend sync to PostgreSQL where relevant for chores/tasks data.
- **PWA**
  - App must be installable and support offline usage.
  - Use service workers for caching critical assets and pages.
- **Authentication**
  - Use Dex as an OAuth2 provider (Google, GitHub).
  - Implement user-specific state segregation.

---

## UI/UX Best Practices

- **Material You Design**
  - Dynamic color theming based on user system theme.
  - Rounded corners, elevation (shadows), soft motion animations.
- **Interactions**
  - Swipe gestures on chore cards.
  - Smooth expand/collapse animations for overlays.
  - Responsive layouts for mobile and desktop.
- **Accessibility**
  - Proper alt text, ARIA roles where necessary.
  - Ensure good color contrast.

---

## Feature-Specific Best Practices

- **Log System**
  - Persistent and limited history (~100 entries).
  - Log actions must always be reflected in the bottom overlay.
  - Expandable with a drag handle.
- **Notifications**
  - Push notifications must be user-configurable.
  - Configurations saved per user profile.
- **Smart Features**
  - Natural language interaction and intelligent chore suggestions must be layered cleanly on top of manual functionality without disruption.

---

## Deployment and Environments

- **GitHub Actions CI/CD**
  - Staging: On head branch commits.
  - Production: On `choremane/prod/v.*` tags.
- **ArgoCD**
  - GitOps-based deployment to Kubernetes cluster.
- **Namespaces**
  - Separate staging and production environments by namespace.

---

This document must evolve as the project grows. Always prefer **clarity, simplicity, and consistency** over cleverness.
