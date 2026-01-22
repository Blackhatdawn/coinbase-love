import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import {
  Vault,
  KeyRound,
  TrendingUp,
  PieChart,
  Building,
  ArrowRight,
  Check,
  Shield
} from "lucide-react";

const services = [
  {
    icon: Vault,
    title: "Cold Storage Vaults",
    description: "Air-gapped, multi-signature cold storage with HSM-backed key management. Your assets are stored offline in geographically distributed secure facilities.",
    features: [
      "95%+ assets in offline cold storage",
      "Hardware Security Modules (HSM)",
      "Geographically distributed vaults",
      "Insurance coverage up to $500M"
    ]
  },
  {
    icon: KeyRound,
    title: "Multi-Signature Wallets",
    description: "Enterprise-grade multi-sig solutions supporting 2-of-3, 3-of-5, or custom configurations for maximum security and flexibility.",
    features: [
      "Customizable signing thresholds",
      "Time-locked transactions",
      "Whitelist-only withdrawals",
      "Hardware wallet integration"
    ]
  },
  {
    icon: TrendingUp,
    title: "Staking-as-a-Service",
    description: "Earn competitive yields on your crypto holdings through our secure staking infrastructure. Non-custodial options available.",
    features: [
      "Competitive APY rates",
      "Auto-compounding rewards",
      "Flexible lock-up periods",
      "Real-time rewards tracking"
    ]
  },
  {
    icon: PieChart,
    title: "Portfolio Management",
    description: "Comprehensive portfolio tracking with real-time valuations, performance analytics, and tax reporting tools.",
    features: [
      "Real-time portfolio tracking",
      "Performance analytics",
      "Tax reporting (CSV export)",
      "Multi-wallet aggregation"
    ]
  },
  {
    icon: Building,
    title: "Institutional OTC",
    description: "High-volume OTC trading desk for institutional clients. Deep liquidity, competitive rates, and dedicated account management.",
    features: [
      "$100K+ minimum trades",
      "Deep liquidity pools",
      "Competitive spreads",
      "Dedicated account manager"
    ]
  }
];

const Services = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-20 sm:pt-24">
        {/* Hero */}
        <section className="section-padding bg-gradient-to-b from-secondary/30 to-background">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-6">
                <Shield className="h-4 w-4 text-primary" />
                <span className="text-sm text-primary font-medium">Institutional-Grade Services</span>
              </div>
              <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold mb-6">
                Secure Digital Asset <span className="text-gradient">Custody Services</span>
              </h1>
              <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto mb-8">
                From cold storage to staking, we provide comprehensive custody solutions
                for individuals and institutions managing digital assets.
              </p>
              <Button variant="hero" size="xl" asChild>
                <Link to="/contact">
                  Contact Sales
                  <ArrowRight className="h-5 w-5 ml-2" />
                </Link>
              </Button>
            </div>
          </div>
        </section>

        {/* Services Grid */}
        <section className="section-padding">
          <div className="container mx-auto px-4">
            <div className="space-y-12">
              {services.map((service, index) => (
                <div
                  key={service.title}
                  className={`grid md:grid-cols-2 gap-8 sm:gap-12 items-center ${index % 2 === 1 ? 'md:flex-row-reverse' : ''}`}
                  data-testid={`service-${service.title.toLowerCase().replace(/\s+/g, '-')}`}
                >
                  <div className={index % 2 === 1 ? 'md:order-2' : ''}>
                    <div className="w-14 h-14 sm:w-16 sm:h-16 lg:w-20 lg:h-20 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center mb-6">
                      <service.icon className="h-7 w-7 sm:h-9 sm:w-9 text-primary" />
                    </div>
                    <h2 className="font-display text-xl sm:text-2xl md:text-3xl font-bold mb-4">
                      {service.title}
                    </h2>
                    <p className="text-muted-foreground mb-5 leading-relaxed">
                      {service.description}
                    </p>
                    <ul className="space-y-3">
                      {service.features.map((feature) => (
                        <li key={feature} className="flex items-center gap-3">
                          <div className="w-5 h-5 rounded-full bg-success/20 flex items-center justify-center flex-shrink-0">
                            <Check className="h-3 w-3 text-success" />
                          </div>
                          <span className="text-sm text-muted-foreground">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className={`glass-card p-8 sm:p-10 ${index % 2 === 1 ? 'md:order-1' : ''}`}>
                    <div className="aspect-square rounded-xl bg-gradient-to-br from-primary/10 to-accent/10 flex items-center justify-center">
                      <service.icon className="h-20 w-20 sm:h-24 sm:w-24 lg:h-32 lg:w-32 text-primary/30" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Pricing Tiers */}
        <section className="section-padding bg-secondary/20">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center mb-10 sm:mb-12">
              <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-bold mb-4">
                Pricing Tiers
              </h2>
              <p className="text-muted-foreground">
                Flexible plans for every level of digital asset management
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6 sm:gap-8 max-w-5xl mx-auto">
              {/* Free Tier */}
              <div className="glass-card p-6 sm:p-8" data-testid="pricing-free">
                <h3 className="font-display text-xl font-semibold mb-2">Free</h3>
                <div className="text-3xl font-bold mb-4">$0<span className="text-sm text-muted-foreground font-normal">/mo</span></div>
                <p className="text-muted-foreground text-sm mb-6">Perfect for getting started</p>
                <ul className="space-y-3 mb-8">
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-success" /> Portfolio tracking
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-success" /> Basic wallet support
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-success" /> Email support
                  </li>
                </ul>
                <Button variant="outline" className="w-full" asChild>
                  <Link to="/auth">Get Started</Link>
                </Button>
              </div>

              {/* Premium Tier */}
              <div className="glass-card p-6 sm:p-8 border-primary/50 relative" data-testid="pricing-premium">
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-primary text-primary-foreground text-xs font-semibold rounded-full">
                  Most Popular
                </div>
                <h3 className="font-display text-xl font-semibold mb-2">Premium</h3>
                <div className="text-3xl font-bold mb-4">$10-50<span className="text-sm text-muted-foreground font-normal">/mo</span></div>
                <p className="text-muted-foreground text-sm mb-6">For active traders</p>
                <ul className="space-y-3 mb-8">
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-success" /> Everything in Free
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-success" /> Multi-sig wallets
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-success" /> Staking access
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-success" /> Priority support
                  </li>
                </ul>
                <Button variant="gradient" className="w-full" asChild>
                  <Link to="/auth">Upgrade Now</Link>
                </Button>
              </div>

              {/* Institutional */}
              <div className="glass-card p-6 sm:p-8" data-testid="pricing-institutional">
                <h3 className="font-display text-xl font-semibold mb-2">Institutional</h3>
                <div className="text-3xl font-bold mb-4">0.1-0.5%<span className="text-sm text-muted-foreground font-normal"> AUM</span></div>
                <p className="text-muted-foreground text-sm mb-6">For enterprises & funds</p>
                <ul className="space-y-3 mb-8">
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-success" /> Everything in Premium
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-success" /> Dedicated custody
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-success" /> OTC desk access
                  </li>
                  <li className="flex items-center gap-2 text-sm">
                    <Check className="h-4 w-4 text-success" /> 24/7 support
                  </li>
                </ul>
                <Button variant="outline" className="w-full" asChild>
                  <Link to="/contact">Contact Sales</Link>
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Supported Assets */}
        <section className="py-20">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <h2 className="font-display text-3xl font-bold mb-6">Supported Assets</h2>
              <p className="text-muted-foreground mb-8">
                Secure custody for leading cryptocurrencies and tokens
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                {['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'AAVE'].map((asset) => (
                  <div
                    key={asset}
                    className="px-6 py-3 rounded-lg bg-secondary/50 border border-border/50 font-mono text-sm"
                  >
                    {asset}
                  </div>
                ))}
                <div className="px-6 py-3 rounded-lg bg-primary/10 border border-primary/20 text-primary font-mono text-sm">
                  + ERC-20s
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Services;
