/**
 * FAQ Section - Frequently Asked Questions
 * Addresses common questions about custody, security, and services
 */
import { HelpCircle, ChevronDown } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { resolveSupportEmail } from '@/lib/runtimeConfig';

interface FAQItem {
  id: number;
  question: string;
  answer: string;
  category: 'security' | 'custody' | 'pricing' | 'compliance' | 'general';
}

const faqs: FAQItem[] = [
  {
    id: 1,
    category: 'security',
    question: "How is CryptoVault different from Coinbase Custody or other providers?",
    answer: "CryptoVault offers multi-jurisdiction storage across 5 countries (US, Switzerland, Singapore, UK, Cayman Islands), real-time on-chain proof of reserves updated daily, and lower custody fees (0.15% vs industry average 0.25%). We've maintained zero security breaches since 2019 and provide dedicated relationship managers for accounts over $1M."
  },
  {
    id: 2,
    category: 'custody',
    question: "What is the minimum to open an institutional custody account?",
    answer: "Individual accounts require a minimum of $10,000 USD. Institutional accounts (family offices, hedge funds, corporations) require a minimum of $500,000 USD to qualify for dedicated support and reduced fee tiers."
  },
  {
    id: 3,
    category: 'security',
    question: "How quickly can I withdraw my assets?",
    answer: "Hot wallet withdrawals (5% of holdings) are processed instantly. Cold storage withdrawals typically take 24-48 hours to complete security audits and multi-sig approvals. This delay is intentional and ensures proper authorization before moving large amounts from cold storage."
  },
  {
    id: 4,
    category: 'custody',
    question: "What cryptocurrencies do you support for custody?",
    answer: "We support 50+ major cryptocurrencies including Bitcoin, Ethereum, and major ERC-20 tokens. Full asset list available in your dashboard. We regularly add support for new assets based on institutional demand and security audits."
  },
  {
    id: 5,
    category: 'security',
    question: "How do you store assets securely? What is cold storage?",
    answer: "95% of assets are stored in cold storage - offline Hardware Security Modules (HSMs) located in geographically distributed, climate-controlled vaults with 24/7 armed security. Private keys never touch internet-connected devices. The remaining 5% is kept in hot wallets for instant withdrawal requests."
  },
  {
    id: 6,
    category: 'pricing',
    question: "What are your custody fees?",
    answer: "Standard custody fee is 0.15% annually (prorated monthly). Enterprise accounts ($10M+) receive custom pricing. Setup fee is $2,500 (waived for first month). No withdrawal fees for standard processing. Expedited withdrawals: 0.1% fee."
  },
  {
    id: 7,
    category: 'compliance',
    question: "Are you regulated? What licenses do you hold?",
    answer: "CryptoVault Financial is a Delaware C-Corporation registered with FinCEN as a Money Service Business (MSB). We are SOC 2 Type II certified, maintain $500M in custody insurance through Lloyd's of London, and comply with AML/KYC regulations in all operating jurisdictions."
  },
  {
    id: 8,
    category: 'security',
    question: "What happens if CryptoVault gets hacked or goes bankrupt?",
    answer: "Our assets are stored in segregated cold storage with multi-sig control - we cannot access your funds unilaterally. In the unlikely event of bankruptcy, your assets are not part of our balance sheet and would be returned to you. Additionally, our $500M Lloyd's of London insurance policy covers losses from security breaches, employee theft, and operational failures."
  },
  {
    id: 9,
    category: 'custody',
    question: "Do you offer multi-signature wallet options?",
    answer: "Yes. We support 2-of-3, 3-of-5, and custom multi-sig configurations. You can hold keys, we hold keys, and/or a third-party custodian holds keys. This ensures no single party can move funds without proper authorization."
  },
  {
    id: 10,
    category: 'general',
    question: "How do I verify that you actually hold the assets you claim (proof of reserves)?",
    answer: "We publish real-time proof of reserves on-chain, updated every 24 hours. You can verify our holdings using blockchain explorers. Our reserves are audited monthly by Armanino LLP (Big 4 accounting firm). Visit our Proof of Reserves page for live verification links."
  },
  {
    id: 11,
    category: 'pricing',
    question: "Are there any hidden fees I should know about?",
    answer: "No. We believe in transparent pricing. You pay: (1) Annual custody fee 0.15%, (2) One-time setup fee $2,500 (waived first month), (3) Optional expedited withdrawal fee 0.1%. That's it. No deposit fees, no monthly minimums, no inactivity fees, no surprise charges."
  },
  {
    id: 12,
    category: 'general',
    question: "How long does account setup take?",
    answer: "Individual accounts: 2-3 business days after KYC verification. Institutional accounts: 5-7 business days after KYB (Know Your Business) verification, legal review, and multi-sig setup. We can expedite to 48 hours for enterprise clients with complete documentation."
  }
];

const FAQCard = ({ faq, isOpen, onToggle }: { faq: FAQItem; isOpen: boolean; onToggle: () => void }) => (
  <div 
    className="glass-card border border-gold-500/10 hover:border-gold-500/30 transition-all duration-300 overflow-hidden"
    data-testid={`faq-item-${faq.id}`}
  >
    <button
      onClick={onToggle}
      className="w-full text-left p-4 sm:p-5 flex items-start justify-between gap-3 sm:gap-4 group touch-target"
      aria-expanded={isOpen}
    >
      <div className="flex-1">
        <h3 className="font-semibold text-sm sm:text-base text-foreground group-hover:text-gold-400 transition-colors leading-relaxed">
          {faq.question}
        </h3>
      </div>
      <ChevronDown 
        className={cn(
          "h-5 w-5 text-gold-400 transition-transform duration-300 flex-shrink-0 mt-0.5 sm:h-6 sm:w-6",
          isOpen && "rotate-180"
        )}
      />
    </button>
    
    <div 
      className={cn(
        "overflow-hidden transition-all duration-300",
        isOpen ? "max-h-96 opacity-100" : "max-h-0 opacity-0"
      )}
    >
      <div className="px-4 sm:px-5 pb-4 sm:pb-5">
        <p className="text-sm sm:text-base text-foreground/75 leading-relaxed border-t border-border/30 pt-3 sm:pt-4">
          {faq.answer}
        </p>
      </div>
    </div>
  </div>
);

const FAQSection = () => {
  const supportEmail = resolveSupportEmail();
  const [openId, setOpenId] = useState<number | null>(1);
  const [activeCategory, setActiveCategory] = useState<string>('all');

  const categories = [
    { id: 'all', label: 'All Questions' },
    { id: 'security', label: 'Security' },
    { id: 'custody', label: 'Custody' },
    { id: 'pricing', label: 'Pricing' },
    { id: 'compliance', label: 'Compliance' }
  ];

  const filteredFAQs = activeCategory === 'all' 
    ? faqs 
    : faqs.filter(faq => faq.category === activeCategory);

  return (
    <section className="py-12 sm:py-16 lg:py-20 bg-background/50" data-testid="faq-section">
      <div className="container mx-auto px-4 sm:px-6">
        {/* Section Header */}
        <div className="text-center mb-8 sm:mb-10">
          <div className="inline-flex items-center justify-center h-12 w-12 rounded-xl bg-gold-500/10 mb-3 sm:mb-4">
            <HelpCircle className="h-6 w-6 text-gold-400" />
          </div>
          <h2 className="font-display text-2xl sm:text-3xl lg:text-4xl font-bold mb-3">
            Frequently Asked <span className="text-gradient">Questions</span>
          </h2>
          <p className="text-foreground/70 text-sm sm:text-base max-w-2xl mx-auto leading-relaxed">
            Everything you need to know about our custody services, security, and pricing. 
            Can't find an answer? <a href="/contact" className="text-gold-400 underline hover:text-gold-300">Contact our team</a>.
          </p>
        </div>

        {/* Category Filter - Mobile optimized */}
        <div className="flex flex-wrap justify-center gap-2 sm:gap-3 mb-6 sm:mb-8">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              className={cn(
                "px-3 py-2 text-sm font-medium rounded-full transition-all duration-300 touch-target-sm",
                activeCategory === category.id
                  ? "bg-gold-500 text-black"
                  : "bg-card/50 text-foreground/80 hover:bg-gold-500/10 hover:text-gold-400 border border-gold-500/20"
              )}
            >
              {category.label}
            </button>
          ))}
        </div>

        {/* FAQ Grid */}
        <div className="max-w-4xl mx-auto space-y-3">
          {filteredFAQs.map((faq, index) => (
            <div
              key={faq.id}
              className="animate-fade-in"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <FAQCard 
                faq={faq} 
                isOpen={openId === faq.id}
                onToggle={() => setOpenId(openId === faq.id ? null : faq.id)}
              />
            </div>
          ))}
        </div>

        {/* Still Have Questions CTA */}
        <div className="mt-10 sm:mt-14 text-center glass-card p-6 sm:p-7 max-w-2xl mx-auto border border-gold-500/20">
          <h3 className="font-display text-lg sm:text-2xl font-bold mb-3">
            Still have questions?
          </h3>
          <p className="text-foreground/70 text-sm sm:text-base mb-5 sm:mb-6 leading-relaxed">
            Our custody specialists are available 24/7 to help you understand our services 
            and find the right solution for your needs.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <a 
              href="/contact"
              className="inline-flex items-center justify-center px-5 py-2.5 bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold rounded-lg transition-all duration-300 hover:scale-105 touch-target"
            >
              Contact Support
            </a>
            <a 
              href={`mailto:${supportEmail}`}
              className="inline-flex items-center justify-center px-5 py-2.5 border border-gold-500/30 hover:border-gold-400 hover:bg-gold-500/10 text-foreground rounded-lg transition-all duration-300 touch-target"
            >
              Email Us
            </a>
          </div>
        </div>

        {/* Additional Resources */}
        <div className="mt-8 sm:mt-10 flex flex-wrap items-center justify-center gap-4 sm:gap-6 text-xs sm:text-sm text-foreground/60">
          <a href="/security" className="hover:text-gold-400 transition-colors underline touch-target-sm">
            Security Architecture
          </a>
          <span className="text-gold-500/30">•</span>
          <a href="/proof-of-reserves" className="hover:text-gold-400 transition-colors underline touch-target-sm">
            Proof of Reserves
          </a>
          <span className="text-gold-500/30">•</span>
          <a href="/terms" className="hover:text-gold-400 transition-colors underline touch-target-sm">
            Terms of Service
          </a>
          <span className="text-gold-500/30">•</span>
          <a href="/help" className="hover:text-gold-400 transition-colors underline touch-target-sm">
            Help Center
          </a>
        </div>
      </div>
    </section>
  );
};

export default FAQSection;
