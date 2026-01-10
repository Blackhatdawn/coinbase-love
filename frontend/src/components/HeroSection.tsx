import { Button } from "@/components/ui/button";
import { ArrowRight, Shield, Zap, Globe } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

const HeroSection = () => {
  const auth = useAuth();
  const user = auth?.user ?? null;
  return (
    <section className="relative pt-32 pb-20 overflow-hidden">
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
            <span className="text-sm text-muted-foreground">Live Markets • 24/7 Trading</span>
          </div>

          {/* Headline */}
          <h1 className="font-display text-5xl md:text-7xl font-bold mb-6 leading-tight">
            The Future of
            <span className="block text-gradient">Digital Finance</span>
          </h1>

          {/* Subheadline */}
          <p className="text-lg md:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto">
            Buy, sell, and trade 200+ cryptocurrencies with industry-leading security. 
            Join 50+ million users trusting CryptoVault worldwide.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Button variant="hero" size="xl" className="group" asChild>
              <Link to={user ? "/dashboard" : "/auth"}>
                Start Trading Now
                <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
            <Button variant="outline" size="xl" asChild>
              <Link to="/markets">
                View Markets
              </Link>
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            <div className="glass-card p-6 animate-slide-up" style={{ animationDelay: '0.1s' }}>
              <Shield className="h-8 w-8 text-primary mb-3 mx-auto" />
              <div className="font-display text-2xl font-bold">$12B+</div>
              <div className="text-sm text-muted-foreground">Assets Protected</div>
            </div>
            <div className="glass-card p-6 animate-slide-up" style={{ animationDelay: '0.2s' }}>
              <Globe className="h-8 w-8 text-primary mb-3 mx-auto" />
              <div className="font-display text-2xl font-bold">100+</div>
              <div className="text-sm text-muted-foreground">Countries Supported</div>
            </div>
            <div className="glass-card p-6 animate-slide-up" style={{ animationDelay: '0.3s' }}>
              <Zap className="h-8 w-8 text-primary mb-3 mx-auto" />
              <div className="font-display text-2xl font-bold">0.1s</div>
              <div className="text-sm text-muted-foreground">Execution Speed</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
