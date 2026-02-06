import { createContext, useContext, useState, useEffect, ReactNode, useRef } from "react";
import { api } from "@/lib/apiClient";
import { setSentryUser, clearSentryUser } from "@/lib/sentry";

interface User {
  id: string;
  email: string;
  name: string;
  createdAt: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<{ error?: string }>;
  signUp: (email: string, password: string, name: string) => Promise<{ error?: string }>;
  signOut: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Maximum time to wait for session check (3 seconds)
const SESSION_CHECK_TIMEOUT = 3000;

// Retry configuration
const MAX_RETRY_ATTEMPTS = 2;
const RETRY_DELAY = 1000;

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const isCheckingSession = useRef(false);
  const sessionCheckTimerRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Check session - SECURE VERSION (No localStorage)
   * Security: Relies solely on httpOnly cookies managed by backend
   */
  const checkSession = async (attempt: number = 0): Promise<void> => {
    // Prevent concurrent session checks
    if (isCheckingSession.current && attempt === 0) {
      console.log('[Auth] Session check already in progress');
      return;
    }

    isCheckingSession.current = true;

    try {
      console.log('[Auth] Checking session (attempt', attempt + 1, 'of', MAX_RETRY_ATTEMPTS + 1, ')');
      
      // SECURITY FIX: Removed localStorage caching - fetch from API only
      // Session is verified via httpOnly cookies (secure, XSS-proof)
      const response = await fetchWithTimeout(
        api.auth.getProfile(),
        SESSION_CHECK_TIMEOUT
      );

      console.log('[Auth] ✅ Session check successful via API');
      
      const userData: User = {
        id: response.user.id,
        email: response.user.email,
        name: response.user.name,
        createdAt: response.user.createdAt,
      };

      setUser(userData);
      
      // Set user context in Sentry
      setSentryUser({
        id: userData.id,
        email: userData.email,
        username: userData.name,
      });

    } catch (error: any) {
      console.log('[Auth] ❌ Session check failed:', error.message || error);

      // Retry logic for network errors
      if (attempt < MAX_RETRY_ATTEMPTS && isNetworkError(error)) {
        console.log(`[Auth] 🔄 Retrying in ${RETRY_DELAY}ms...`);
        await delay(RETRY_DELAY);
        return checkSession(attempt + 1);
      }

      // Expected: No valid session
      if (error?.statusCode === 401 || error?.message === 'Session check timeout') {
        console.log('[Auth] ℹ️ No active session (expected for logged-out users)');
      } else {
        console.warn('[Auth] ⚠️ Unexpected session check error:', error);
      }

      setUser(null);
      clearSentryUser();
    } finally {
      setIsLoading(false);
      isCheckingSession.current = false;
      console.log('[Auth] ✅ Session check complete. Loading state: false');
    }
  };

  /**
   * Manual session refresh (for use after login/signup)
   */
  const refreshSession = async () => {
    setIsLoading(true);
    await checkSession(0);
  };

  // Initial session check on mount
  useEffect(() => {
    console.log('[Auth] 🚀 AuthProvider mounted, starting session check');
    
    // Clear any existing timers
    if (sessionCheckTimerRef.current) {
      clearTimeout(sessionCheckTimerRef.current);
    }

    // Start session check
    checkSession(0);

    // Failsafe: Force loading to false after maximum wait time
    sessionCheckTimerRef.current = setTimeout(() => {
      if (isLoading) {
        console.warn('[Auth] ⏱️ Failsafe: Forcing loading state to false after timeout');
        setIsLoading(false);
      }
    }, SESSION_CHECK_TIMEOUT + 1000);

    // Cleanup
    return () => {
      if (sessionCheckTimerRef.current) {
        clearTimeout(sessionCheckTimerRef.current);
      }
    };
  }, []); // Only run once on mount

  const signIn = async (email: string, password: string): Promise<{ error?: string }> => {
    try {
      console.log('[Auth] 🔐 Signing in...');
      const response = await api.auth.login({ email, password });

      const userData: User = {
        id: response.user.id,
        email: response.user.email,
        name: response.user.name,
        createdAt: response.user.createdAt,
      };

      // Store access token for WebSocket auth
      if (response.access_token) {
        setToken(response.access_token);
      }

      setUser(userData);
      setIsLoading(false);
      
      // Set user context in Sentry
      setSentryUser({
        id: userData.id,
        email: userData.email,
        username: userData.name,
      });

      console.log('[Auth] ✅ Sign in successful');
      return {};
    } catch (error: any) {
      console.error('[Auth] ❌ Sign in failed:', error);
      return { error: error.message || "Failed to sign in" };
    }
  };

  const signUp = async (email: string, password: string, name: string): Promise<{ error?: string }> => {
    try {
      console.log('[Auth] 📝 Signing up...');
      const response = await api.auth.signup({ email, password, name });

      const userData: User = {
        id: response.user.id,
        email: response.user.email,
        name: response.user.name,
        createdAt: response.user.createdAt,
      };

      // SECURITY FIX: No localStorage - session managed by httpOnly cookies
      setUser(userData);
      setIsLoading(false);
      
      // Set user context in Sentry
      setSentryUser({
        id: userData.id,
        email: userData.email,
        username: userData.name,
      });

      console.log('[Auth] ✅ Sign up successful');
      return {};
    } catch (error: any) {
      console.error('[Auth] ❌ Sign up failed:', error);
      return { error: error.message || "Failed to create account" };
    }
  };

  const signOut = async () => {
    try {
      console.log('[Auth] 👋 Signing out...');
      await api.auth.logout();
    } catch (error) {
      console.error('[Auth] ⚠️ Logout API error (continuing anyway):', error);
    }
    
    setUser(null);
    setToken(null);
    clearSentryUser();
    console.log('[Auth] ✅ Signed out');
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, signIn, signUp, signOut, refreshSession }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Fetch with timeout
 */
function fetchWithTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error('Session check timeout')), timeoutMs)
    ),
  ]);
}

/**
 * Check if error is a network error (should retry)
 */
function isNetworkError(error: any): boolean {
  return (
    error?.code === 'NETWORK_ERROR' ||
    error?.code === 'TIMEOUT_ERROR' ||
    error?.message?.includes('timeout') ||
    error?.message?.includes('network') ||
    !error?.statusCode // No status code = network error
  );
}

/**
 * Delay helper
 */
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
