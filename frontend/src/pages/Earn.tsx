import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { TrendingUp, Lock, Zap, Gift } from "lucide-react";

const earnPrograms = [
  {
    icon: TrendingUp,
    title: "Staking",
    description: "Earn rewards by staking your cryptocurrencies",
    apy: "5-12%",
    minAmount: "$100",
    features: ["Daily rewards", "Flexible lockup", "Auto-compound"],
  },
  {
    icon: Lock,
    title: "Savings",
    description: "Generate passive income on idle assets",
    apy: "3-8%",
    minAmount: "$50",
    features: ["Low risk", "Quick withdrawal", "FDIC insured"],
  },
  {
    icon: Zap,
    title: "Launchpad",
    description: "Get early access to new token launches",
    apy: "Varies",
    minAmount: "$1,000",
    features: ["Early access", "Exclusive deals", "Community voting"],
  },
  {
    icon: Gift,
    title: "Referral Program",
    description: "Earn commissions by inviting friends",
    apy: "10-15%",
    minAmount: "Free",
    features: ["Lifetime rewards", "No limits", "Instant payouts"],
  },
];

const Earn = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-24 pb-20">
        <div className="container mx-auto px-4">
          {/* Header */}
          <div className="mb-16 animate-fade-in">
            <h1 className="font-display text-4xl md:text-5xl font-bold mb-3">
              Earn <span className="text-gradient">Passive Income</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl">
              Put your crypto to work and earn rewards. Choose from staking, savings, launchpad, and referral programs.
            </p>
          </div>

          {/* Earn Programs Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
            {earnPrograms.map((program) => {
              const IconComponent = program.icon;
              return (
                <Card
                  key={program.title}
                  className="p-8 border-border/50 bg-secondary/20 backdrop-blur hover:border-primary/50 transition-colors group cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-6">
                    <div>
                      <div className="h-12 w-12 rounded-lg bg-primary/20 flex items-center justify-center mb-4 group-hover:bg-primary/30 transition-colors">
                        <IconComponent className="h-6 w-6 text-primary" />
                      </div>
                      <h3 className="font-display text-2xl font-bold mb-2">{program.title}</h3>
                      <p className="text-muted-foreground">{program.description}</p>
                    </div>
                  </div>

                  {/* APY */}
                  <div className="mb-6 p-4 bg-primary/10 rounded-lg border border-primary/20">
                    <p className="text-sm text-muted-foreground mb-1">Annual Percentage Yield</p>
                    <p className="font-display text-2xl font-bold text-primary">{program.apy}</p>
                  </div>

                  {/* Min Amount */}
                  <div className="mb-6">
                    <p className="text-sm text-muted-foreground mb-1">Minimum Amount</p>
                    <p className="font-medium">{program.minAmount}</p>
                  </div>

                  {/* Features */}
                  <div className="mb-8">
                    <p className="text-sm font-medium mb-3">Features</p>
                    <ul className="space-y-2">
                      {program.features.map((feature) => (
                        <li key={feature} className="flex items-center gap-2 text-sm text-muted-foreground">
                          <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <Button variant="hero" className="w-full">
                    Start Earning
                  </Button>
                </Card>
              );
            })}
          </div>

          {/* Info Section */}
          <Card className="p-8 border-border/50 bg-secondary/20 backdrop-blur">
            <h2 className="font-display text-2xl font-bold mb-6">How It Works</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div>
                <div className="inline-flex items-center justify-center h-10 w-10 rounded-full bg-primary/20 text-primary font-display font-bold mb-4">
                  1
                </div>
                <h3 className="font-medium mb-2">Deposit</h3>
                <p className="text-sm text-muted-foreground">
                  Choose your cryptocurrency and amount. Transfer your assets to your CryptoVault wallet.
                </p>
              </div>
              <div>
                <div className="inline-flex items-center justify-center h-10 w-10 rounded-full bg-primary/20 text-primary font-display font-bold mb-4">
                  2
                </div>
                <h3 className="font-medium mb-2">Select Program</h3>
                <p className="text-sm text-muted-foreground">
                  Pick the earning program that best fits your investment goals and risk tolerance.
                </p>
              </div>
              <div>
                <div className="inline-flex items-center justify-center h-10 w-10 rounded-full bg-primary/20 text-primary font-display font-bold mb-4">
                  3
                </div>
                <h3 className="font-medium mb-2">Earn Rewards</h3>
                <p className="text-sm text-muted-foreground">
                  Start earning rewards immediately. Watch your balance grow with daily, weekly, or monthly payouts.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Earn;
