import { createContext, useContext, useState, useEffect, ReactNode } from "react";
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
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<{ error?: string }>;
  signUp: (email: string, password: string, name: string) => Promise<{ error?: string }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session by calling the /me endpoint
    // If the user is authenticated, the server will return user info
    // The HttpOnly cookie will be sent automatically
    const checkSession = async () => {
      try {
        console.log('[Auth] Checking session...');
        
        // Add timeout to prevent infinite loading
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Session check timeout')), 10000)
        );
        
        const response = await Promise.race([
          api.auth.getProfile(),
          timeoutPromise
        ]) as any;
        
        console.log('[Auth] Session check response:', response);
        
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
        
        console.log('[Auth] Session check successful, user:', userData.email);
      } catch (error: any) {
        // Expected: No valid session, user is not authenticated
        // Log errors only if they seem unexpected
        console.log('[Auth] Session check failed:', error);
        if (error?.statusCode && error.statusCode !== 401 && error.statusCode !== 0) {
          console.warn('⚠️ Unexpected session check error:', error.message || error);
        } else {
          console.log('[Auth] No active session (expected for logged-out users)');
        }
        setUser(null);
        clearSentryUser();
      } finally {
        console.log('[Auth] Setting isLoading to false');
        setIsLoading(false);
      }
    };

    checkSession();
  }, []);

  const signIn = async (email: string, password: string): Promise<{ error?: string }> => {
    try {
      const response = await api.auth.login({ email, password });

      const userData: User = {
        id: response.user.id,
        email: response.user.email,
        name: response.user.name,
        createdAt: response.user.createdAt,
      };

      // HttpOnly cookies are set by the server, no need to store here
      setUser(userData);
      
      // Set user context in Sentry
      setSentryUser({
        id: userData.id,
        email: userData.email,
        username: userData.name,
      });

      return {};
    } catch (error: any) {
      return { error: error.message || "Failed to sign in" };
    }
  };

  const signUp = async (email: string, password: string, name: string): Promise<{ error?: string }> => {
    try {
      const response = await api.auth.signup({ email, password, name });

      const userData: User = {
        id: response.user.id,
        email: response.user.email,
        name: response.user.name,
        createdAt: response.user.createdAt,
      };

      // HttpOnly cookies are set by the server, no need to store here
      setUser(userData);
      
      // Set user context in Sentry
      setSentryUser({
        id: userData.id,
        email: userData.email,
        username: userData.name,
      });

      return {};
    } catch (error: any) {
      return { error: error.message || "Failed to create account" };
    }
  };

  const signOut = async () => {
    try {
      await api.auth.logout();
    } catch (error) {
      // Even if logout fails, clear the user state
      console.error("Logout error:", error);
    }
    // Clear user state (cookies are cleared by the server)
    setUser(null);
    
    // Clear user context in Sentry
    clearSentryUser();
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, signIn, signUp, signOut }}>
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
