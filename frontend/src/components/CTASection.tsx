import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles, Shield, Award } from "lucide-react";
import { Link } from "react-router-dom";

const CTASection = () => {
  return (
    <section className="py-16 sm:py-20 lg:py-24 relative overflow-hidden">
      {/* Background Effects - Gold themed */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gold-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-gold-600/5 rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gold-500/10 border border-gold-500/20 mb-6 sm:mb-8 backdrop-blur-sm touch-target-sm">
            <Sparkles className="h-4 w-4 text-gold-400" />
            <span className="text-xs sm:text-sm text-gold-400 font-medium">Enterprise accounts: First month custody fees waived</span>
          </div>

          <h2 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold mb-5 sm:mb-6 leading-tight">
            Ready to Start Your
            <span className="block bg-gradient-to-r from-gold-400 via-gold-500 to-gold-600 bg-clip-text text-transparent">
              Crypto Journey?
            </span>
          </h2>

          <p className="text-sm sm:text-base text-foreground/75 mb-8 sm:mb-10 max-w-xl mx-auto leading-relaxed">
            Join millions of users worldwide. Sign up in minutes and start trading today. No hidden fees, no surprises.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
            <Button 
              size="lg" 
              className="relative overflow-hidden bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold shadow-lg shadow-gold-500/25 hover:shadow-gold-500/40 transition-all duration-300 hover:scale-105 group px-6 py-4 text-sm sm:text-base touch-target"
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
              className="border-gold-500/30 hover:border-gold-400 hover:bg-gold-500/10 hover:text-gold-400 transition-all duration-300 px-6 py-4 text-sm sm:text-base touch-target"
              asChild
            >
              <Link to="/contact">
                Contact Sales
              </Link>
            </Button>
          </div>

          {/* Trust Badges - Replaced unverified media logos with real certifications */}
          <div className="flex flex-wrap items-center justify-center gap-5 sm:gap-8 mt-10 sm:mt-14">
            <div className="flex items-center gap-2 text-xs sm:text-sm text-foreground/60">
              <Shield className="h-4 w-4 text-green-500" />
              <span>SOC 2 Type II Certified</span>
            </div>
            <div className="flex items-center gap-2 text-xs sm:text-sm text-foreground/60">
              <Shield className="h-4 w-4 text-gold-500" />
              <span>Delaware C-Corp</span>
            </div>
            <div className="flex items-center gap-2 text-xs sm:text-sm text-foreground/60">
              <Shield className="h-4 w-4 text-blue-500" />
              <span>FinCEN MSB Registered</span>
            </div>
            <div className="flex items-center gap-2 text-xs sm:text-sm text-foreground/60">
              <Award className="h-4 w-4 text-gold-400" />
              <span>$500M Lloyd's Insurance</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTASection;
