/**
 * Authentication context — single source of truth for the logged-in session.
 *
 * Why a context instead of prop-drilling or a global store?
 * Any component tree depth can call useAuth() without threading account/token
 * props down through every intermediate component. This matters most for the
 * RequireAuth wrapper in App.tsx and the sign-out button deep inside the nav.
 *
 * Session persistence strategy:
 *  - Both the account object and the JWT are written to localStorage on sign-in.
 *  - On page refresh, the initial useState calls read directly from storage so
 *    the user never hits the login page unnecessarily.
 *  - The axios Authorization header is restored via useEffect so API calls
 *    made immediately after mount (e.g. the initial listThresholds in
 *    ThresholdsPage) already carry the correct Bearer token.
 *
 * Security note: storing a JWT in localStorage is acceptable for this demo
 * context. A production deployment should use httpOnly cookies to prevent
 * XSS-based token theft.
 */
import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { Account } from '../types';
import { setAuthToken, apiClient } from '../api/client';


interface AuthContextValue {
  account: Account | null;
  token: string | null;
  /** True only when account.clearance === 'admin'; controls write-gating in the UI. */
  isAdmin: boolean;
  signIn: (account: Account, token: string | null) => void;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// Namespaced keys avoid collisions when multiple apps share the same origin.
const STORAGE_KEY_ACCOUNT = 'scemas_account';
const STORAGE_KEY_TOKEN   = 'scemas_token';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Lazy initialisers read from storage once at mount — never on re-renders.
  const [account, setAccount] = useState<Account | null>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY_ACCOUNT);
      return raw ? (JSON.parse(raw) as Account) : null;
    } catch {
      // Corrupted storage — start unauthenticated rather than crashing.
      return null;
    }
  });

  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem(STORAGE_KEY_TOKEN),
  );

  // Rehydrate the axios Authorization header when the app loads with a stored token.
  // Without this, the first API call after a refresh would be unauthenticated even
  // though account is non-null, causing an immediate 401 and redirect to /login.
  useEffect(() => {
    if (token) setAuthToken(token);
  }, [token]);

  const signIn = useCallback((acc: Account, tok: string | null) => {
    setAccount(acc);
    setToken(tok);
    localStorage.setItem(STORAGE_KEY_ACCOUNT, JSON.stringify(acc));
    if (tok) {
      localStorage.setItem(STORAGE_KEY_TOKEN, tok);
      setAuthToken(tok);
      apiClient.defaults.headers.common['X-Account-Id'] = String(acc.aid);
      apiClient.defaults.headers.common['X-Account-Clearance'] = acc.clearance;
      apiClient.defaults.headers.common['X-Account-Email'] = acc.email;
    }
  }, []);

  const signOut = useCallback(() => {
    setAccount(null);
    setToken(null);
    localStorage.removeItem(STORAGE_KEY_ACCOUNT);
    localStorage.removeItem(STORAGE_KEY_TOKEN);
    // Clear the header so the next login attempt goes out unauthenticated.
    setAuthToken(null);
    delete apiClient.defaults.headers.common['X-Account-Id'];
    delete apiClient.defaults.headers.common['X-Account-Clearance'];
    delete apiClient.defaults.headers.common['X-Account-Email'];
  }, []);

  // Derive admin flag from the account's clearance string rather than the JWT role
  // so the UI stays consistent with the source-of-truth stored in the DB.
  const isAdmin = account?.clearance === 'admin';

  return (
    <AuthContext.Provider value={{ account, token, isAdmin, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

/** Throws if called outside of <AuthProvider> to surface misconfigured component trees early. */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
