import { Wallet, Twitter, Github, Linkedin, Youtube } from "lucide-react";
import { Link } from "react-router-dom";

const Footer = () => {
  const links = {
    products: [
      { label: "Exchange", href: "/markets" },
      { label: "Wallet", href: "#" },
      { label: "Card", href: "#" },
      { label: "Earn", href: "/earn" },
      { label: "NFT", href: "#" },
    ],
    resources: [
      { label: "Learn", href: "/learn" },
      { label: "Blog", href: "#" },
      { label: "API Docs", href: "#" },
      { label: "Status", href: "#" },
      { label: "Support", href: "/contact" },
    ],
    company: [
      { label: "About", href: "#" },
      { label: "Careers", href: "#" },
      { label: "Press", href: "#" },
      { label: "Legal", href: "#" },
      { label: "Privacy", href: "/privacy" },
    ],
  };

  return (
    <footer className="border-t border-border/50 bg-secondary/20">
      <div className="container mx-auto px-4 py-14">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
          {/* Brand */}
          <div className="col-span-2">
            <Link to="/" className="flex items-center gap-2 mb-4 w-fit hover:opacity-80 transition-opacity">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent">
                <Wallet className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="font-display text-xl font-bold">CryptoVault</span>
            </Link>
            <p className="text-sm text-muted-foreground max-w-xs mb-6">
              The most trusted cryptocurrency platform for buying, selling, and managing digital assets.
            </p>
            <div className="flex gap-4">
              <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-primary transition-colors">
                <Twitter className="h-5 w-5" />
              </a>
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-primary transition-colors">
                <Github className="h-5 w-5" />
              </a>
              <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-primary transition-colors">
                <Linkedin className="h-5 w-5" />
              </a>
              <a href="https://youtube.com" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-primary transition-colors">
                <Youtube className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Links */}
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
        </div>

        <div className="border-t border-border/50 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-muted-foreground">
            © 2024 CryptoVault. All rights reserved.
          </p>
          <div className="flex gap-6">
            <Link to="/terms" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Terms of Service
            </Link>
            <Link to="/privacy" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Privacy Policy
            </Link>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Cookie Policy
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
