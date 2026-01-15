import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { api } from "@/lib/apiClient";

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
        const response = await api.auth.getProfile();
        const userData: User = {
          id: response.user.id,
          email: response.user.email,
          name: response.user.name,
          createdAt: response.user.createdAt,
        };
        setUser(userData);
      } catch (error: any) {
        // Expected: No valid session, user is not authenticated
        // Log errors only if they seem unexpected
        if (error?.status && error.status !== 401 && error.status !== 0) {
          console.warn('⚠️ Session check failed:', error.message);
        }
        setUser(null);
      } finally {
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
