import { Twitter, Linkedin, MessageCircle, Send, MapPin, Mail, Shield, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import { resolveSupportEmail } from "@/lib/runtimeConfig";
import { getSocialLinks } from "@/config/socialLinks";

const Footer = () => {
  const links = {
    company: [
      { label: "About Us", href: "/about" },
      { label: "Services", href: "/services" },
      { label: "Security", href: "/security" },
      { label: "Careers", href: "/careers" },
      { label: "Blog", href: "/blog" },
    ],
    products: [
      { label: "Markets", href: "/markets" },
      { label: "Trade", href: "/trade" },
      { label: "Earn (Staking)", href: "/earn" },
      { label: "Portfolio", href: "/dashboard" },
      { label: "Fees", href: "/fees" },
    ],
    resources: [
      { label: "Learn", href: "/learn" },
      { label: "FAQ", href: "/faq" },
      { label: "Help Center", href: "/help" },
      { label: "API Docs", href: "#" },
      { label: "Contact", href: "/contact" },
    ],
    legal: [
      { label: "Terms of Service", href: "/terms" },
      { label: "Privacy Policy", href: "/privacy" },
      { label: "Cookie Policy", href: "/cookies" },
      { label: "AML Policy", href: "/aml" },
      { label: "Risk Disclosure", href: "/risk-disclosure" },
    ],
  };

  const supportEmail = resolveSupportEmail();
  const socialLinks = getSocialLinks();

  return (
    <footer className="border-t border-gold-500/10 bg-background/95" data-testid="footer">
      <div className="container mx-auto px-4 py-10 sm:py-12">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-6 sm:gap-8">
          {/* Brand */}
          <div className="col-span-2">
            <Link to="/" className="flex items-center gap-3 mb-4 w-fit group">
              <div className="relative">
                <img
                  src="/favicon.svg"
                  alt="CryptoVault"
                  className="h-10 w-10 sm:h-12 sm:w-12 object-contain transition-transform duration-300 group-hover:scale-105"
                />
                <div className="absolute inset-0 rounded-full bg-gold-500/0 group-hover:bg-gold-500/20 blur-lg transition-all duration-500 -z-10" />
              </div>
              <div className="flex flex-col">
                <span className="font-display text-xl sm:text-2xl font-bold tracking-tight">
                  Crypto<span className="text-gold-400">Vault</span>
                </span>
                <span className="flex items-center gap-1 text-[10px] text-muted-foreground tracking-wider uppercase">
                  <Shield className="h-2.5 w-2.5 text-gold-500" />
                  Secure Global Trading
                </span>
              </div>
            </Link>
            <p className="text-sm text-muted-foreground max-w-xs mb-5">
              Institutional-grade digital asset custody and management.
              Secure, compliant, and trusted by individuals and enterprises worldwide.
            </p>

            {/* Contact Info */}
            <div className="space-y-2 mb-5">
              <a
                href={`mailto:${supportEmail}`}
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-gold-400 transition-colors"
                data-testid="footer-email"
              >
                <Mail className="h-4 w-4" />
                {supportEmail}
              </a>
              <div className="flex items-start gap-2 text-sm text-muted-foreground">
                <MapPin className="h-4 w-4 mt-0.5 text-gold-500/60" />
                <span>1201 Market Street, Suite 101<br />Wilmington, DE 19801</span>
              </div>
            </div>

            {/* Social Links */}
            <div className="flex gap-3 sm:gap-4">
              {socialLinks.twitter && (
                <a
                  href={socialLinks.twitter}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 rounded-lg bg-gold-500/5 text-muted-foreground hover:text-gold-400 hover:bg-gold-500/10 transition-all"
                  title="X (Twitter)"
                  data-testid="social-twitter"
                >
                  <Twitter className="h-4 w-4 sm:h-5 sm:w-5" />
                </a>
              )}
              {socialLinks.linkedin && (
                <a
                  href={socialLinks.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 rounded-lg bg-gold-500/5 text-muted-foreground hover:text-gold-400 hover:bg-gold-500/10 transition-all"
                  title="LinkedIn"
                  data-testid="social-linkedin"
                >
                  <Linkedin className="h-4 w-4 sm:h-5 sm:w-5" />
                </a>
              )}
              {socialLinks.discord && (
                <a
                  href={socialLinks.discord}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 rounded-lg bg-gold-500/5 text-muted-foreground hover:text-gold-400 hover:bg-gold-500/10 transition-all"
                  title="Discord"
                  data-testid="social-discord"
                >
                  <MessageCircle className="h-4 w-4 sm:h-5 sm:w-5" />
                </a>
              )}
              {socialLinks.telegram && (
                <a
                  href={socialLinks.telegram}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 rounded-lg bg-gold-500/5 text-muted-foreground hover:text-gold-400 hover:bg-gold-500/10 transition-all"
                  title="Telegram"
                  data-testid="social-telegram"
                >
                  <Send className="h-4 w-4 sm:h-5 sm:w-5" />
                </a>
              )}
            </div>
          </div>

          {/* Company Links */}
          <div>
            <h4 className="font-semibold mb-3 text-gold-400">Company</h4>
            <ul className="space-y-2 sm:space-y-3">
              {links.company.map((link) => (
                <li key={link.label}>
                  {link.href.startsWith("http") || link.href === "#" ? (
                    <a href={link.href} className="text-sm text-muted-foreground hover:text-gold-400 transition-colors flex items-center gap-1">
                      {link.label}
                      {link.href.startsWith("http") && <ExternalLink className="h-3 w-3" />}
                    </a>
                  ) : (
                    <Link to={link.href} className="text-sm text-muted-foreground hover:text-gold-400 transition-colors">
                      {link.label}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Products Links */}
          <div>
            <h4 className="font-semibold mb-3 text-gold-400">Products</h4>
            <ul className="space-y-2 sm:space-y-3">
              {links.products.map((link) => (
                <li key={link.label}>
                  {link.href.startsWith("http") || link.href === "#" ? (
                    <a href={link.href} className="text-sm text-muted-foreground hover:text-gold-400 transition-colors">
                      {link.label}
                    </a>
                  ) : (
                    <Link to={link.href} className="text-sm text-muted-foreground hover:text-gold-400 transition-colors">
                      {link.label}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Links */}
          <div>
            <h4 className="font-semibold mb-3 text-gold-400">Resources</h4>
            <ul className="space-y-2 sm:space-y-3">
              {links.resources.map((link) => (
                <li key={link.label}>
                  {link.href.startsWith("http") || link.href === "#" ? (
                    <a href={link.href} className="text-sm text-muted-foreground hover:text-gold-400 transition-colors">
                      {link.label}
                    </a>
                  ) : (
                    <Link to={link.href} className="text-sm text-muted-foreground hover:text-gold-400 transition-colors">
                      {link.label}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h4 className="font-semibold mb-3 text-gold-400">Legal</h4>
            <ul className="space-y-2 sm:space-y-3">
              {links.legal.map((link) => (
                <li key={link.label}>
                  {link.href.startsWith("http") || link.href === "#" ? (
                    <a href={link.href} className="text-sm text-muted-foreground hover:text-gold-400 transition-colors">
                      {link.label}
                    </a>
                  ) : (
                    <Link to={link.href} className="text-sm text-muted-foreground hover:text-gold-400 transition-colors">
                      {link.label}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="border-t border-gold-500/10 mt-10 sm:mt-12 pt-6 sm:pt-8">
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
              <span>FinCEN MSB Registered</span>
              <span className="hidden md:inline text-gold-500/30">•</span>
              <span className="text-gold-500/80">SOC 2 Type II</span>
            </div>
          </div>
          
          {/* Risk Disclaimer */}
          <p className="text-xs text-muted-foreground/70 mt-5 sm:mt-6 text-center max-w-4xl mx-auto">
            Digital asset investments involve substantial risk. Prices can be volatile and you may lose 
            your entire investment. Past performance does not guarantee future results. CryptoVault Financial 
            does not provide investment advice. Please review our <Link to="/risk-disclosure" className="underline hover:text-gold-400">risk disclosures</Link> before trading.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
