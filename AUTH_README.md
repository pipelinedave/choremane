# Choremane Authentication with Dex

This document provides an overview of how authentication has been implemented in Choremane using Dex as an OIDC provider.

## Backend Implementation

The backend uses FastAPI's OAuth2 functionality with JWT token validation:

1. **Dependencies**:
   - `python-jose[cryptography]`: JWT token handling
   - `httpx`: Async HTTP client for interacting with Dex
   - `authlib`: OAuth2 client implementation
   - `python-multipart`: Form data parsing

2. **Key Files**:
   - `app/auth.py`: JWT validation, user extraction, and JWKS handling
   - `app/api/auth_routes.py`: Authentication endpoints (callback, refresh)
   - `app/main.py`: Session middleware and OAuth setup
   - `app/models.py`: User model and token structures

3. **Kubernetes Configuration**:
   - Environment variables for OAuth settings
   - Secret for client credentials
   - ConfigMap for URLs and configuration

## Frontend Implementation

The frontend uses Pinia for state management and Vue Router for navigation:

1. **Dependencies**:
   - `jwt-decode`: Decoding JWT tokens
   - `vue-router`: Route protection and redirection

2. **Key Files**:
   - `src/store/authStore.js`: Token management and user state
   - `src/views/Login.vue`: Login page with Dex redirect
   - `src/views/AuthCallback.vue`: Callback handling after authentication
   - `src/plugins/axios.js`: Token refresh interceptors

3. **Authentication Flow**:
   - User visits protected route
   - Router guard checks authentication state
   - Unauthenticated users are redirected to login
   - Login redirects to Dex
   - After authentication, tokens are stored in Pinia
   - Token is included in all API requests
   - Refresh token is used to obtain new tokens when needed

## Local Development Authentication

Starting from May 2025, a mock authentication system has been implemented for local development due to issues with the external Dex OIDC provider. This allows developers to sign in with test credentials without requiring access to the production authentication service.

### How it works

1. The backend checks for the `USE_MOCK_AUTH` environment variable
2. When `USE_MOCK_AUTH=true`, authentication requests are redirected to an internal mock login page
3. Developers can enter test credentials and receive valid JWT tokens
4. These tokens work the same as production tokens for local development

### Usage

The VS Code task "Run Backend Dev Server" automatically includes the `USE_MOCK_AUTH=true` environment variable. When you navigate to the login page in your local environment, you'll be presented with a simple form instead of being redirected to the Dex provider.

### Troubleshooting

If you encounter authentication issues in local development:

1. Verify that the backend is running with `USE_MOCK_AUTH=true`
2. Check that the frontend is correctly redirecting to `http://localhost:8090/auth/login`
3. Ensure the `FRONTEND_URL` environment variable is correctly set to match your frontend URL (default: `http://localhost:5000`)
4. Check the browser console for any error messages during the authentication process
5. Look at the backend logs for detailed information about the authentication flow

### Reverting to Real Authentication

If you need to test with the actual Dex authentication:

1. Ensure the Dex server is operational (check with your team lead)
2. Edit the VS Code task to remove the `USE_MOCK_AUTH=true` environment variable
3. Restart the backend server

## Testing

1. Local development:
   ```bash
   # Terminal 1: Run backend
   cd /home/dave/src/choremane/backend
   export OAUTH_CLIENT_ID=choremane
   export OAUTH_CLIENT_SECRET=choremane-secret
   export DEX_ISSUER_URL=https://dex.stillon.top
   export SESSION_SECRET=local-dev-secret
   export FRONTEND_URL=http://localhost:5000
   export USE_MOCK_AUTH=true  # Enable mock authentication for local development
   uvicorn app.main:app --reload --port 8090
   
   # Terminal 2: Run frontend
   cd /home/dave/src/choremane/frontend
   npm run serve
   ```

2. Kubernetes:
   - Frontend: https://chores.stillon.top
   - Backend: https://chores.stillon.top/api
   - Dex: https://dex.stillon.top

## Security Considerations

1. **Token Handling**:
   - Access tokens expire after 24 hours
   - Refresh tokens are stored securely
   - JWKs are cached to improve performance

2. **User Management**:
   - User information is stored in the database
   - Private chores are associated with user emails
   - Login timestamps are recorded

3. **Environment Configuration**:
   - Different secrets for staging and production
   - Session secret is stored in ConfigMap
   - Client secret is stored in Secret
