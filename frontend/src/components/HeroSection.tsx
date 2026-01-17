import { Button } from "@/components/ui/button";
import { ArrowRight, Shield, Vault, Lock, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

const HeroSection = () => {
  const auth = useAuth();
  const user = auth?.user ?? null;
  
  return (
    <section className="relative pt-24 sm:pt-28 md:pt-32 pb-12 sm:pb-16 md:pb-20 overflow-hidden" data-testid="hero-section">
      {/* Background Effects - Gold themed */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-48 sm:w-72 md:w-96 h-48 sm:h-72 md:h-96 bg-gold-500/10 rounded-full blur-3xl animate-pulse-glow" />
        <div className="absolute bottom-1/4 right-1/4 w-40 sm:w-60 md:w-80 h-40 sm:h-60 md:h-80 bg-gold-600/10 rounded-full blur-3xl animate-pulse-glow" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] sm:w-[450px] md:w-[600px] h-[300px] sm:h-[450px] md:h-[600px] bg-gold-400/5 rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-4 sm:px-6 relative z-10">
        <div className="max-w-4xl mx-auto text-center animate-fade-in">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 sm:px-4 py-2 sm:py-2 rounded-full bg-gold-500/10 border border-gold-500/20 mb-6 sm:mb-8 backdrop-blur-sm touch-target-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-gold-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-gold-500"></span>
            </span>
            <span className="text-sm sm:text-sm text-gold-400 font-medium">Trusted by 250+ Institutions Globally</span>
          </div>

          {/* Headline - Gold gradient with mobile-first sizing */}
          <h1 className="font-display text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold mb-4 sm:mb-6 leading-tight px-2" data-testid="hero-headline">
            The Custody Solution
            <span className="block bg-gradient-to-r from-gold-400 via-gold-500 to-gold-600 bg-clip-text text-transparent">
              Institutions Trust With $10B+
            </span>
          </h1>

          {/* Subheadline - Improved readability */}
          <p className="text-base sm:text-lg md:text-xl text-foreground/80 mb-8 sm:mb-10 max-w-2xl mx-auto px-4 leading-relaxed" data-testid="hero-subheadline">
            Multi-jurisdiction cold storage, real-time proof of reserves, and zero security breaches since 2019. 
            Built for family offices, hedge funds, and enterprises who demand more than promises.
          </p>

          {/* CTAs - Gold themed with mobile-first sizing */}
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center mb-12 sm:mb-16 px-4">
            <Button 
              size="lg" 
              className="relative overflow-hidden bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold shadow-lg shadow-gold-500/25 hover:shadow-gold-500/40 transition-all duration-300 hover:scale-105 group h-12 sm:h-14 px-6 sm:px-8 text-base min-h-[48px]"
              asChild 
              data-testid="hero-cta-primary"
            >
              <Link to={user ? "/dashboard" : "/auth"}>
                <span className="relative z-10 flex items-center gap-2">
                  <Sparkles className="h-4 w-4 sm:h-5 sm:w-5" />
                  {user ? "Go to Dashboard" : "Get Started"}
                  <ArrowRight className="h-4 w-4 sm:h-5 sm:w-5 transition-transform group-hover:translate-x-1" />
                </span>
                <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform duration-700" />
              </Link>
            </Button>
            <Button 
              variant="outline" 
              size="lg"
              className="border-gold-500/30 hover:border-gold-400 hover:bg-gold-500/10 hover:text-gold-400 transition-all duration-300 h-12 sm:h-14 px-6 sm:px-8 text-base min-h-[48px]"
              asChild 
              data-testid="hero-cta-secondary"
            >
              <Link to="/services">
                Explore Services
              </Link>
            </Button>
          </div>

          {/* Trust Indicators - Gold accents with responsive grid and improved readability */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 max-w-3xl mx-auto px-4">
            <div className="glass-card p-5 sm:p-6 animate-slide-up border border-gold-500/10 hover:border-gold-500/30 transition-all duration-300 group" style={{ animationDelay: '0.1s' }} data-testid="trust-indicator-1">
              <div className="flex sm:flex-col items-center sm:items-center gap-4 sm:gap-0">
                <div className="w-14 h-14 sm:w-14 sm:h-14 sm:mx-auto sm:mb-3 rounded-xl bg-gold-500/10 flex items-center justify-center group-hover:bg-gold-500/20 transition-colors flex-shrink-0">
                  <Shield className="h-7 w-7 sm:h-7 sm:w-7 text-gold-400" />
                </div>
                <div className="text-left sm:text-center">
                  <div className="font-display text-2xl sm:text-2xl font-bold text-gold-400">Zero Breaches</div>
                  <div className="text-[15px] sm:text-sm text-foreground/70 mt-1">Since 2019</div>
                </div>
              </div>
            </div>
            <div className="glass-card p-5 sm:p-6 animate-slide-up border border-gold-500/10 hover:border-gold-500/30 transition-all duration-300 group" style={{ animationDelay: '0.2s' }} data-testid="trust-indicator-2">
              <div className="flex sm:flex-col items-center sm:items-center gap-4 sm:gap-0">
                <div className="w-14 h-14 sm:w-14 sm:h-14 sm:mx-auto sm:mb-3 rounded-xl bg-gold-500/10 flex items-center justify-center group-hover:bg-gold-500/20 transition-colors flex-shrink-0">
                  <Vault className="h-7 w-7 sm:h-7 sm:w-7 text-gold-400" />
                </div>
                <div className="text-left sm:text-center">
                  <div className="font-display text-2xl sm:text-2xl font-bold text-gold-400">$10.2B</div>
                  <div className="text-[15px] sm:text-sm text-foreground/70 mt-1">Assets Under Custody</div>
                </div>
              </div>
            </div>
            <div className="glass-card p-5 sm:p-6 animate-slide-up border border-gold-500/10 hover:border-gold-500/30 transition-all duration-300 group" style={{ animationDelay: '0.3s' }} data-testid="trust-indicator-3">
              <div className="flex sm:flex-col items-center sm:items-center gap-4 sm:gap-0">
                <div className="w-14 h-14 sm:w-14 sm:h-14 sm:mx-auto sm:mb-3 rounded-xl bg-gold-500/10 flex items-center justify-center group-hover:bg-gold-500/20 transition-colors flex-shrink-0">
                  <Lock className="h-7 w-7 sm:h-7 sm:w-7 text-gold-400" />
                </div>
                <div className="text-left sm:text-center">
                  <div className="font-display text-2xl sm:text-2xl font-bold text-gold-400">5 Jurisdictions</div>
                  <div className="text-[15px] sm:text-sm text-foreground/70 mt-1">Multi-Location Storage</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
