/**
 * App — root routing component.
 *
 * Simple explanation (alerts): Screens for viewing and managing alerts can be added
 * as routes here later; today this file wires login, protected thresholds, and auth.
 *
 * Route structure:
 *  /login       → LoginPage (public, no auth required)
 *  /thresholds  → ThresholdsPage wrapped in RequireAuth (authenticated only)
 *  /*           → redirect to /thresholds (handles unknown paths gracefully)
 *
 * RequireAuth:
 *  Reads `account` from AuthContext. If null (not signed in or token cleared),
 *  it redirects to /login before rendering the protected component. The `replace`
 *  flag overwrites the history entry so the browser Back button doesn't return
 *  the user to the blocked page.
 *
 *  Note: RequireAuth checks whether the session exists in context, not whether
 *  the JWT is still valid on the server. An expired token will pass this check
 *  but will return 401 from the first API call in ThresholdsPage, which then
 *  calls signOut() and redirects back to /login.
 *
 * BrowserRouter is mounted in main.tsx (the entry point) rather than here so
 * that App.tsx only depends on the Router being present in its ancestor tree,
 * which is easier to test with mock routers.
 */
import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import ThresholdsPage from './pages/ThresholdsPage';

/**
 * Route guard that redirects unauthenticated users to /login.
 * Rendered as a wrapper so the protected component tree is never mounted
 * until auth is confirmed — this also prevents any data-fetching hooks
 * inside ThresholdsPage from firing without credentials.
 */
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { account } = useAuth();
  if (!account) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/thresholds"
        element={
          <RequireAuth>
            <ThresholdsPage />
          </RequireAuth>
        }
      />
      {/* Catch-all: redirect any unknown path to the main dashboard.
          If the user is not authenticated, RequireAuth will then redirect
          them onward to /login. */}
      <Route path="*" element={<Navigate to="/thresholds" replace />} />
    </Routes>
  );
}
