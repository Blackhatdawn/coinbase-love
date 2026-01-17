import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Loader2 } from "lucide-react";

interface ProtectedRouteProps {
  children?: React.ReactNode;
}

const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const auth = useAuth();
  
  if (auth?.isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f]">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-16 h-16 rounded-full border-2 border-gold-500/20" />
            <div className="absolute inset-0 w-16 h-16 rounded-full border-2 border-transparent border-t-gold-500 animate-spin" />
            <img src="/logo.svg" alt="" className="absolute inset-0 m-auto w-8 h-8" />
          </div>
          <p className="text-muted-foreground animate-pulse">Loading your session...</p>
        </div>
      </div>
    );
  }
  
  if (!auth?.user) {
    return <Navigate to="/auth" replace />;
  }
  
  // If children exist, render them; otherwise render Outlet for nested routes
  return children ? <>{children}</> : <Outlet />;
};

export default ProtectedRoute;
