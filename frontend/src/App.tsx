import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { Web3Provider } from "@/contexts/Web3Context";
import { SocketProvider } from "@/contexts/SocketContext";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import ProtectedRoute from "@/components/ProtectedRoute";
import RedirectLoadingSpinner from "@/components/RedirectLoadingSpinner";
import OnboardingLoader from "@/components/OnboardingLoader";
import AppLayout from "@/layouts/AppLayout";
import { useState, useEffect, Suspense, lazy } from "react";
import { useRedirectSpinner } from "@/hooks/useRedirectSpinner";
import { HelmetProvider } from 'react-helmet-async';
import { Toaster as HotToaster } from 'react-hot-toast';
import { healthCheckService } from "@/services/healthCheck";
import { api } from "@/lib/apiClient";
import DebugApiStatus from "@/components/DebugApiStatus";

// Eager loaded pages (critical path)
import Index from "./pages/Index";
import Auth from "./pages/Auth";
import NotFound from "./pages/NotFound";
import { ResetRequest, ResetConfirm } from "./pages/PasswordReset";

// Lazy loaded pages for performance
const Dashboard = lazy(() => import("./pages/Dashboard"));
const TransactionHistory = lazy(() => import("./pages/TransactionHistory"));
const Markets = lazy(() => import("./pages/Markets"));
const Trade = lazy(() => import("./pages/Trade"));
const EnhancedTrade = lazy(() => import("./pages/EnhancedTrade"));
const Earn = lazy(() => import("./pages/Earn"));
const Learn = lazy(() => import("./pages/Learn"));
const Contact = lazy(() => import("./pages/Contact"));
const TermsOfService = lazy(() => import("./pages/TermsOfService"));
const PrivacyPolicy = lazy(() => import("./pages/PrivacyPolicy"));
const About = lazy(() => import("./pages/About"));
const Services = lazy(() => import("./pages/Services"));
const Security = lazy(() => import("./pages/Security"));
const FAQ = lazy(() => import("./pages/FAQ"));
const Fees = lazy(() => import("./pages/Fees"));
const Blog = lazy(() => import("./pages/Blog"));
const Careers = lazy(() => import("./pages/Careers"));
const CookiePolicy = lazy(() => import("./pages/CookiePolicy"));
const AMLPolicy = lazy(() => import("./pages/AMLPolicy"));
const HelpCenter = lazy(() => import("./pages/HelpCenter"));
const RiskDisclosure = lazy(() => import("./pages/RiskDisclosure"));
const WalletDeposit = lazy(() => import("./pages/WalletDeposit"));
const WalletWithdraw = lazy(() => import("./pages/WalletWithdraw"));
const P2PTransfer = lazy(() => import("./pages/P2PTransfer"));
const PriceAlerts = lazy(() => import("./pages/PriceAlerts"));
const AdminDashboard = lazy(() => import("./pages/AdminDashboard"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000, // 30 seconds
      retry: 3, // Retry failed requests 3 times
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff with max 30s
      refetchOnWindowFocus: false,
      refetchOnReconnect: true, // Refetch on network reconnection
      // Circuit breaker: pause retries if too many failures
      networkMode: 'online', // Only run queries when online
    },
    mutations: {
      retry: 2, // Retry mutations twice
      retryDelay: (attemptIndex) => Math.min(500 * 2 ** attemptIndex, 5000), // Faster retry for mutations
      // Network mode for mutations
      networkMode: 'online',
    },
  },
});

// Suspense fallback component - Premium loading animation
const PageLoader = () => (
  <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-2 border-gold-500/20" />
        <div className="absolute inset-0 w-16 h-16 rounded-full border-2 border-transparent border-t-gold-500 animate-spin" />
        <img src="/logo.svg" alt="" className="absolute inset-0 m-auto w-8 h-8" />
      </div>
      <p className="text-sm text-muted-foreground animate-pulse">Loading...</p>
    </div>
  </div>
);

const AppContent = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [apiAvailable, setApiAvailable] = useState(true);

  useRedirectSpinner((visible) => setIsLoading(visible));

  // Initialize health check and warmup API
  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Warmup: Make initial API request to activate backend
        console.log('[App] Warming up backend API...');
        try {
          await api.crypto.getAll();
          console.log('[App] ✅ Backend API is active and responding');
          setApiAvailable(true);
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : String(error);
          console.warn(
            '[App] ⚠️ Backend API warmup failed:',
            errorMessage
          );
          // Still allow app to load even if initial call fails
          setApiAvailable(false);
        }

        // Start health check service to keep backend alive
        healthCheckService.start();
      } finally {
        setTimeout(() => setIsInitializing(false), 2000);
      }
    };

    initializeApp();

    // Cleanup: Stop health check on unmount
    return () => {
      healthCheckService.stop();
    };
  }, []);

  // Handle navigation loading states
  useEffect(() => {
    const handleNavigationStart = () => setIsLoading(true);
    const handleNavigationEnd = () => setTimeout(() => setIsLoading(false), 300);

    window.addEventListener("popstate", handleNavigationStart);
    window.addEventListener("load", handleNavigationEnd);

    return () => {
      window.removeEventListener("popstate", handleNavigationStart);
      window.removeEventListener("load", handleNavigationEnd);
    };
  }, []);

  return (
    <>
      <OnboardingLoader isLoading={isInitializing} minDisplayTime={2000} />
      <RedirectLoadingSpinner isVisible={isLoading} onLoadComplete={() => setIsLoading(false)} />
      
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* ============================================ */}
          {/* PUBLIC ROUTES - With full marketing layout */}
          {/* ============================================ */}
          <Route path="/" element={<Index />} />
          <Route path="/auth" element={<Auth />} />
          <Route path="/markets" element={<Markets />} />
          <Route path="/learn" element={<Learn />} />
          <Route path="/contact" element={<Contact />} />

          {/* Password Reset */}
          <Route path="/reset-password" element={<ResetRequest />} />
          <Route path="/reset" element={<ResetConfirm />} />

          {/* Company Pages */}
          <Route path="/about" element={<About />} />
          <Route path="/services" element={<Services />} />
          <Route path="/security" element={<Security />} />
          <Route path="/careers" element={<Careers />} />
          <Route path="/blog" element={<Blog />} />
          <Route path="/fees" element={<Fees />} />

          {/* Resources */}
          <Route path="/faq" element={<FAQ />} />
          <Route path="/help" element={<HelpCenter />} />

          {/* Legal Pages */}
          <Route path="/terms" element={<TermsOfService />} />
          <Route path="/privacy" element={<PrivacyPolicy />} />
          <Route path="/cookies" element={<CookiePolicy />} />
          <Route path="/aml" element={<AMLPolicy />} />
          <Route path="/risk-disclosure" element={<RiskDisclosure />} />

          {/* ============================================ */}
          {/* PROTECTED ROUTES - With AppLayout (Dashboard layout) */}
          {/* No heavy footer, slim sidebar, professional dashboard UI */}
          {/* ============================================ */}
          <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/transactions" element={<TransactionHistory />} />
            <Route path="/wallet/deposit" element={<WalletDeposit />} />
            <Route path="/wallet/withdraw" element={<WalletWithdraw />} />
            <Route path="/wallet/transfer" element={<P2PTransfer />} />
            <Route path="/alerts" element={<PriceAlerts />} />
            <Route path="/trade" element={<ErrorBoundary><EnhancedTrade /></ErrorBoundary>} />
            <Route path="/earn" element={<Earn />} />
            <Route path="/admin" element={<AdminDashboard />} />
          </Route>

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>

      {/* Debug API Status - Development Only */}
      <DebugApiStatus />
    </>
  );
};

const App = () => (
  <HelmetProvider>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Web3Provider>
          <SocketProvider>
            <TooltipProvider>
              <Toaster />
              <Sonner />
              <HotToaster 
                position="top-right"
                toastOptions={{
                  style: {
                    background: '#1a1a2e',
                    color: '#fff',
                    border: '1px solid rgba(245, 158, 11, 0.2)',
                  },
                }}
              />
              <BrowserRouter>
                <AppContent />
              </BrowserRouter>
            </TooltipProvider>
          </SocketProvider>
        </Web3Provider>
      </AuthProvider>
    </QueryClientProvider>
  </HelmetProvider>
);

export default App;
