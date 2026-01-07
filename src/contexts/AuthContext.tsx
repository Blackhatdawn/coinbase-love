import { createContext, useContext, useState, useEffect, ReactNode } from "react";

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
  signOut: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const USERS_KEY = "cryptovault_users";
const SESSION_KEY = "cryptovault_session";

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const session = localStorage.getItem(SESSION_KEY);
    if (session) {
      try {
        setUser(JSON.parse(session));
      } catch {
        localStorage.removeItem(SESSION_KEY);
      }
    }
    setIsLoading(false);
  }, []);

  const signIn = async (email: string, password: string): Promise<{ error?: string }> => {
    const usersData = localStorage.getItem(USERS_KEY);
    const users = usersData ? JSON.parse(usersData) : {};
    
    const userRecord = users[email.toLowerCase()];
    if (!userRecord) {
      return { error: "No account found with this email" };
    }
    
    if (userRecord.password !== password) {
      return { error: "Incorrect password" };
    }
    
    const userData: User = {
      id: userRecord.id,
      email: userRecord.email,
      name: userRecord.name,
      createdAt: userRecord.createdAt,
    };
    
    setUser(userData);
    localStorage.setItem(SESSION_KEY, JSON.stringify(userData));
    return {};
  };

  const signUp = async (email: string, password: string, name: string): Promise<{ error?: string }> => {
    const usersData = localStorage.getItem(USERS_KEY);
    const users = usersData ? JSON.parse(usersData) : {};
    
    if (users[email.toLowerCase()]) {
      return { error: "An account with this email already exists" };
    }
    
    const newUser = {
      id: crypto.randomUUID(),
      email: email.toLowerCase(),
      name,
      password,
      createdAt: new Date().toISOString(),
    };
    
    users[email.toLowerCase()] = newUser;
    localStorage.setItem(USERS_KEY, JSON.stringify(users));
    
    const userData: User = {
      id: newUser.id,
      email: newUser.email,
      name: newUser.name,
      createdAt: newUser.createdAt,
    };
    
    setUser(userData);
    localStorage.setItem(SESSION_KEY, JSON.stringify(userData));
    return {};
  };

  const signOut = () => {
    setUser(null);
    localStorage.removeItem(SESSION_KEY);
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
