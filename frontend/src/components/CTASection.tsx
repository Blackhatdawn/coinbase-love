import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

const CTASection = () => {
  return (
    <section className="py-24 relative overflow-hidden">
      {/* Background Effects - Gold themed */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gold-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-gold-600/5 rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gold-500/10 border border-gold-500/20 mb-8 backdrop-blur-sm">
            <Sparkles className="h-4 w-4 text-gold-400" />
            <span className="text-sm text-gold-400 font-medium">New users get $10 in free crypto</span>
          </div>

          <h2 className="font-display text-4xl md:text-5xl font-bold mb-6">
            Ready to Start Your
            <span className="block bg-gradient-to-r from-gold-400 via-gold-500 to-gold-600 bg-clip-text text-transparent">
              Crypto Journey?
            </span>
          </h2>

          <p className="text-lg text-muted-foreground mb-10 max-w-xl mx-auto">
            Join millions of users worldwide. Sign up in minutes and start trading today. No hidden fees, no surprises.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button 
              size="lg" 
              className="relative overflow-hidden bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold shadow-lg shadow-gold-500/25 hover:shadow-gold-500/40 transition-all duration-300 hover:scale-105 group px-8 py-6 text-base"
              asChild
            >
              <Link to="/auth">
                <span className="relative z-10 flex items-center gap-2">
                  Create Free Account
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
            >
              <Link to="/contact">
                Contact Sales
              </Link>
            </Button>
          </div>

          {/* Trust Badges */}
          <div className="flex flex-wrap items-center justify-center gap-8 mt-14 opacity-60">
            <div className="text-sm text-muted-foreground">Trusted by:</div>
            <div className="font-display font-semibold text-lg text-gold-400/80">Forbes</div>
            <div className="font-display font-semibold text-lg text-gold-400/80">TechCrunch</div>
            <div className="font-display font-semibold text-lg text-gold-400/80">Bloomberg</div>
            <div className="font-display font-semibold text-lg text-gold-400/80">CNBC</div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTASection;
