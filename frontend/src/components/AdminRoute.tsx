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

/**
 * AdminRoute - Protected route wrapper for admin pages
 * 
 * Checks for admin authentication via sessionStorage (separate from user auth).
 * Redirects to /admin/login if not authenticated.
 * 
 * Usage in App.tsx:
 * <Route element={<AdminRoute />}>
 *   <Route path="/admin/dashboard" element={<AdminDashboard />} />
 * </Route>
 */
const AdminRoute = ({ children }: AdminRouteProps) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const checkAdminAuth = () => {
      const token = sessionStorage.getItem('adminToken');
      const adminData = sessionStorage.getItem('adminData');
      
      if (!token || !adminData) {
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }
      
      try {
        // Verify adminData is valid JSON
        const parsed: AdminData = JSON.parse(adminData);
        
        // Basic validation - ensure required fields exist
        if (parsed.id && parsed.email && parsed.role) {
          setIsAuthenticated(true);
        } else {
          // Invalid admin data structure
          sessionStorage.removeItem('adminToken');
          sessionStorage.removeItem('adminData');
          setIsAuthenticated(false);
        }
      } catch {
        // Invalid JSON in sessionStorage
        sessionStorage.removeItem('adminToken');
        sessionStorage.removeItem('adminData');
        setIsAuthenticated(false);
      }
      
      setIsLoading(false);
    };

    checkAdminAuth();
  }, []);

  // Show loading state while checking auth
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

  // Redirect to admin login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/admin/login" replace />;
  }

  // Render children or Outlet for nested routes
  return children ? <>{children}</> : <Outlet />;
};

export default AdminRoute;
