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
          {/* Badge with improved design */}
          <div className="inline-flex items-center gap-2.5 px-5 py-2.5 rounded-full bg-gradient-to-r from-gold-500/10 via-gold-500/5 to-gold-500/10 border border-gold-500/30 mb-8 backdrop-blur-sm hover:border-gold-400/50 transition-all duration-300 group cursor-default">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-gold-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-gold-500 shadow-[0_0_10px_rgba(251,191,36,0.5)]"></span>
            </span>
            <span className="text-sm font-semibold text-gold-400 font-mono tracking-wide">
              TRUSTED BY 250+ INSTITUTIONS GLOBALLY
            </span>
          </div>

          {/* Headline - Enhanced with better hierarchy */}
          <h1 className="font-display text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-black mb-6 leading-[1.1] tracking-tight" data-testid="hero-headline">
            <span className="block text-foreground mb-2">
              Institutional-Grade
            </span>
            <span className="block bg-gradient-to-r from-gold-300 via-gold-400 to-gold-500 bg-clip-text text-transparent drop-shadow-[0_0_30px_rgba(251,191,36,0.3)]">
              Digital Asset Custody
            </span>
          </h1>

          {/* Subheadline - More impactful */}
          <p className="text-lg sm:text-xl md:text-2xl text-foreground/90 mb-10 max-w-3xl mx-auto px-4 leading-relaxed font-light" data-testid="hero-subheadline">
            Multi-jurisdiction cold storage • Real-time proof of reserves • Zero breaches since 2019
            <span className="block mt-3 text-gold-400/80 text-base sm:text-lg font-medium">
              $10.2B+ in assets secured for family offices, hedge funds, and enterprises worldwide
            </span>
          </p>

          {/* CTAs - Enhanced with better styling and animations */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16 px-4">
            <Button 
              size="lg" 
              className="relative overflow-hidden bg-gradient-to-r from-gold-400 via-gold-500 to-gold-600 hover:from-gold-300 hover:via-gold-400 hover:to-gold-500 text-black font-bold shadow-xl shadow-gold-500/30 hover:shadow-gold-500/50 transition-all duration-300 hover:scale-105 group h-14 sm:h-16 px-8 sm:px-10 text-base sm:text-lg"
              asChild 
              data-testid="hero-cta-primary"
            >
              <Link to={user ? "/dashboard" : "/auth"}>
                <span className="relative z-10 flex items-center gap-2.5">
                  <Sparkles className="h-5 w-5 sm:h-6 sm:w-6 group-hover:rotate-12 transition-transform" />
                  <span className="font-mono tracking-wide">{user ? "GO TO DASHBOARD" : "GET STARTED FREE"}</span>
                  <ArrowRight className="h-5 w-5 sm:h-6 sm:w-6 transition-transform group-hover:translate-x-2" />
                </span>
                <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full bg-gradient-to-r from-transparent via-white/30 to-transparent transition-transform duration-700" />
              </Link>
            </Button>
            <Button 
              variant="outline" 
              size="lg"
              className="border-2 border-gold-500/30 hover:border-gold-400 hover:bg-gold-500/10 hover:text-gold-400 transition-all duration-300 backdrop-blur-sm h-14 sm:h-16 px-8 sm:px-10 text-base sm:text-lg font-semibold hover:scale-105"
              asChild 
              data-testid="hero-cta-secondary"
            >
              <Link to="/services">
                <span className="font-mono tracking-wide">EXPLORE SERVICES</span>
              </Link>
            </Button>
          </div>

          {/* Trust Indicators - Enhanced cards with better visual hierarchy */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-4xl mx-auto px-4">
            <div className="glass-card p-6 sm:p-8 animate-slide-up border-2 border-gold-500/20 hover:border-gold-400/40 transition-all duration-300 group hover:shadow-xl hover:shadow-gold-500/10 hover:-translate-y-1" style={{ animationDelay: '0.1s' }} data-testid="trust-indicator-1">
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 sm:w-18 sm:h-18 mb-4 rounded-2xl bg-gradient-to-br from-gold-500/20 to-gold-600/10 flex items-center justify-center group-hover:from-gold-500/30 group-hover:to-gold-600/20 transition-all duration-300 shadow-lg shadow-gold-500/20">
                  <Shield className="h-8 w-8 sm:h-9 sm:w-9 text-gold-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.5)]" />
                </div>
                <div className="font-display text-3xl sm:text-4xl font-black text-gold-400 mb-2">ZERO</div>
                <div className="text-sm sm:text-base text-foreground/80 font-medium">Security Breaches</div>
                <div className="text-xs text-muted-foreground mt-1 font-mono">Since 2019</div>
              </div>
            </div>
            <div className="glass-card p-6 sm:p-8 animate-slide-up border-2 border-gold-500/20 hover:border-gold-400/40 transition-all duration-300 group hover:shadow-xl hover:shadow-gold-500/10 hover:-translate-y-1" style={{ animationDelay: '0.2s' }} data-testid="trust-indicator-2">
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 sm:w-18 sm:h-18 mb-4 rounded-2xl bg-gradient-to-br from-gold-500/20 to-gold-600/10 flex items-center justify-center group-hover:from-gold-500/30 group-hover:to-gold-600/20 transition-all duration-300 shadow-lg shadow-gold-500/20">
                  <Vault className="h-8 w-8 sm:h-9 sm:w-9 text-gold-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.5)]" />
                </div>
                <div className="font-display text-3xl sm:text-4xl font-black text-gold-400 mb-2">$10.2B+</div>
                <div className="text-sm sm:text-base text-foreground/80 font-medium">Assets Under Custody</div>
                <div className="text-xs text-muted-foreground mt-1 font-mono">Globally Secured</div>
              </div>
            </div>
            <div className="glass-card p-6 sm:p-8 animate-slide-up border-2 border-gold-500/20 hover:border-gold-400/40 transition-all duration-300 group hover:shadow-xl hover:shadow-gold-500/10 hover:-translate-y-1" style={{ animationDelay: '0.3s' }} data-testid="trust-indicator-3">
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 sm:w-18 sm:h-18 mb-4 rounded-2xl bg-gradient-to-br from-gold-500/20 to-gold-600/10 flex items-center justify-center group-hover:from-gold-500/30 group-hover:to-gold-600/20 transition-all duration-300 shadow-lg shadow-gold-500/20">
                  <Lock className="h-8 w-8 sm:h-9 sm:w-9 text-gold-400 drop-shadow-[0_0_8px_rgba(251,191,36,0.5)]" />
                </div>
                <div className="font-display text-3xl sm:text-4xl font-black text-gold-400 mb-2">5</div>
                <div className="text-sm sm:text-base text-foreground/80 font-medium">Jurisdictions</div>
                <div className="text-xs text-muted-foreground mt-1 font-mono">Multi-Location Storage</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
