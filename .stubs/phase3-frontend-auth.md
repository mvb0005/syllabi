# Phase 3D — Frontend Auth Shell & OpenAPI Codegen (Agent Implementation Spec)

## Goal
Wire authentication into the React/Vite frontend:
- Login page that posts to `POST /api/auth/login`
- `useCurrentUser()` hook backed by `GET /api/auth/me`
- Route guard that redirects unauthenticated users to `/login`
- Replace the handwritten `client.ts` helpers with a typed client generated from the FastAPI OpenAPI spec

---

## Dependency on Phase 3A
Requires the backend `POST /auth/login` and `GET /auth/me` endpoints from Phase 3A.
If not yet deployed, mock the responses in `src/api/client.ts` during development.

---

## Tech Stack

```
Framework:      Vite 7 + React 19 + TypeScript
Styling:        Tailwind CSS v4 — utility classes only, no CSS modules, no inline styles
Components:     Shadcn UI (already installed — see frontend/src/components/ui/)
Routing:        React Router v7 (already in package.json)
API codegen:    openapi-typescript + openapi-fetch
```

---

## Project Layout (relevant paths)

```
frontend/
  package.json                          # add openapi-typescript, openapi-fetch
  src/
    App.tsx                             # add /login route; wrap protected routes
    api/
      client.ts                         # REPLACE with openapi-fetch typed client
      schema.d.ts                       # GENERATED — do not edit manually
    components/
      auth/
        ProtectedRoute.tsx              # CREATE
      ui/                               # existing Shadcn components (use as-is)
    hooks/
      useCurrentUser.ts                 # CREATE
    pages/
      LoginPage.tsx                     # CREATE
      DashboardPage.tsx                 # already exists — keep as-is
```

---

## Implementation Tasks

### 1. OpenAPI Codegen Setup — `frontend/package.json`

Add dev dependencies:
```json
"openapi-typescript": "^7.0.0",
"openapi-fetch": "^0.10.0"
```

Add npm scripts:
```json
"gen:api": "openapi-typescript http://localhost:8000/openapi.json -o src/api/schema.d.ts"
```

Run `npm install` after updating.

### 2. Typed API Client — `frontend/src/api/client.ts` (REPLACE)

```typescript
import createClient from "openapi-fetch";
import type { paths } from "./schema";

export const apiClient = createClient<paths>({
  baseUrl: "/api",
  credentials: "include",   // send httpOnly cookies with every request
});
```

The `credentials: "include"` is required so the `access_token` httpOnly cookie is sent.

### 3. `useCurrentUser` Hook — `frontend/src/hooks/useCurrentUser.ts` (CREATE)

```typescript
interface CurrentUserState {
  user: components["schemas"]["UserPublic"] | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

export function useCurrentUser(): CurrentUserState {
  // Call GET /api/auth/me on mount
  // On 200: set user, isAuthenticated = true
  // On 401: user = null, isAuthenticated = false
  // isLoading = true until the request settles
}
```

Use `useEffect` + `useState`. Do NOT use any external state management library.

### 4. ProtectedRoute Component — `frontend/src/components/auth/ProtectedRoute.tsx` (CREATE)

```typescript
interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps): JSX.Element {
  // Use useCurrentUser()
  // If isLoading: render a loading spinner (Tailwind: "flex items-center justify-center h-screen")
  // If !isAuthenticated: <Navigate to="/login" replace />
  // Otherwise: render children
}
```

### 5. Login Page — `frontend/src/pages/LoginPage.tsx` (CREATE)

Requirements:
- Email + password fields using Shadcn `Input` and `Label`
- Submit button using Shadcn `Button`
- On submit: call `POST /api/auth/login` via `apiClient`
- On 200: navigate to `/dashboard` using `useNavigate()`
- On 4xx: show inline error message (red text, Tailwind `text-red-500 text-sm mt-1`)
- Centered card layout using Shadcn `Card`, `CardHeader`, `CardContent`
- No inline styles; Tailwind utility classes only

Example structure:
```tsx
<div className="min-h-screen flex items-center justify-center bg-gray-50">
  <Card className="w-full max-w-md">
    <CardHeader>
      <h1 className="text-2xl font-semibold">Sign In</h1>
    </CardHeader>
    <CardContent>
      {/* form */}
    </CardContent>
  </Card>
</div>
```

### 6. Update Routing — `frontend/src/App.tsx`

Wire together:
```tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";

// Routes:
// /login              → <LoginPage />
// /dashboard          → <ProtectedRoute><DashboardPage /></ProtectedRoute>
// /                   → <Navigate to="/dashboard" replace />
// *                   → <Navigate to="/dashboard" replace />
```

---

## Shadcn Components Available (already installed)

Located in `frontend/src/components/ui/`:
- `button.tsx` — `<Button variant="default|outline|ghost" />`
- `card.tsx` — `<Card>`, `<CardHeader>`, `<CardContent>`
- `input.tsx` — `<Input type="text|email|password" />`
- `label.tsx` — `<Label htmlFor="..." />`

Import as: `import { Button } from "@/components/ui/button"`

---

## Acceptance Criteria

- `npm run build` completes with no TypeScript errors
- `npm run lint` (eslint) passes with no warnings
- `npm run gen:api` regenerates `schema.d.ts` without errors (requires backend running)
- Unauthenticated visit to `/dashboard` → redirects to `/login`
- Successful login → navigates to `/dashboard`
- `useCurrentUser()` returns the logged-in user after successful login
- No `localStorage` usage anywhere in the codebase for tokens (grep must find zero hits)
- All API calls use `apiClient` from `src/api/client.ts`

---

## Constraints

- No class components — functional components and hooks only
- Tailwind utility classes exclusively — no CSS modules, no inline `style={}` props
- No `localStorage` or `sessionStorage` for JWT/auth tokens
- The generated `schema.d.ts` must never be edited manually — always regenerated via `npm run gen:api`
- Do not implement enrollment UI or grading UI — those are future phases
