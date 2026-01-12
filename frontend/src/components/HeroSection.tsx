import { Button } from "@/components/ui/button";
import { ArrowRight, Shield, Vault, Lock } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

const HeroSection = () => {
  const auth = useAuth();
  const user = auth?.user ?? null;
  
  return (
    <section className="relative pt-32 pb-20 overflow-hidden" data-testid="hero-section">
      {/* Background Effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl animate-pulse-glow" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent/20 rounded-full blur-3xl animate-pulse-glow" style={{ animationDelay: '1s' }} />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-4xl mx-auto text-center animate-fade-in">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary/50 border border-border/50 mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
            </span>
            <span className="text-sm text-muted-foreground">Institutional-Grade Security • SOC 2 in Progress</span>
          </div>

          {/* Headline - Updated to match specs */}
          <h1 className="font-display text-5xl md:text-7xl font-bold mb-6 leading-tight" data-testid="hero-headline">
            Secure, Institutional-Grade
            <span className="block text-gradient">Custody for Digital Assets</span>
          </h1>

          {/* Subheadline */}
          <p className="text-lg md:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto" data-testid="hero-subheadline">
            CryptoVault Financial provides bank-grade custody solutions with cold storage,
            multi-signature wallets, and comprehensive compliance for individuals and institutions.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Button variant="hero" size="xl" className="group" asChild data-testid="hero-cta-primary">
              <Link to={user ? "/dashboard" : "/auth"}>
                {user ? "Go to Dashboard" : "Get Started"}
                <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
            <Button variant="outline" size="xl" asChild data-testid="hero-cta-secondary">
              <Link to="/services">
                Explore Services
              </Link>
            </Button>
          </div>

          {/* Trust Indicators */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            <div className="glass-card p-6 animate-slide-up" style={{ animationDelay: '0.1s' }} data-testid="trust-indicator-1">
              <Vault className="h-8 w-8 text-primary mb-3 mx-auto" />
              <div className="font-display text-2xl font-bold">95%+</div>
              <div className="text-sm text-muted-foreground">Cold Storage</div>
            </div>
            <div className="glass-card p-6 animate-slide-up" style={{ animationDelay: '0.2s' }} data-testid="trust-indicator-2">
              <Lock className="h-8 w-8 text-primary mb-3 mx-auto" />
              <div className="font-display text-2xl font-bold">Multi-Sig</div>
              <div className="text-sm text-muted-foreground">2-of-3, 3-of-5 Support</div>
            </div>
            <div className="glass-card p-6 animate-slide-up" style={{ animationDelay: '0.3s' }} data-testid="trust-indicator-3">
              <Shield className="h-8 w-8 text-primary mb-3 mx-auto" />
              <div className="font-display text-2xl font-bold">$500M</div>
              <div className="text-sm text-muted-foreground">Insurance Coverage</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
