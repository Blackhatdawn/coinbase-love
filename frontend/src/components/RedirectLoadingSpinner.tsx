import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

interface RedirectLoadingSpinnerProps {
  isVisible: boolean;
  onLoadComplete?: () => void;
}

const RedirectLoadingSpinner = ({ isVisible, onLoadComplete }: RedirectLoadingSpinnerProps) => {
  const [show, setShow] = useState(isVisible);

  useEffect(() => {
    setShow(isVisible);

    if (isVisible) {
      // Auto-hide spinner after 3 seconds or when page loads
      const timer = setTimeout(() => {
        setShow(false);
        onLoadComplete?.();
      }, 3000);

      // Also trigger on page load events
      const handleLoad = () => {
        setShow(false);
        onLoadComplete?.();
      };

      window.addEventListener("load", handleLoad);
      document.addEventListener("readystatechange", handleLoad);

      return () => {
        clearTimeout(timer);
        window.removeEventListener("load", handleLoad);
        document.removeEventListener("readystatechange", handleLoad);
      };
    }
  }, [isVisible, onLoadComplete]);

  if (!show) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-background/80 backdrop-blur-sm animate-fade-in">
      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          <Loader2 className="h-12 w-12 text-primary animate-spin" />
          <div className="absolute inset-0 bg-gradient-to-r from-primary to-accent rounded-full opacity-20 animate-pulse" />
        </div>
        <div className="text-center">
          <p className="font-display text-lg font-semibold text-foreground">Loading</p>
          <p className="text-sm text-muted-foreground">Redirecting you now...</p>
        </div>
      </div>
    </div>
  );
};

export default RedirectLoadingSpinner;
