import { Button } from "@/components/ui/button";
import { 
  Wallet, 
  Menu, 
  X, 
  LogOut, 
  ChevronDown, 
  Globe, 
  Sun, 
  Moon,
  Shield,
  Sparkles
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
        className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-gold-400 hover:bg-gold-500/10 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-gold-500/50"
        aria-label="Select language"
      >
        <Globe className="h-4 w-4" />
        <span className="hidden lg:inline uppercase">{currentLang}</span>
        <ChevronDown className="h-3 w-3 opacity-60" />
      </DropdownMenuTrigger>
      <DropdownMenuContent 
        align="end" 
        className="w-40 bg-background/95 backdrop-blur-xl border-gold-500/20"
      >
        {languages.map((lang) => (
          <DropdownMenuItem 
            key={lang.code}
            onClick={() => setCurrentLang(lang.code)}
            className={`cursor-pointer hover:bg-gold-500/10 hover:text-gold-400 transition-colors ${
              currentLang === lang.code ? "text-gold-400 bg-gold-500/10" : ""
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
// DARK MODE TOGGLE COMPONENT
// ============================================
const DarkModeToggle = () => {
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    // Check initial theme
    const root = document.documentElement;
    const isDarkMode = root.classList.contains("dark") || 
      !root.classList.contains("light");
    setIsDark(isDarkMode);
  }, []);

  const toggleTheme = () => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.remove("dark");
      root.classList.add("light");
    } else {
      root.classList.remove("light");
      root.classList.add("dark");
    }
    setIsDark(!isDark);
  };

  return (
    <button
      onClick={toggleTheme}
      className="relative p-2.5 rounded-lg text-muted-foreground hover:text-gold-400 hover:bg-gold-500/10 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-gold-500/50 group"
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
    >
      <div className="relative w-5 h-5">
        <Sun 
          className={`absolute inset-0 h-5 w-5 transition-all duration-500 ${
            isDark ? "rotate-90 scale-0 opacity-0" : "rotate-0 scale-100 opacity-100"
          }`}
        />
        <Moon 
          className={`absolute inset-0 h-5 w-5 transition-all duration-500 ${
            isDark ? "rotate-0 scale-100 opacity-100" : "-rotate-90 scale-0 opacity-0"
          }`}
        />
      </div>
      {/* Gold glow effect on hover */}
      <div className="absolute inset-0 rounded-lg bg-gold-500/0 group-hover:bg-gold-500/5 transition-all duration-300" />
    </button>
  );
};

// ============================================
// NAVIGATION LINK COMPONENT (with gold underline animation)
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
      className={`relative text-sm font-medium transition-colors duration-300 group py-2 ${
        isActive 
          ? "text-gold-400" 
          : "text-muted-foreground hover:text-foreground"
      } ${className}`}
    >
      {children}
      {/* Animated underline */}
      <span 
        className={`absolute bottom-0 left-1/2 -translate-x-1/2 h-0.5 bg-gradient-to-r from-gold-400 to-gold-600 transition-all duration-300 ${
          isActive ? "w-full" : "w-0 group-hover:w-full"
        }`}
      />
    </Link>
  );
};

// ============================================
// CONNECT WALLET BUTTON (Web3 feel with rainbow gradient)
// ============================================
const ConnectWalletButton = () => {
  return (
    <button
      className="relative overflow-hidden px-4 py-2 rounded-lg text-sm font-semibold text-white transition-all duration-300 group focus:outline-none focus:ring-2 focus:ring-gold-500/50"
      style={{
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)",
      }}
      aria-label="Connect wallet"
    >
      {/* Rainbow shimmer effect on hover */}
      <div 
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
        style={{
          background: "linear-gradient(135deg, #f093fb 0%, #f5576c 25%, #4facfe 50%, #00f2fe 75%, #667eea 100%)",
          backgroundSize: "200% 200%",
          animation: "gradient-shift 3s ease infinite",
        }}
      />
      <span className="relative flex items-center gap-2">
        <Wallet className="h-4 w-4" />
        Connect Wallet
      </span>
    </button>
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
    { to: "/", label: "Home" },
    { to: "/markets", label: "Markets" },
    { to: "/trade", label: "Trade" },
    { to: "/earn", label: "Wallet" },
    { to: "/learn", label: "Learn" },
    { to: "/contact", label: "Support" },
  ];

  return (
    <>
      {/* Backdrop */}
      <div 
        className={`fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity duration-300 ${
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Menu Panel */}
      <div 
        className={`fixed inset-0 z-50 bg-background/98 backdrop-blur-2xl transition-all duration-500 transform ${
          isOpen ? "translate-y-0 opacity-100" : "-translate-y-full opacity-0"
        }`}
        role="dialog"
        aria-modal="true"
        aria-label="Mobile navigation menu"
      >
        {/* Header with close button */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gold-500/20">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3" onClick={onClose}>
            <div className="relative">
              <img
                src="/favicon.svg"
                alt="CryptoVault"
                className="h-10 w-10 object-contain"
              />
              {/* Gold glow */}
              <div className="absolute inset-0 rounded-full bg-gold-500/20 blur-md -z-10" />
            </div>
            <div className="flex flex-col">
              <span className="font-display text-xl font-bold tracking-tight">
                Crypto<span className="text-gold-400">Vault</span>
              </span>
            </div>
          </Link>
          
          {/* Close button */}
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-gold-500/10 transition-all duration-300"
            aria-label="Close menu"
          >
            <X className="h-6 w-6" />
          </button>
        </div>
        
        {/* Navigation Links */}
        <nav className="flex flex-col px-6 py-8 space-y-2">
          {menuLinks.map((link, index) => (
            <Link
              key={link.to}
              to={link.to}
              onClick={onClose}
              className="text-lg font-medium text-muted-foreground hover:text-gold-400 py-3 px-4 rounded-lg hover:bg-gold-500/10 transition-all duration-300 flex items-center justify-between group"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              {link.label}
              <ChevronDown className="h-4 w-4 -rotate-90 opacity-0 group-hover:opacity-100 transition-opacity" />
            </Link>
          ))}
        </nav>
        
        {/* Bottom Actions */}
        <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-gold-500/20 bg-background/80 backdrop-blur-xl">
          <div className="flex flex-col gap-3">
            {/* Theme and Language */}
            <div className="flex items-center justify-between mb-4">
              <DarkModeToggle />
              <LanguageSelector />
            </div>
            
            {user ? (
              <>
                <Button 
                  variant="outline" 
                  className="w-full border-gold-500/30 hover:border-gold-400 hover:bg-gold-500/10 hover:text-gold-400"
                  asChild
                >
                  <Link to="/dashboard" onClick={onClose}>Dashboard</Link>
                </Button>
                <Button 
                  variant="ghost" 
                  className="w-full text-muted-foreground hover:text-destructive"
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
                  className="w-full border-gold-500/30 hover:border-gold-400 hover:bg-gold-500/10 hover:text-gold-400"
                  asChild
                >
                  <Link to="/auth" onClick={onClose}>Sign In</Link>
                </Button>
                <Button 
                  className="w-full bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold"
                  asChild
                >
                  <Link to="/auth" onClick={onClose}>
                    <Sparkles className="h-4 w-4 mr-2" />
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

  // Handle scroll for header background change
  const handleScroll = useCallback(() => {
    setIsScrolled(window.scrollY > 10);
  }, []);

  useEffect(() => {
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  // Prevent body scroll when mobile menu is open
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
            ? "bg-background/95 backdrop-blur-2xl shadow-lg shadow-black/10 border-b border-gold-500/10" 
            : "bg-transparent"
        }`}
        data-testid="header"
        role="banner"
      >
        {/* Optional: Announcement bar */}
        {/* <div className="bg-gradient-to-r from-gold-600 via-gold-500 to-gold-600 text-black text-xs text-center py-1.5 font-medium">
          🎉 New: Zero-fee trading on BTC/USDT pairs this week!
        </div> */}

        <div className="container mx-auto px-4 lg:px-6">
          <div className="flex h-18 lg:h-20 items-center justify-between">
            
            {/* ===== LEFT: Logo + Tagline ===== */}
            <Link 
              to="/" 
              className="flex items-center gap-3 lg:gap-4 group"
              data-testid="logo-link"
              aria-label="CryptoVault - Go to homepage"
            >
              {/* Logo with glow effect - LARGER SIZE */}
              <div className="relative">
                <img 
                  src="/favicon.svg" 
                  alt="" 
                  className="h-10 w-10 lg:h-14 lg:w-14 object-contain transition-transform duration-300 group-hover:scale-110"
                  aria-hidden="true"
                />
                {/* Gold glow on hover */}
                <div className="absolute inset-0 rounded-full bg-gold-500/0 group-hover:bg-gold-500/30 blur-xl transition-all duration-500 -z-10" />
              </div>
              
              {/* Brand text */}
              <div className="flex flex-col">
                <span className="font-display text-xl lg:text-2xl font-bold tracking-tight leading-none">
                  Crypto<span className="text-gold-400">Vault</span>
                </span>
                {/* Tagline - hidden on mobile */}
                <span className="hidden lg:flex items-center gap-1 text-[10px] text-muted-foreground tracking-wider uppercase mt-0.5">
                  <Shield className="h-2.5 w-2.5 text-gold-500" />
                  Secure Global Trading
                </span>
              </div>
            </Link>

            {/* ===== CENTER: Desktop Navigation ===== */}
            <nav 
              className="hidden lg:flex items-center gap-8"
              role="navigation"
              aria-label="Main navigation"
            >
              {navLinks.map((link) => (
                <AnimatedNavLink key={link.to} to={link.to}>
                  {link.label}
                </AnimatedNavLink>
              ))}
            </nav>

            {/* ===== RIGHT: Actions ===== */}
            <div className="flex items-center gap-2 lg:gap-3">
              {/* Language Selector - Hidden on mobile */}
              <div className="hidden lg:block">
                <LanguageSelector />
              </div>

              {/* Dark Mode Toggle - Hidden on mobile */}
              <div className="hidden lg:block">
                <DarkModeToggle />
              </div>

              {/* Desktop Auth/Wallet Buttons */}
              <div className="hidden lg:flex items-center gap-3">
                {user && <WalletConnect />}
                
                {user ? (
                  <>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="text-muted-foreground hover:text-gold-400 hover:bg-gold-500/10"
                      asChild 
                      data-testid="nav-dashboard"
                    >
                      <Link to="/dashboard">Dashboard</Link>
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={handleSignOut}
                      className="text-muted-foreground hover:text-destructive"
                      data-testid="nav-signout"
                    >
                      <LogOut className="h-4 w-4 mr-2" />
                      Sign Out
                    </Button>
                  </>
                ) : (
                  <>
                    {/* Sign In - Outline style */}
                    <Button 
                      variant="outline" 
                      size="sm"
                      className="border-gold-500/30 hover:border-gold-400 hover:bg-gold-500/10 hover:text-gold-400 transition-all duration-300"
                      asChild 
                      data-testid="nav-signin"
                    >
                      <Link to="/auth">Sign In</Link>
                    </Button>
                    
                    {/* Get Started - Solid gold with pulse animation */}
                    <Button 
                      size="sm"
                      className="relative overflow-hidden bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-semibold shadow-lg shadow-gold-500/25 hover:shadow-gold-500/40 transition-all duration-300 hover:scale-105 group"
                      asChild 
                      data-testid="nav-get-started"
                    >
                      <Link to="/auth">
                        <span className="relative z-10 flex items-center gap-1.5">
                          <Sparkles className="h-4 w-4" />
                          Get Started
                        </span>
                        {/* Subtle shine effect */}
                        <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform duration-700" />
                      </Link>
                    </Button>
                  </>
                )}
              </div>

              {/* Mobile Menu Toggle */}
              <button 
                className="lg:hidden relative p-2.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-gold-500/10 transition-all duration-300 group"
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                data-testid="mobile-menu-toggle"
                aria-expanded={isMenuOpen}
                aria-controls="mobile-menu"
                aria-label={isMenuOpen ? "Close menu" : "Open menu"}
              >
                <div className="relative w-6 h-6">
                  {/* Hamburger to X animation */}
                  <span 
                    className={`absolute block h-0.5 w-6 bg-current transform transition-all duration-300 ${
                      isMenuOpen ? "rotate-45 top-3" : "rotate-0 top-1"
                    }`}
                  />
                  <span 
                    className={`absolute block h-0.5 w-6 bg-current top-3 transition-all duration-300 ${
                      isMenuOpen ? "opacity-0 scale-0" : "opacity-100 scale-100"
                    }`}
                  />
                  <span 
                    className={`absolute block h-0.5 w-6 bg-current transform transition-all duration-300 ${
                      isMenuOpen ? "-rotate-45 top-3" : "rotate-0 top-5"
                    }`}
                  />
                </div>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Menu */}
      <MobileMenu 
        isOpen={isMenuOpen}
        onClose={() => setIsMenuOpen(false)}
        user={user}
        onSignOut={handleSignOut}
      />

      {/* CSS for gradient animation */}
      <style>{`
        @keyframes gradient-shift {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
      `}</style>
    </>
  );
};

export default Header;
