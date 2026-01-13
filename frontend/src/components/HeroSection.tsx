import { Button } from "@/components/ui/button";
import { ArrowRight, Shield, Vault, Lock, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

const HeroSection = () => {
  const auth = useAuth();
  const user = auth?.user ?? null;
  
  return (
    <section className="relative pt-32 pb-20 overflow-hidden" data-testid="hero-section">
      {/* Background Effects - Gold themed */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-gold-500/10 rounded-full blur-3xl animate-pulse-glow" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-gold-600/10 rounded-full blur-3xl animate-pulse-glow" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gold-400/5 rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-4xl mx-auto text-center animate-fade-in">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gold-500/10 border border-gold-500/20 mb-8 backdrop-blur-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-gold-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-gold-500"></span>
            </span>
            <span className="text-sm text-gold-400/90">Institutional-Grade Security • SOC 2 in Progress</span>
          </div>

          {/* Headline - Gold gradient */}
          <h1 className="font-display text-5xl md:text-7xl font-bold mb-6 leading-tight" data-testid="hero-headline">
            Secure, Institutional-Grade
            <span className="block bg-gradient-to-r from-gold-400 via-gold-500 to-gold-600 bg-clip-text text-transparent">
              Custody for Digital Assets
            </span>
          </h1>

          {/* Subheadline */}
          <p className="text-lg md:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto" data-testid="hero-subheadline">
            CryptoVault Financial provides bank-grade custody solutions with cold storage,
            multi-signature wallets, and comprehensive compliance for individuals and institutions.
          </p>

          {/* CTAs - Gold themed */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Button 
              size="lg" 
              className="relative overflow-hidden bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold shadow-lg shadow-gold-500/25 hover:shadow-gold-500/40 transition-all duration-300 hover:scale-105 group px-8 py-6 text-base"
              asChild 
              data-testid="hero-cta-primary"
            >
              <Link to={user ? "/dashboard" : "/auth"}>
                <span className="relative z-10 flex items-center gap-2">
                  <Sparkles className="h-5 w-5" />
                  {user ? "Go to Dashboard" : "Get Started"}
                  <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
                </span>
                <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform duration-700" />
              </Link>
            </Button>
            <Button 
              variant="outline" 
              size="lg"
              className="border-gold-500/30 hover:border-gold-400 hover:bg-gold-500/10 hover:text-gold-400 transition-all duration-300 px-8 py-6 text-base"
              asChild 
              data-testid="hero-cta-secondary"
            >
              <Link to="/services">
                Explore Services
              </Link>
            </Button>
          </div>

          {/* Trust Indicators - Gold accents */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            <div className="glass-card p-6 animate-slide-up border border-gold-500/10 hover:border-gold-500/30 transition-all duration-300 group" style={{ animationDelay: '0.1s' }} data-testid="trust-indicator-1">
              <div className="w-14 h-14 mx-auto mb-3 rounded-xl bg-gold-500/10 flex items-center justify-center group-hover:bg-gold-500/20 transition-colors">
                <Vault className="h-7 w-7 text-gold-400" />
              </div>
              <div className="font-display text-2xl font-bold text-gold-400">95%+</div>
              <div className="text-sm text-muted-foreground">Cold Storage</div>
            </div>
            <div className="glass-card p-6 animate-slide-up border border-gold-500/10 hover:border-gold-500/30 transition-all duration-300 group" style={{ animationDelay: '0.2s' }} data-testid="trust-indicator-2">
              <div className="w-14 h-14 mx-auto mb-3 rounded-xl bg-gold-500/10 flex items-center justify-center group-hover:bg-gold-500/20 transition-colors">
                <Lock className="h-7 w-7 text-gold-400" />
              </div>
              <div className="font-display text-2xl font-bold text-gold-400">Multi-Sig</div>
              <div className="text-sm text-muted-foreground">2-of-3, 3-of-5 Support</div>
            </div>
            <div className="glass-card p-6 animate-slide-up border border-gold-500/10 hover:border-gold-500/30 transition-all duration-300 group" style={{ animationDelay: '0.3s' }} data-testid="trust-indicator-3">
              <div className="w-14 h-14 mx-auto mb-3 rounded-xl bg-gold-500/10 flex items-center justify-center group-hover:bg-gold-500/20 transition-colors">
                <Shield className="h-7 w-7 text-gold-400" />
              </div>
              <div className="font-display text-2xl font-bold text-gold-400">$500M</div>
              <div className="text-sm text-muted-foreground">Insurance Coverage</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
