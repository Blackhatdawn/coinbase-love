import { Navigate, Outlet } from "react-router-dom";
import { useState, useEffect } from "react";

interface AdminData {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface AdminRouteProps {
  children?: React.ReactNode;
}

const AdminRoute = ({ children }: AdminRouteProps) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    let mounted = true;

    const checkAdminAuth = async () => {
      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
        const response = await fetch(`${baseUrl}/api/admin/me`, {
          method: 'GET',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        });

        if (!mounted) return;

        if (!response.ok) {
          sessionStorage.removeItem('adminData');
          setIsAuthenticated(false);
          return;
        }

        const data = await response.json();
        const admin: AdminData = data?.admin;
        if (admin?.id && admin?.email && admin?.role) {
          sessionStorage.setItem('adminData', JSON.stringify(admin));
          setIsAuthenticated(true);
        } else {
          sessionStorage.removeItem('adminData');
          setIsAuthenticated(false);
        }
      } catch {
        if (!mounted) return;
        // Fail closed: network/unknown failures should not grant access.
        setIsAuthenticated(false);
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    checkAdminAuth();
    return () => {
      mounted = false;
    };
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-amber-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-400 text-sm">Verifying admin access...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/admin/login" replace />;
  }

  return children ? <>{children}</> : <Outlet />;
};

export default AdminRoute;
