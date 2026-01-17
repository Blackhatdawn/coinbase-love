/**
 * Social Proof Section - Testimonials & Trust Stats
 */
import { Star, Shield, Clock, Users, DollarSign, Award } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Testimonial {
  id: number;
  name: string;
  role: string;
  avatar: string;
  content: string;
  rating: number;
}

const testimonials: Testimonial[] = [
  {
    id: 1,
    name: "Michael Chen",
    role: "Director of Digital Assets",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Michael",
    content: "Migrated $50M from a competitor to CryptoVault. The multi-jurisdiction storage and real-time proof of reserves gave our board the confidence they needed. Setup took 2 hours, not 2 weeks.",
    rating: 5
  },
  {
    id: 2,
    name: "Sarah Williams",
    role: "CTO, Blockchain Capital",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah",
    content: "We evaluated 8 custody providers. CryptoVault's transparent fee structure and SOC 2 compliance made them stand out. Their support team actually understands institutional requirements.",
    rating: 5
  },
  {
    id: 3,
    name: "James Rodriguez",
    role: "CFO, Digital Ventures",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=James",
    content: "The dedicated account manager and quarterly security audits justify the premium. We sleep better knowing our treasury is protected by multi-sig and cold storage across 5 jurisdictions.",
    rating: 5
  },
  {
    id: 4,
    name: "Emily Zhang",
    role: "Head of Risk, Quantum Capital",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Emily",
    content: "Their insurance coverage through Lloyd's of London and zero security breaches since launch were decisive factors. Real-time reporting integrates perfectly with our risk management systems.",
    rating: 5
  }
];

const stats = [
  { 
    icon: Shield, 
    value: "$10.2B", 
    label: "Assets Under Custody",
    sublabel: "Updated Jan 2026",
    verified: true
  },
  { 
    icon: Clock, 
    value: "99.997%", 
    label: "Uptime",
    sublabel: "Since Jan 2019",
    verified: true
  },
  { 
    icon: Users, 
    value: "250+", 
    label: "Institutions",
    sublabel: "Family offices & funds",
    verified: true
  },
  { 
    icon: Award, 
    value: "Zero", 
    label: "Security Breaches",
    sublabel: "Since launch 2019",
    verified: true
  }
];

const TestimonialCard = ({ testimonial }: { testimonial: Testimonial }) => (
  <div 
    className="glass-card p-5 sm:p-6 rounded-xl border border-gold-500/10 hover:border-gold-500/30 transition-all duration-300 h-full flex flex-col"
    data-testid={`testimonial-${testimonial.id}`}
  >
    {/* Rating Stars */}
    <div className="flex gap-1 mb-4">
      {Array.from({ length: testimonial.rating }).map((_, i) => (
        <Star key={i} className="h-4 w-4 fill-gold-400 text-gold-400" />
      ))}
    </div>
    
    {/* Content */}
    <p className="text-sm sm:text-base text-muted-foreground mb-6 flex-1 leading-relaxed">
      "{testimonial.content}"
    </p>
    
    {/* Author */}
    <div className="flex items-center gap-3 pt-4 border-t border-border/30">
      <img 
        src={testimonial.avatar} 
        alt={testimonial.name}
        className="h-10 w-10 rounded-full bg-gold-500/20"
      />
      <div className="flex-1">
        <div className="font-semibold text-sm flex items-center gap-2">
          {testimonial.name}
          <span className="inline-flex items-center justify-center h-4 w-4 rounded-full bg-blue-500/20 border border-blue-500/50">
            <svg className="h-2.5 w-2.5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
            </svg>
          </span>
        </div>
        <div className="text-xs text-muted-foreground">{testimonial.role}</div>
      </div>
    </div>
  </div>
);

const StatCard = ({ stat }: { stat: typeof stats[0] }) => (
  <div 
    className="text-center p-4 sm:p-6"
    data-testid={`stat-${stat.label.toLowerCase().replace(' ', '-')}`}
  >
    <div className="inline-flex items-center justify-center h-12 w-12 sm:h-14 sm:w-14 rounded-xl bg-gold-500/10 mb-3 sm:mb-4 mx-auto">
      <stat.icon className="h-6 w-6 sm:h-7 sm:w-7 text-gold-400" />
    </div>
    <div className="font-display text-2xl sm:text-3xl lg:text-4xl font-bold text-gold-400 mb-1">
      {stat.value}
    </div>
    <div className="text-sm sm:text-base font-medium text-foreground mb-0.5">
      {stat.label}
    </div>
    <div className="text-xs text-muted-foreground">
      {stat.sublabel}
    </div>
  </div>
);

const SocialProofSection = () => {
  return (
    <section className="py-16 sm:py-20 lg:py-24 relative overflow-hidden" data-testid="social-proof-section">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-gold-500/5 to-transparent pointer-events-none" />
      
      <div className="container mx-auto px-4 sm:px-6 relative z-10">
        {/* Stats Row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-16 sm:mb-20">
          {stats.map((stat, index) => (
            <div 
              key={stat.label}
              className="glass-card rounded-xl border border-gold-500/10 hover:border-gold-500/20 transition-all duration-300"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <StatCard stat={stat} />
            </div>
          ))}
        </div>

        {/* Section Header */}
        <div className="text-center mb-10 sm:mb-12">
          <h2 className="font-display text-2xl sm:text-3xl lg:text-4xl font-bold mb-3">
            Trusted by <span className="text-gradient">Professionals</span>
          </h2>
          <p className="text-muted-foreground text-sm sm:text-base max-w-2xl mx-auto">
            Join thousands of traders and institutions who trust CryptoVault for their digital asset needs.
          </p>
        </div>

        {/* Testimonials Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          {testimonials.map((testimonial, index) => (
            <div 
              key={testimonial.id}
              className="animate-fade-in"
              style={{ animationDelay: `${index * 150}ms` }}
            >
              <TestimonialCard testimonial={testimonial} />
            </div>
          ))}
        </div>

        {/* Trust Badges */}
        <div className="mt-12 sm:mt-16 flex flex-wrap items-center justify-center gap-6 sm:gap-8 opacity-60">
          <div className="flex items-center gap-2 text-xs sm:text-sm text-muted-foreground">
            <Shield className="h-4 w-4" />
            <span>SOC 2 Compliant</span>
          </div>
          <div className="flex items-center gap-2 text-xs sm:text-sm text-muted-foreground">
            <DollarSign className="h-4 w-4" />
            <span>$500M Insurance</span>
          </div>
          <div className="flex items-center gap-2 text-xs sm:text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>24/7 Support</span>
          </div>
        </div>
      </div>
    </section>
  );
};

export default SocialProofSection;
