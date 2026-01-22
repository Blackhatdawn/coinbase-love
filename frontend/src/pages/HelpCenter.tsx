import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Search, MessageCircle, Mail, Phone, FileQuestion, BookOpen, CreditCard, Shield, User, Wallet, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const HelpCenter = () => {
  const categories = [
    {
      icon: User,
      title: "Account & Verification",
      description: "Signup, login, KYC, and account settings",
      articles: 24
    },
    {
      icon: Wallet,
      title: "Deposits & Withdrawals",
      description: "Funding your account and withdrawing funds",
      articles: 18
    },
    {
      icon: CreditCard,
      title: "Trading",
      description: "Order types, fees, and trading features",
      articles: 32
    },
    {
      icon: Shield,
      title: "Security",
      description: "2FA, passwords, and account protection",
      articles: 15
    },
    {
      icon: BookOpen,
      title: "Getting Started",
      description: "Beginner guides and platform tutorials",
      articles: 20
    },
    {
      icon: FileQuestion,
      title: "Troubleshooting",
      description: "Common issues and solutions",
      articles: 28
    }
  ];

  const popularArticles = [
    "How to verify my identity (KYC)",
    "How to enable Two-Factor Authentication (2FA)",
    "Understanding trading fees",
    "How to deposit cryptocurrency",
    "Why is my withdrawal pending?",
    "How to reset my password",
    "Account security best practices",
    "Understanding limit vs market orders"
  ];

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-20 sm:pt-24 pb-16 sm:pb-20">
        <div className="container mx-auto px-4">
          {/* Hero */}
          <div className="text-center max-w-3xl mx-auto mb-12">
            <h1 className="font-display text-4xl md:text-5xl font-bold mb-6">
              How Can We <span className="bg-gradient-to-r from-gold-400 to-gold-600 bg-clip-text text-transparent">Help?</span>
            </h1>
            <p className="text-lg text-muted-foreground mb-8">
              Search our knowledge base or browse categories to find answers to your questions.
            </p>
            
            {/* Search */}
            <div className="relative max-w-xl mx-auto">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search for articles, guides, and FAQs..."
                className="pl-12 h-14 text-lg bg-background border-gold-500/20 focus:border-gold-400"
              />
            </div>
          </div>

          {/* Categories */}
          <section className="mb-16">
            <h2 className="text-2xl font-bold mb-8 text-center">Browse by Category</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {categories.map((category) => (
                <div key={category.title} className="glass-card p-6 border border-gold-500/10 hover:border-gold-500/30 transition-all group cursor-pointer">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gold-500/10 flex items-center justify-center shrink-0 group-hover:bg-gold-500/20 transition-colors">
                      <category.icon className="h-6 w-6 text-gold-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold mb-1 group-hover:text-gold-400 transition-colors">{category.title}</h3>
                      <p className="text-sm text-muted-foreground mb-2">{category.description}</p>
                      <span className="text-xs text-gold-400">{category.articles} articles</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Popular Articles */}
          <section className="mb-16">
            <h2 className="text-2xl font-bold mb-8 flex items-center gap-2">
              <span className="h-8 w-1 bg-gradient-to-b from-gold-400 to-gold-600 rounded-full"></span>
              Popular Articles
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              {popularArticles.map((article) => (
                <div key={article} className="flex items-center justify-between p-4 glass-card border border-gold-500/10 hover:border-gold-500/30 transition-all group cursor-pointer">
                  <span className="group-hover:text-gold-400 transition-colors">{article}</span>
                  <ArrowRight className="h-4 w-4 text-gold-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              ))}
            </div>
          </section>

          {/* Contact Options */}
          <section>
            <h2 className="text-2xl font-bold mb-8 text-center">Still Need Help?</h2>
            <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              <div className="glass-card p-6 border border-gold-500/10 text-center">
                <div className="w-14 h-14 mx-auto mb-4 rounded-xl bg-gold-500/10 flex items-center justify-center">
                  <MessageCircle className="h-7 w-7 text-gold-400" />
                </div>
                <h3 className="font-semibold mb-2">Live Chat</h3>
                <p className="text-sm text-muted-foreground mb-4">Chat with our support team 24/7</p>
                <Button variant="outline" className="border-gold-500/30 hover:border-gold-400 hover:text-gold-400">
                  Start Chat
                </Button>
              </div>
              <div className="glass-card p-6 border border-gold-500/10 text-center">
                <div className="w-14 h-14 mx-auto mb-4 rounded-xl bg-gold-500/10 flex items-center justify-center">
                  <Mail className="h-7 w-7 text-gold-400" />
                </div>
                <h3 className="font-semibold mb-2">Email Support</h3>
                <p className="text-sm text-muted-foreground mb-4">Get a response within 24 hours</p>
                <Button variant="outline" className="border-gold-500/30 hover:border-gold-400 hover:text-gold-400" asChild>
                  <Link to="/contact">Contact Us</Link>
                </Button>
              </div>
              <div className="glass-card p-6 border border-gold-500/10 text-center">
                <div className="w-14 h-14 mx-auto mb-4 rounded-xl bg-gold-500/10 flex items-center justify-center">
                  <Phone className="h-7 w-7 text-gold-400" />
                </div>
                <h3 className="font-semibold mb-2">Phone Support</h3>
                <p className="text-sm text-muted-foreground mb-4">VIP customers: +1 (800) 555-0123</p>
                <Button variant="outline" className="border-gold-500/30 hover:border-gold-400 hover:text-gold-400" disabled>
                  VIP Only
                </Button>
              </div>
            </div>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default HelpCenter;
