import { Wallet, Twitter, Linkedin, MessageCircle, Send, MapPin, Mail, Phone } from "lucide-react";
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
    <footer className="border-t border-border/50 bg-secondary/20" data-testid="footer">
      <div className="container mx-auto px-4 py-14">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-8">
          {/* Brand */}
          <div className="col-span-2">
            <Link to="/" className="flex items-center gap-2 mb-4 w-fit hover:opacity-80 transition-opacity">
              <img 
                src="/cryptovault-logo.png" 
                alt="CryptoVault" 
                className="h-9 w-9 object-contain"
              />
              <span className="font-display text-xl font-bold">CryptoVault</span>
            </Link>
            <p className="text-sm text-muted-foreground max-w-xs mb-6">
              Institutional-grade digital asset custody and management. 
              Secure, compliant, and trusted by individuals and enterprises.
            </p>
            
            {/* Contact Info */}
            <div className="space-y-2 mb-6">
              <a 
                href="mailto:support@cryptovault.financial" 
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors"
                data-testid="footer-email"
              >
                <Mail className="h-4 w-4" />
                support@cryptovault.financial
              </a>
              <div className="flex items-start gap-2 text-sm text-muted-foreground">
                <MapPin className="h-4 w-4 mt-0.5" />
                <span>1201 Market Street, Suite 101<br />Wilmington, DE 19801</span>
              </div>
            </div>

            {/* Social Links */}
            <div className="flex gap-4">
              {/* TODO: Replace with actual CryptoVault social links */}
              <a 
                href="https://twitter.com/CryptoVaultFin" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-muted-foreground hover:text-primary transition-colors"
                title="X (Twitter) @CryptoVaultFin"
                data-testid="social-twitter"
              >
                <Twitter className="h-5 w-5" />
              </a>
              <a 
                href="https://linkedin.com/company/cryptovault-financial" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-muted-foreground hover:text-primary transition-colors"
                title="LinkedIn"
                data-testid="social-linkedin"
              >
                <Linkedin className="h-5 w-5" />
              </a>
              <a 
                href="https://discord.gg/cryptovault" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-muted-foreground hover:text-primary transition-colors"
                title="Discord"
                data-testid="social-discord"
              >
                <MessageCircle className="h-5 w-5" />
              </a>
              <a 
                href="https://t.me/cryptovaultfinancial" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-muted-foreground hover:text-primary transition-colors"
                title="Telegram"
                data-testid="social-telegram"
              >
                <Send className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Company Links */}
          <div>
            <h4 className="font-semibold mb-4">Company</h4>
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
            <h4 className="font-semibold mb-4">Products</h4>
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
            <h4 className="font-semibold mb-4">Resources</h4>
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
            <h4 className="font-semibold mb-4">Legal</h4>
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
        <div className="border-t border-border/50 mt-12 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-muted-foreground">
              © 2024 CryptoVault Financial, Inc. All rights reserved.
            </p>
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span>Delaware C-Corp</span>
              <span className="hidden md:inline">•</span>
              <span>FinCEN Registered</span>
              <span className="hidden md:inline">•</span>
              <span>SOC 2 Type II (In Progress)</span>
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
