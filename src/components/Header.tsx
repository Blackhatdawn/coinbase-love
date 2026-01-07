import { Button } from "@/components/ui/button";
import { Wallet, Menu, X, LogOut } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

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
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent">
              <Wallet className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="font-display text-xl font-bold">CryptoVault</span>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Markets
            </a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Trade
            </a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Earn
            </a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Learn
            </a>
          </nav>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center gap-3">
            {user ? (
              <>
                <span className="text-sm text-muted-foreground">
                  Hi, {user.name.split(' ')[0]}
                </span>
                <Button variant="ghost" size="sm" onClick={handleSignOut}>
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign Out
                </Button>
              </>
            ) : (
              <>
                <Button variant="ghost" size="sm" asChild>
                  <Link to="/auth">Sign In</Link>
                </Button>
                <Button variant="gradient" size="sm" asChild>
                  <Link to="/auth">Get Started</Link>
                </Button>
              </>
            )}
          </div>

          {/* Mobile Menu Toggle */}
          <button 
            className="md:hidden p-2"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden py-4 border-t border-border/50 animate-slide-up">
            <nav className="flex flex-col gap-4">
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Markets
              </a>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Trade
              </a>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Earn
              </a>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                Learn
              </a>
              <div className="flex flex-col gap-2 pt-4 border-t border-border/50">
                {user ? (
                  <>
                    <span className="text-sm text-muted-foreground px-2">
                      Hi, {user.name}
                    </span>
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
