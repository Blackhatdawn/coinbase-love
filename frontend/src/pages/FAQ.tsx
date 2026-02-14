import Header from "@/components/Header";
import Footer from "@/components/Footer";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { HelpCircle, BookOpen, TrendingUp, Shield, ArrowRight } from "lucide-react";

const faqCategories = [
  {
    title: "Getting Started",
    icon: BookOpen,
    questions: [
      {
        q: "How do I create an account?",
        a: "Creating an account is simple. Click 'Get Started', enter your email, create a strong password, and verify your email. You'll then need to complete identity verification (KYC) before you can deposit or trade."
      },
      {
        q: "What documents do I need for verification?",
        a: "For individual accounts, you'll need a government-issued ID (passport, driver's license, or national ID) and proof of address (utility bill or bank statement dated within 3 months). Institutional accounts require additional corporate documentation."
      },
      {
        q: "How long does verification take?",
        a: "Most verifications are completed within 24 hours. Complex cases or institutional accounts may take 3-5 business days. You'll receive email updates throughout the process."
      },
      {
        q: "Is there a minimum deposit?",
        a: "There's no minimum deposit for crypto. For fiat deposits, the minimum is $10 USD or equivalent. Institutional accounts may have different minimums based on their service tier."
      }
    ]
  },
  {
    title: "Security",
    icon: Shield,
    questions: [
      {
        q: "How secure is CryptoVault?",
        a: "We employ bank-grade security including 95%+ cold storage, multi-signature wallets, HSM-backed key management, and $500M insurance coverage. We're also pursuing SOC 2 Type II certification."
      },
      {
        q: "What is multi-signature (multi-sig)?",
        a: "Multi-sig requires multiple private keys to authorize a transaction. Our standard is 2-of-3 (2 signatures from 3 possible signers), and institutional clients can use 3-of-5 or custom configurations."
      },
      {
        q: "How do I enable two-factor authentication (2FA)?",
        a: "Go to Settings > Security > Two-Factor Authentication. We recommend using an authenticator app like Google Authenticator or Authy. SMS 2FA is available but less secure."
      },
      {
        q: "What happens if I lose access to my 2FA?",
        a: "When you set up 2FA, you receive backup codes. Store these securely. If you lose both your 2FA device and backup codes, you'll need to contact support and go through identity reverification."
      }
    ]
  },
  {
    title: "Trading & Fees",
    icon: TrendingUp,
    questions: [
      {
        q: "What cryptocurrencies can I trade?",
        a: "We support major cryptocurrencies including BTC, ETH, SOL, ADA, DOT, AVAX, and many ERC-20 tokens. Check our Markets page for the full list of supported assets."
      },
      {
        q: "What are the trading fees?",
        a: "Trading fees range from 0.1% to 0.5% depending on your account tier and 30-day trading volume. Institutional accounts benefit from lower fees. See our pricing page for details."
      },
      {
        q: "How do withdrawals work?",
        a: "Navigate to your wallet, select the asset, click Withdraw, enter the destination address and amount. Withdrawals go through our security review process and are typically processed within 24 hours."
      },
      {
        q: "Are there withdrawal limits?",
        a: "Withdrawal limits depend on your verification level and account tier. Standard accounts have daily limits of $50,000 USD equivalent. Premium and Institutional accounts have higher or no limits."
      }
    ]
  }
];

const resources = [
  {
    title: "Crypto Security Best Practices",
    description: "Learn how to protect your digital assets with industry-standard security practices.",
    category: "Security"
  },
  {
    title: "Understanding Multi-Signature Wallets",
    description: "A deep dive into how multi-sig technology protects your assets.",
    category: "Education"
  },
  {
    title: "Staking Rewards Explained",
    description: "How staking works and what returns you can expect from different protocols.",
    category: "Staking"
  },
  {
    title: "Market Analysis: Q3 2024",
    description: "Our quarterly analysis of cryptocurrency market trends and outlook.",
    category: "Insights"
  }
];

const FAQ = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-20 sm:pt-24">
        {/* Hero */}
        <section className="py-14 sm:py-20 bg-gradient-to-b from-secondary/30 to-background">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-6">
                <HelpCircle className="h-4 w-4 text-primary" />
                <span className="text-sm text-primary font-medium">Help Center</span>
              </div>
              <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold mb-5 sm:mb-6">
                FAQ & <span className="text-gradient">Resources</span>
              </h1>
              <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto">
                Find answers to common questions and explore our educational resources
                to make the most of your CryptoVault experience.
              </p>
            </div>
          </div>
        </section>

        {/* FAQ Sections */}
        <section className="py-14 sm:py-20">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto space-y-8 sm:space-y-12">
              {faqCategories.map((category) => (
                <div key={category.title} data-testid={`faq-${category.title.toLowerCase().replace(/\s+/g, '-')}`}>
                  <div className="flex items-center gap-3 mb-5 sm:mb-6">
                    <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <category.icon className="h-4 w-4 sm:h-5 sm:w-5 text-primary" />
                    </div>
                    <h2 className="font-display text-xl sm:text-2xl font-bold">{category.title}</h2>
                  </div>
                  <Accordion type="single" collapsible className="space-y-2">
                    {category.questions.map((item, index) => (
                      <AccordionItem
                        key={index}
                        value={`${category.title}-${index}`}
                        className="glass-card px-4 sm:px-6"
                      >
                        <AccordionTrigger className="text-left font-medium hover:no-underline">
                          {item.q}
                        </AccordionTrigger>
                        <AccordionContent className="text-muted-foreground">
                          {item.a}
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Resources / Blog */}
        <section className="py-14 sm:py-20 bg-secondary/20">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-center justify-between mb-8 sm:mb-10">
                <div>
                  <h2 className="font-display text-2xl sm:text-3xl font-bold mb-2">Resources & Insights</h2>
                  <p className="text-sm sm:text-base text-muted-foreground">Educational content and market analysis</p>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4 sm:gap-6">
                {resources.map((resource) => (
                  <div
                    key={resource.title}
                    className="glass-card p-4 sm:p-6 hover:border-primary/50 transition-colors cursor-pointer group"
                  >
                    <span className="inline-block px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium mb-4">
                      {resource.category}
                    </span>
                    <h3 className="font-display text-base sm:text-lg font-semibold mb-2 group-hover:text-primary transition-colors">
                      {resource.title}
                    </h3>
                    <p className="text-muted-foreground text-sm">{resource.description}</p>
                  </div>
                ))}
              </div>

              <div className="text-center mt-8 sm:mt-10">
                <p className="text-muted-foreground text-xs sm:text-sm">
                  Read more in our full research and education hub on the Blog page.
                </p>
                <Button variant="outline" size="sm" asChild className="mt-3">
                  <Link to="/blog">Open Blog</Link>
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Contact CTA */}
        <section className="py-14 sm:py-20">
          <div className="container mx-auto px-4">
            <div className="max-w-2xl mx-auto text-center">
              <h2 className="font-display text-2xl sm:text-3xl font-bold mb-4">
                Still Have Questions?
              </h2>
              <p className="text-sm sm:text-base text-muted-foreground mb-6 sm:mb-8">
                Our support team is here to help you 24/7.
              </p>
              <Button variant="hero" size="xl" asChild>
                <Link to="/contact">
                  Contact Support
                  <ArrowRight className="h-5 w-5 ml-2" />
                </Link>
              </Button>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default FAQ;
