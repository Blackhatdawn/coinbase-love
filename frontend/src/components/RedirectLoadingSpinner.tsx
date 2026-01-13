import { useEffect, useState } from "react";
import { Shield } from "lucide-react";

interface RedirectLoadingSpinnerProps {
  isVisible: boolean;
  onLoadComplete?: () => void;
}

/**
 * CryptoVault branded loading spinner
 * Shows during page transitions with gold theme
 */
const RedirectLoadingSpinner = ({ isVisible, onLoadComplete }: RedirectLoadingSpinnerProps) => {
  const [show, setShow] = useState(isVisible);
  const [fadeOut, setFadeOut] = useState(false);

  useEffect(() => {
    if (isVisible) {
      setShow(true);
      setFadeOut(false);
      
      // Auto-hide spinner after 3 seconds max
      const timer = setTimeout(() => {
        setFadeOut(true);
        setTimeout(() => {
          setShow(false);
          onLoadComplete?.();
        }, 300);
      }, 3000);

      // Also trigger on page load events
      const handleLoad = () => {
        setFadeOut(true);
        setTimeout(() => {
          setShow(false);
          onLoadComplete?.();
        }, 300);
      };

      window.addEventListener("load", handleLoad);
      document.addEventListener("readystatechange", () => {
        if (document.readyState === "complete") handleLoad();
      });

      return () => {
        clearTimeout(timer);
        window.removeEventListener("load", handleLoad);
      };
    } else {
      setFadeOut(true);
      setTimeout(() => setShow(false), 300);
    }
  }, [isVisible, onLoadComplete]);

  if (!show) return null;

  return (
    <div 
      className={`fixed inset-0 z-[9999] flex items-center justify-center bg-background/95 backdrop-blur-xl transition-opacity duration-300 ${fadeOut ? "opacity-0" : "opacity-100"}`}
      role="progressbar"
      aria-label="Loading"
    >
      <div className="flex flex-col items-center gap-6">
        {/* Animated Logo */}
        <div className="relative">
          {/* Outer ring */}
          <div className="absolute inset-0 rounded-full border-2 border-gold-500/20 scale-150" />
          
          {/* Spinning ring */}
          <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-gold-500 scale-150 animate-spin" style={{ animationDuration: "1s" }} />
          
          {/* Logo container */}
          <div className="relative w-20 h-20 flex items-center justify-center">
            <img 
              src="/favicon.svg" 
              alt="CryptoVault" 
              className="w-14 h-14 object-contain animate-pulse"
            />
            {/* Gold glow */}
            <div className="absolute inset-0 rounded-full bg-gold-500/20 blur-xl animate-pulse" />
          </div>
        </div>

        {/* Brand name */}
        <div className="text-center">
          <h2 className="font-display text-2xl font-bold tracking-tight">
            Crypto<span className="text-gold-400">Vault</span>
          </h2>
          <div className="flex items-center justify-center gap-2 mt-2">
            <div className="flex gap-1">
              <span className="w-2 h-2 rounded-full bg-gold-400 animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 rounded-full bg-gold-400 animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 rounded-full bg-gold-400 animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-3 flex items-center justify-center gap-1">
            <Shield className="h-3 w-3 text-gold-500" />
            Secure connection
          </p>
        </div>
      </div>
    </div>
  );
};

export default RedirectLoadingSpinner;
