import { Shield, Zap, Lock, CreditCard, Globe, BarChart3 } from "lucide-react";

const features = [
  {
    icon: Shield,
    title: "Bank-Grade Security",
    description: "Your assets are protected with military-grade encryption and cold storage solutions."
  },
  {
    icon: Zap,
    title: "Lightning Fast",
    description: "Execute trades in milliseconds with our high-performance matching engine."
  },
  {
    icon: Lock,
    title: "Insurance Protected",
    description: "$500M insurance fund to protect your digital assets against security breaches."
  },
  {
    icon: CreditCard,
    title: "Instant Buy/Sell",
    description: "Connect your bank or card to instantly buy and sell cryptocurrency."
  },
  {
    icon: Globe,
    title: "Global Access",
    description: "Trade from anywhere in the world with support for 100+ countries."
  },
  {
    icon: BarChart3,
    title: "Advanced Analytics",
    description: "Professional charting tools and real-time market data at your fingertips."
  }
];

const FeaturesSection = () => {
  return (
    <section className="py-20 bg-secondary/20">
      <div className="container mx-auto px-4">
        <div className="text-center mb-14">
          <h2 className="font-display text-3xl md:text-4xl font-bold mb-3">
            Why Choose <span className="text-gradient">CryptoVault</span>?
          </h2>
          <p className="text-muted-foreground max-w-xl mx-auto">
            Industry-leading platform trusted by millions. Built for beginners and pros alike.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div 
              key={feature.title}
              className="group glass-card p-6 hover:border-primary/50 transition-all duration-300 animate-slide-up"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <feature.icon className="h-6 w-6 text-primary" />
              </div>
              <h3 className="font-display text-xl font-semibold mb-2 group-hover:text-primary transition-colors">
                {feature.title}
              </h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
