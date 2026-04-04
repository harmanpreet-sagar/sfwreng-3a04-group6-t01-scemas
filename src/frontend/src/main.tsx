/**
 * Application entry point — bootstraps React and mounts the component tree.
 *
 * Provider ordering matters:
 *  1. BrowserRouter — must wrap everything that uses useNavigate / useLocation.
 *     AuthContext's signOut and the RequireAuth guard both call navigate(), so
 *     BrowserRouter must be an ancestor of AuthProvider and App.
 *  2. AuthProvider — must wrap App so that RequireAuth and any page component
 *     can call useAuth() without a context error.
 *  3. App — contains the route definitions; placed inside both providers.
 *
 * React.StrictMode:
 *  Enables additional runtime warnings in development (double-invoked effects,
 *  deprecated API usage). Has no effect in the production build.
 *  It causes useEffect to run twice in dev — this is intentional behaviour and
 *  not a bug; effects must be idempotent (calling setAuthToken twice is safe).
 *
 * index.css is imported here (not inside App) so Tailwind's global base styles
 * and Leaflet's CSS apply before any component renders.
 */
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
