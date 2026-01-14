import { Button } from "@/components/ui/button";
import { 
  Wallet, 
  X, 
  LogOut, 
  ChevronDown, 
  Globe, 
  Shield,
  Zap,
  Menu,
  LayoutDashboard,
  LineChart,
  Briefcase,
  BookOpen,
  HelpCircle
} from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { WalletConnect } from "@/components/WalletConnect";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// ============================================
// LANGUAGE SELECTOR COMPONENT
// ============================================
const languages = [
  { code: "en", name: "English", flag: "🇺🇸" },
  { code: "es", name: "Español", flag: "🇪🇸" },
  { code: "zh", name: "中文", flag: "🇨🇳" },
  { code: "ja", name: "日本語", flag: "🇯🇵" },
];

const LanguageSelector = () => {
  const [currentLang, setCurrentLang] = useState("en");

  return (
    <DropdownMenu>
      <DropdownMenuTrigger 
        className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:text-primary transition-colors duration-300 focus:outline-none min-h-[44px]"
        aria-label="Select language"
      >
        <Globe className="h-4 w-4" />
        <span className="hidden lg:inline uppercase font-mono">{currentLang}</span>
        <ChevronDown className="h-3 w-3 opacity-60" />
      </DropdownMenuTrigger>
      <DropdownMenuContent 
        align="end" 
        className="w-40 bg-card/95 backdrop-blur-xl border-white/10"
      >
        {languages.map((lang) => (
          <DropdownMenuItem 
            key={lang.code}
            onClick={() => setCurrentLang(lang.code)}
            className={`cursor-pointer hover:bg-primary/10 hover:text-primary transition-colors min-h-[44px] ${
              currentLang === lang.code ? "text-primary bg-primary/10" : ""
            }`}
          >
            <span className="mr-2">{lang.flag}</span>
            {lang.name}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

// ============================================
// NAVIGATION LINK COMPONENT
// ============================================
interface NavLinkProps {
  to: string;
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

const AnimatedNavLink = ({ to, children, onClick, className = "" }: NavLinkProps) => {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      onClick={onClick}
      className={`relative text-sm font-medium transition-colors duration-300 group py-2 font-mono uppercase tracking-wider ${
        isActive 
          ? "text-gold-400" 
          : "text-muted-foreground hover:text-foreground"
      } ${className}`}
    >
      {children}
      <span 
        className={`absolute bottom-0 left-1/2 -translate-x-1/2 h-px bg-gold-400 transition-all duration-300 ${
          isActive ? "w-full" : "w-0 group-hover:w-full"
        }`}
      />
    </Link>
  );
};

// ============================================
// MOBILE MENU COMPONENT
// ============================================
interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  user: any;
  onSignOut: () => void;
}

const MobileMenu = ({ isOpen, onClose, user, onSignOut }: MobileMenuProps) => {
  const menuLinks = [
    { to: "/", label: "Home", icon: Shield },
    { to: "/markets", label: "Markets", icon: LineChart },
    { to: "/trade", label: "Trade", icon: Briefcase },
    { to: "/earn", label: "Wallet", icon: Wallet },
    { to: "/learn", label: "Learn", icon: BookOpen },
    { to: "/contact", label: "Support", icon: HelpCircle },
  ];

  return (
    <>
      {/* Backdrop */}
      <div 
        className={`fixed inset-0 bg-black/80 backdrop-blur-sm z-40 transition-opacity duration-300 ${
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Menu Panel */}
      <div 
        className={`fixed inset-0 z-50 bg-background/98 backdrop-blur-2xl transition-all duration-500 transform ${
          isOpen ? "translate-x-0 opacity-100" : "translate-x-full opacity-0"
        }`}
        role="dialog"
        aria-modal="true"
        aria-label="Mobile navigation menu"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 sm:px-6 py-4 border-b border-white/10">
          <Link to="/" className="flex items-center gap-3" onClick={onClose}>
            <img 
              src="/logo.svg" 
              alt="CryptoVault" 
              className="h-10 w-10 object-contain"
            />
            <span className="font-display text-xl font-bold tracking-tight">
              Crypto<span className="text-gold-400">Vault</span>
            </span>
          </Link>
          
          <button
            onClick={onClose}
            className="p-3 text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors rounded-lg min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Close menu"
          >
            <X className="h-6 w-6" />
          </button>
        </div>
        
        {/* Navigation Links */}
        <nav className="flex flex-col px-4 sm:px-6 py-6 space-y-1 overflow-y-auto max-h-[calc(100vh-200px)]">
          {menuLinks.map((link, index) => {
            const Icon = link.icon;
            return (
              <Link
                key={link.to}
                to={link.to}
                onClick={onClose}
                className="text-base font-medium text-muted-foreground hover:text-gold-400 py-4 px-4 hover:bg-gold-500/5 transition-colors flex items-center gap-4 rounded-lg min-h-[56px]"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <Icon className="h-5 w-5" />
                {link.label}
              </Link>
            );
          })}
        </nav>
        
        {/* Bottom Actions */}
        <div className="absolute bottom-0 left-0 right-0 p-4 sm:p-6 border-t border-white/10 bg-background/80 backdrop-blur-xl safe-area-pb">
          <div className="flex flex-col gap-3">
            {user ? (
              <>
                <Button 
                  variant="outline" 
                  className="w-full h-12 border-gold-500/30 hover:border-gold-400 hover:bg-gold-500/10 hover:text-gold-400 font-mono uppercase"
                  asChild
                >
                  <Link to="/dashboard" onClick={onClose}>
                    <LayoutDashboard className="h-4 w-4 mr-2" />
                    Dashboard
                  </Link>
                </Button>
                <Button 
                  variant="ghost" 
                  className="w-full h-12 text-muted-foreground hover:text-destructive font-mono uppercase"
                  onClick={() => { onSignOut(); onClose(); }}
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign Out
                </Button>
              </>
            ) : (
              <>
                <Button 
                  variant="outline" 
                  className="w-full h-12 border-gold-500/30 hover:border-gold-400 hover:bg-gold-500/10 hover:text-gold-400 font-mono uppercase"
                  asChild
                >
                  <Link to="/auth" onClick={onClose}>Sign In</Link>
                </Button>
                <Button 
                  className="w-full h-12 bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-bold font-mono uppercase tracking-wider"
                  asChild
                >
                  <Link to="/auth" onClick={onClose}>
                    <Zap className="h-4 w-4 mr-2" />
                    Get Started
                  </Link>
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

// ============================================
// MAIN HEADER COMPONENT
// ============================================
const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const auth = useAuth();
  const navigate = useNavigate();

  const user = auth?.user ?? null;
  const signOut = auth?.signOut ?? (() => {});

  const handleScroll = useCallback(() => {
    setIsScrolled(window.scrollY > 10);
  }, []);

  useEffect(() => {
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  useEffect(() => {
    if (isMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isMenuOpen]);

  const handleSignOut = () => {
    signOut();
    navigate("/");
  };

  const navLinks = [
    { to: "/", label: "Home" },
    { to: "/markets", label: "Markets" },
    { to: "/trade", label: "Trade" },
    { to: "/earn", label: "Wallet" },
    { to: "/learn", label: "Learn" },
    { to: "/contact", label: "Support" },
  ];

  return (
    <>
      <header 
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
          isScrolled 
            ? "bg-background/95 backdrop-blur-2xl border-b border-white/5 shadow-lg" 
            : "bg-transparent"
        }`}
        data-testid="header"
        role="banner"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex h-16 sm:h-18 lg:h-20 items-center justify-between">
            
            {/* LEFT: Logo */}
            <Link 
              to="/" 
              className="flex items-center gap-2 sm:gap-3 group"
              data-testid="logo-link"
              aria-label="CryptoVault - Go to homepage"
            >
              <div className="relative">
                <img 
                  src="/logo.svg" 
                  alt="CryptoVault Logo" 
                  className="h-9 w-9 sm:h-10 sm:w-10 lg:h-12 lg:w-12 object-contain transition-transform duration-300 group-hover:scale-105"
                />
              </div>
              
              <div className="flex flex-col">
                <span className="font-display text-lg sm:text-xl lg:text-2xl font-semibold tracking-tight leading-none">
                  Crypto<span className="text-gold-400">Vault</span>
                </span>
                <span className="hidden lg:flex items-center gap-1 text-[10px] text-muted-foreground tracking-widest uppercase mt-0.5 font-mono">
                  <Shield className="h-2.5 w-2.5 text-gold-400" />
                  Secure Global Trading
                </span>
              </div>
            </Link>

            {/* CENTER: Desktop Navigation */}
            <nav 
              className="hidden lg:flex items-center gap-6 xl:gap-8"
              role="navigation"
              aria-label="Main navigation"
            >
              {navLinks.map((link) => (
                <AnimatedNavLink key={link.to} to={link.to}>
                  {link.label}
                </AnimatedNavLink>
              ))}
            </nav>

            {/* RIGHT: Actions */}
            <div className="flex items-center gap-1 sm:gap-2 lg:gap-3">
              <div className="hidden md:block">
                <LanguageSelector />
              </div>

              <div className="hidden lg:flex items-center gap-3">
                {user && <WalletConnect />}
                
                {user ? (
                  <>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="text-muted-foreground hover:text-gold-400 hover:bg-gold-500/10 font-mono uppercase tracking-wider min-h-[44px]"
                      asChild 
                      data-testid="nav-dashboard"
                    >
                      <Link to="/dashboard">Dashboard</Link>
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={handleSignOut}
                      className="text-muted-foreground hover:text-destructive min-h-[44px]"
                      data-testid="nav-signout"
                    >
                      <LogOut className="h-4 w-4" />
                    </Button>
                  </>
                ) : (
                  <>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      className="text-muted-foreground hover:text-gold-400 hover:bg-gold-500/10 transition-colors font-mono uppercase tracking-wider min-h-[44px]"
                      asChild 
                      data-testid="nav-signin"
                    >
                      <Link to="/auth">Sign In</Link>
                    </Button>
                    
                    <Button 
                      size="sm"
                      className="bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-bold font-mono uppercase tracking-wider min-h-[44px] group"
                      asChild 
                      data-testid="nav-get-started"
                    >
                      <Link to="/auth">
                        <Zap className="h-4 w-4 mr-1.5 transition-transform group-hover:scale-110" />
                        Get Started
                      </Link>
                    </Button>
                  </>
                )}
              </div>

              {/* Mobile Menu Toggle */}
              <button 
                className="lg:hidden p-2.5 text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors rounded-lg min-h-[44px] min-w-[44px] flex items-center justify-center"
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                data-testid="mobile-menu-toggle"
                aria-expanded={isMenuOpen}
                aria-label={isMenuOpen ? "Close menu" : "Open menu"}
              >
                <Menu className="h-6 w-6" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <MobileMenu 
        isOpen={isMenuOpen}
        onClose={() => setIsMenuOpen(false)}
        user={user}
        onSignOut={handleSignOut}
      />
    </>
  );
};

export default Header;
