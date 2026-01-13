import { Twitter, Linkedin, MessageCircle, Send, MapPin, Mail, Shield } from "lucide-react";
import { Link } from "react-router-dom";

const Footer = () => {
  const links = {
    company: [
      { label: "About Us", href: "/about" },
      { label: "Services", href: "/services" },
      { label: "Security", href: "/security" },
      { label: "Careers", href: "#" },
    ],
    products: [
      { label: "Markets", href: "/markets" },
      { label: "Trade", href: "/trade" },
      { label: "Earn", href: "/earn" },
      { label: "Portfolio", href: "/dashboard" },
    ],
    resources: [
      { label: "Learn", href: "/learn" },
      { label: "FAQ", href: "/faq" },
      { label: "API Docs", href: "#" },
      { label: "Status", href: "#" },
    ],
    legal: [
      { label: "Terms of Service", href: "/terms" },
      { label: "Privacy Policy", href: "/privacy" },
      { label: "Cookie Policy", href: "#" },
      { label: "Risk Disclosure", href: "/security" },
    ],
  };

  return (
    <footer className="border-t border-gold-500/10 bg-background/95" data-testid="footer">
      <div className="container mx-auto px-4 py-14">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-8">
          {/* Brand */}
          <div className="col-span-2">
            <Link to="/" className="flex items-center gap-3 mb-4 w-fit group">
              <div className="relative">
                <img 
                  src="/favicon.svg" 
                  alt="CryptoVault" 
                  className="h-10 w-10 object-contain transition-transform duration-300 group-hover:scale-105"
                />
                <div className="absolute inset-0 rounded-full bg-gold-500/0 group-hover:bg-gold-500/20 blur-lg transition-all duration-500 -z-10" />
              </div>
              <div className="flex flex-col">
                <span className="font-display text-xl font-bold tracking-tight">
                  Crypto<span className="text-gold-400">Vault</span>
                </span>
                <span className="flex items-center gap-1 text-[10px] text-muted-foreground tracking-wider uppercase">
                  <Shield className="h-2.5 w-2.5 text-gold-500" />
                  Secure Global Trading
                </span>
              </div>
            </Link>
            <p className="text-sm text-muted-foreground max-w-xs mb-6">
              Institutional-grade digital asset custody and management. 
              Secure, compliant, and trusted by individuals and enterprises.
            </p>
            
            {/* Contact Info */}
            <div className="space-y-2 mb-6">
              <a 
                href="mailto:support@cryptovault.financial" 
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-gold-400 transition-colors"
                data-testid="footer-email"
              >
                <Mail className="h-4 w-4" />
                support@cryptovault.financial
              </a>
              <div className="flex items-start gap-2 text-sm text-muted-foreground">
                <MapPin className="h-4 w-4 mt-0.5 text-gold-500/60" />
                <span>1201 Market Street, Suite 101<br />Wilmington, DE 19801</span>
              </div>
            </div>

            {/* Social Links */}
            <div className="flex gap-4">
              <a 
                href="https://twitter.com/CryptoVaultFin" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-muted-foreground hover:text-gold-400 transition-colors"
                title="X (Twitter) @CryptoVaultFin"
                data-testid="social-twitter"
              >
                <Twitter className="h-5 w-5" />
              </a>
              <a 
                href="https://linkedin.com/company/cryptovault-financial" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-muted-foreground hover:text-gold-400 transition-colors"
                title="LinkedIn"
                data-testid="social-linkedin"
              >
                <Linkedin className="h-5 w-5" />
              </a>
              <a 
                href="https://discord.gg/cryptovault" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-muted-foreground hover:text-gold-400 transition-colors"
                title="Discord"
                data-testid="social-discord"
              >
                <MessageCircle className="h-5 w-5" />
              </a>
              <a 
                href="https://t.me/cryptovaultfinancial" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-muted-foreground hover:text-gold-400 transition-colors"
                title="Telegram"
                data-testid="social-telegram"
              >
                <Send className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Company Links */}
          <div>
            <h4 className="font-semibold mb-4 text-gold-400">Company</h4>
            <ul className="space-y-3">
              {links.company.map((link) => (
                <li key={link.label}>
                  {link.href.startsWith("http") || link.href === "#" ? (
                    <a href={link.href} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                      {link.label}
                    </a>
                  ) : (
                    <Link to={link.href} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                      {link.label}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Products Links */}
          <div>
            <h4 className="font-semibold mb-4 text-gold-400">Products</h4>
            <ul className="space-y-3">
              {links.products.map((link) => (
                <li key={link.label}>
                  {link.href.startsWith("http") || link.href === "#" ? (
                    <a href={link.href} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                      {link.label}
                    </a>
                  ) : (
                    <Link to={link.href} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                      {link.label}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Links */}
          <div>
            <h4 className="font-semibold mb-4 text-gold-400">Resources</h4>
            <ul className="space-y-3">
              {links.resources.map((link) => (
                <li key={link.label}>
                  {link.href.startsWith("http") || link.href === "#" ? (
                    <a href={link.href} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                      {link.label}
                    </a>
                  ) : (
                    <Link to={link.href} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                      {link.label}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h4 className="font-semibold mb-4 text-gold-400">Legal</h4>
            <ul className="space-y-3">
              {links.legal.map((link) => (
                <li key={link.label}>
                  {link.href.startsWith("http") || link.href === "#" ? (
                    <a href={link.href} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                      {link.label}
                    </a>
                  ) : (
                    <Link to={link.href} className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                      {link.label}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="border-t border-gold-500/10 mt-12 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-muted-foreground">
              © 2025 CryptoVault Financial, Inc. All rights reserved.
            </p>
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Shield className="h-3 w-3 text-gold-500" />
                Delaware C-Corp
              </span>
              <span className="hidden md:inline text-gold-500/30">•</span>
              <span>FinCEN Registered</span>
              <span className="hidden md:inline text-gold-500/30">•</span>
              <span className="text-gold-500/80">SOC 2 Type II (In Progress)</span>
            </div>
          </div>
          
          {/* Risk Disclaimer */}
          <p className="text-xs text-muted-foreground/70 mt-6 text-center max-w-4xl mx-auto">
            Digital asset investments involve substantial risk. Prices can be volatile and you may lose 
            your entire investment. Past performance does not guarantee future results. CryptoVault Financial 
            does not provide investment advice. Please review our risk disclosures before trading.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
