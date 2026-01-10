import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { Web3Provider } from "@/contexts/Web3Context";
import ProtectedRoute from "@/components/ProtectedRoute";
import RedirectLoadingSpinner from "@/components/RedirectLoadingSpinner";
import Index from "./pages/Index";
import Auth from "./pages/Auth";
import Dashboard from "./pages/Dashboard";
import TransactionHistory from "./pages/TransactionHistory";
import Markets from "./pages/Markets";
import Trade from "./pages/Trade";
import Earn from "./pages/Earn";
import Learn from "./pages/Learn";
import Contact from "./pages/Contact";
import TermsOfService from "./pages/TermsOfService";
import PrivacyPolicy from "./pages/PrivacyPolicy";
import NotFound from "./pages/NotFound";
import { useState, useEffect } from "react";
import { useRedirectSpinner } from "@/hooks/useRedirectSpinner";

const queryClient = new QueryClient();

const AppContent = () => {
  const [isLoading, setIsLoading] = useState(false);

  useRedirectSpinner((visible) => setIsLoading(visible));

  useEffect(() => {
    const handleNavigationStart = () => setIsLoading(true);
    const handleNavigationEnd = () => {
      // Hide spinner after a short delay to allow page to render
      setTimeout(() => setIsLoading(false), 300);
    };

    window.addEventListener("popstate", handleNavigationStart);
    window.addEventListener("load", handleNavigationEnd);

    return () => {
      window.removeEventListener("popstate", handleNavigationStart);
      window.removeEventListener("load", handleNavigationEnd);
    };
  }, []);

  return (
    <>
      <RedirectLoadingSpinner
        isVisible={isLoading}
        onLoadComplete={() => setIsLoading(false)}
      />
      <Routes>
        <Route path="/" element={<Index />} />
        <Route path="/auth" element={<Auth />} />
        <Route path="/markets" element={<Markets />} />
        <Route path="/trade" element={<Trade />} />
        <Route path="/earn" element={<Earn />} />
        <Route path="/learn" element={<Learn />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/terms" element={<TermsOfService />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/transactions" element={<ProtectedRoute><TransactionHistory /></ProtectedRoute>} />
        {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <Web3Provider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <AppContent />
          </BrowserRouter>
        </TooltipProvider>
      </Web3Provider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
