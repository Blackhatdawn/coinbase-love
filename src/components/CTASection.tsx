import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

const CTASection = () => {
  return (
    <section className="py-24 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-accent/10 rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-8">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-sm text-primary font-medium">New users get $10 in free crypto</span>
          </div>

          <h2 className="font-display text-4xl md:text-5xl font-bold mb-6">
            Ready to Start Your
            <span className="block text-gradient">Crypto Journey?</span>
          </h2>

          <p className="text-lg text-muted-foreground mb-10 max-w-xl mx-auto">
            Join millions of users worldwide. Sign up in minutes and start trading today. No hidden fees, no surprises.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="hero" size="xl" className="group">
              Create Free Account
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
            </Button>
            <Button variant="outline" size="xl">
              Contact Sales
            </Button>
          </div>

          {/* Trust Badges */}
          <div className="flex flex-wrap items-center justify-center gap-8 mt-14 opacity-60">
            <div className="text-sm text-muted-foreground">Trusted by:</div>
            <div className="font-display font-semibold text-lg">Forbes</div>
            <div className="font-display font-semibold text-lg">TechCrunch</div>
            <div className="font-display font-semibold text-lg">Bloomberg</div>
            <div className="font-display font-semibold text-lg">CNBC</div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTASection;
