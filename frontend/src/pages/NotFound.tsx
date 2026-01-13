import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Home, ArrowLeft, Search, Shield } from "lucide-react";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    // Log 404 for analytics (non-sensitive)
    if (import.meta.env.DEV) {
      console.warn("404: Page not found -", location.pathname);
    }
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      <main className="flex-1 flex items-center justify-center pt-20">
        <div className="container mx-auto px-4">
          <div className="max-w-lg mx-auto text-center">
            {/* 404 Graphic */}
            <div className="relative mb-8">
              <div className="text-[150px] md:text-[200px] font-display font-bold text-gold-500/10 leading-none select-none">
                404
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-24 h-24 rounded-2xl bg-gold-500/10 flex items-center justify-center">
                  <Search className="w-12 h-12 text-gold-400" />
                </div>
              </div>
            </div>

            {/* Message */}
            <h1 className="font-display text-3xl md:text-4xl font-bold mb-4">
              Page Not <span className="bg-gradient-to-r from-gold-400 to-gold-600 bg-clip-text text-transparent">Found</span>
            </h1>
            <p className="text-muted-foreground mb-8">
              The page you're looking for doesn't exist or has been moved. 
              Let's get you back on track.
            </p>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                variant="outline" 
                className="border-gold-500/30 hover:border-gold-400 hover:text-gold-400"
                onClick={() => window.history.back()}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Go Back
              </Button>
              <Button 
                className="bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black"
                asChild
              >
                <Link to="/">
                  <Home className="h-4 w-4 mr-2" />
                  Back to Home
                </Link>
              </Button>
            </div>

            {/* Help Links */}
            <div className="mt-12 pt-8 border-t border-gold-500/10">
              <p className="text-sm text-muted-foreground mb-4">Need help? Try these:</p>
              <div className="flex flex-wrap justify-center gap-4 text-sm">
                <Link to="/help" className="text-gold-400 hover:text-gold-300 hover:underline">Help Center</Link>
                <Link to="/faq" className="text-gold-400 hover:text-gold-300 hover:underline">FAQ</Link>
                <Link to="/contact" className="text-gold-400 hover:text-gold-300 hover:underline">Contact Support</Link>
              </div>
            </div>

            {/* Security badge */}
            <div className="mt-8 flex items-center justify-center gap-2 text-xs text-muted-foreground">
              <Shield className="h-3 w-3 text-gold-500" />
              <span>Your connection is secure</span>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default NotFound;
