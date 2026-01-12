import { Button } from "@/components/ui/button";
import { Wallet, Menu, X, LogOut, ChevronDown } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { WalletConnect } from "@/components/WalletConnect";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const auth = useAuth();
  const navigate = useNavigate();

  const user = auth?.user ?? null;
  const signOut = auth?.signOut ?? (() => {});

  const handleSignOut = () => {
    signOut();
    navigate("/");
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl" data-testid="header">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2" data-testid="logo-link">
            <img 
              src="/cryptovault-logo.png" 
              alt="CryptoVault" 
              className="h-9 w-9 object-contain"
            />
            <span className="font-display text-xl font-bold">CryptoVault</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <DropdownMenu>
              <DropdownMenuTrigger className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
                Company <ChevronDown className="h-4 w-4" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-48">
                <DropdownMenuItem asChild>
                  <Link to="/about" className="w-full cursor-pointer">About Us</Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/services" className="w-full cursor-pointer">Services</Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/security" className="w-full cursor-pointer">Security & Compliance</Link>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            
            <Link to="/markets" className="text-sm text-muted-foreground hover:text-foreground transition-colors" data-testid="nav-markets">
              Markets
            </Link>
            <Link to="/trade" className="text-sm text-muted-foreground hover:text-foreground transition-colors" data-testid="nav-trade">
              Trade
            </Link>
            <Link to="/earn" className="text-sm text-muted-foreground hover:text-foreground transition-colors" data-testid="nav-earn">
              Earn
            </Link>
            
            <DropdownMenu>
              <DropdownMenuTrigger className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
                Resources <ChevronDown className="h-4 w-4" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-48">
                <DropdownMenuItem asChild>
                  <Link to="/learn" className="w-full cursor-pointer">Learn</Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/faq" className="w-full cursor-pointer">FAQ</Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link to="/contact" className="w-full cursor-pointer">Contact</Link>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </nav>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center gap-3">
            {user && <WalletConnect />}
            {user ? (
              <>
                <Button variant="ghost" size="sm" asChild data-testid="nav-dashboard">
                  <Link to="/dashboard">Dashboard</Link>
                </Button>
                <Button variant="ghost" size="sm" onClick={handleSignOut} data-testid="nav-signout">
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign Out
                </Button>
              </>
            ) : (
              <>
                <Button variant="ghost" size="sm" asChild data-testid="nav-signin">
                  <Link to="/auth">Sign In</Link>
                </Button>
                <Button variant="gradient" size="sm" asChild data-testid="nav-get-started">
                  <Link to="/auth">Get Started</Link>
                </Button>
              </>
            )}
          </div>

          {/* Mobile Menu Toggle */}
          <button 
            className="md:hidden p-2"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            data-testid="mobile-menu-toggle"
          >
            {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden py-4 border-t border-border/50 animate-slide-up" data-testid="mobile-menu">
            <nav className="flex flex-col gap-4">
              <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Company</div>
              <Link to="/about" className="text-sm text-muted-foreground hover:text-foreground transition-colors pl-2">
                About Us
              </Link>
              <Link to="/services" className="text-sm text-muted-foreground hover:text-foreground transition-colors pl-2">
                Services
              </Link>
              <Link to="/security" className="text-sm text-muted-foreground hover:text-foreground transition-colors pl-2">
                Security & Compliance
              </Link>
              
              <div className="text-xs text-muted-foreground uppercase tracking-wider mt-4 mb-1">Trading</div>
              <Link to="/markets" className="text-sm text-muted-foreground hover:text-foreground transition-colors pl-2">
                Markets
              </Link>
              <Link to="/trade" className="text-sm text-muted-foreground hover:text-foreground transition-colors pl-2">
                Trade
              </Link>
              <Link to="/earn" className="text-sm text-muted-foreground hover:text-foreground transition-colors pl-2">
                Earn
              </Link>
              
              <div className="text-xs text-muted-foreground uppercase tracking-wider mt-4 mb-1">Resources</div>
              <Link to="/learn" className="text-sm text-muted-foreground hover:text-foreground transition-colors pl-2">
                Learn
              </Link>
              <Link to="/faq" className="text-sm text-muted-foreground hover:text-foreground transition-colors pl-2">
                FAQ
              </Link>
              <Link to="/contact" className="text-sm text-muted-foreground hover:text-foreground transition-colors pl-2">
                Contact
              </Link>
              
              <div className="flex flex-col gap-2 pt-4 border-t border-border/50 mt-4">
                {user ? (
                  <>
                    <Button variant="ghost" size="sm" className="justify-start" asChild>
                      <Link to="/dashboard">Dashboard</Link>
                    </Button>
                    <Button variant="ghost" size="sm" className="justify-start" onClick={handleSignOut}>
                      <LogOut className="h-4 w-4 mr-2" />
                      Sign Out
                    </Button>
                  </>
                ) : (
                  <>
                    <Button variant="ghost" size="sm" className="justify-start" asChild>
                      <Link to="/auth">Sign In</Link>
                    </Button>
                    <Button variant="gradient" size="sm" asChild>
                      <Link to="/auth">Get Started</Link>
                    </Button>
                  </>
                )}
              </div>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
