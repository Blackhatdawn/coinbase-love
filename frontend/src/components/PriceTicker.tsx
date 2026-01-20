import { TrendingUp, TrendingDown, RefreshCw, AlertCircle } from "lucide-react";
import { useCryptoData, formatPrice, formatPercentage } from "@/hooks/useCryptoData";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";

/**
 * PriceTicker - Real-time cryptocurrency price ticker
 * Displays live prices from CoinCap via backend proxy
 * Mobile-first responsive design with smooth animations
 */
const PriceTicker = () => {
  const { data, isLoading, error, isRefreshing } = useCryptoData({
    refreshInterval: 15000, // Refresh every 15 seconds for real-time feel
    autoRefresh: true,
  });

  // Track previous prices for flash animation
  const [prevPrices, setPrevPrices] = useState<Record<string, number>>({});
  const [flashingCoins, setFlashingCoins] = useState<Record<string, 'up' | 'down' | null>>({});

  // Detect price changes and trigger flash animation
  useEffect(() => {
    if (data.length === 0) return;

    const newFlashing: Record<string, 'up' | 'down' | null> = {};
    
    data.forEach(crypto => {
      const prevPrice = prevPrices[crypto.symbol];
      if (prevPrice !== undefined && prevPrice !== crypto.price) {
        newFlashing[crypto.symbol] = crypto.price > prevPrice ? 'up' : 'down';
      }
    });

    if (Object.keys(newFlashing).length > 0) {
      setFlashingCoins(newFlashing);
      // Clear flash after animation
      setTimeout(() => setFlashingCoins({}), 1000);
    }

    // Update previous prices
    const newPrevPrices: Record<string, number> = {};
    data.forEach(crypto => {
      newPrevPrices[crypto.symbol] = crypto.price;
    });
    setPrevPrices(newPrevPrices);
  }, [data]);

  // Show skeleton loader while loading
  if (isLoading && data.length === 0) {
    return (
      <div className="bg-background/80 border-y border-gold-500/10 overflow-hidden backdrop-blur-sm">
        <div className="flex animate-ticker-scroll">
          {Array.from({ length: 16 }).map((_, index) => (
            <div
              key={index}
              className="flex items-center gap-2 sm:gap-3 px-4 sm:px-6 py-2.5 sm:py-3 whitespace-nowrap"
            >
              <div className="h-4 w-8 sm:w-10 bg-gold-500/10 animate-pulse rounded" />
              <div className="h-4 w-16 sm:w-20 bg-gold-500/10 animate-pulse rounded" />
              <div className="h-4 w-12 sm:w-14 bg-gold-500/10 animate-pulse rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Show error state with retry option
  if (error && data.length === 0) {
    return (
      <div className="bg-destructive/10 border-y border-destructive/20 py-2.5 sm:py-3">
        <div className="container mx-auto px-4 flex items-center justify-center gap-2 sm:gap-3 text-xs sm:text-sm">
          <AlertCircle className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-destructive flex-shrink-0" />
          <span className="text-destructive">Failed to load market data</span>
          <button
            onClick={() => window.location.reload()}
            className="text-gold-400 hover:text-gold-300 hover:underline flex items-center gap-1 min-h-[44px] px-2"
          >
            <RefreshCw className="h-3 w-3" />
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Duplicate data for seamless scroll animation
  const tickerContent = [...data, ...data];

  return (
    <div className="bg-background/80 border-y border-gold-500/10 overflow-hidden relative backdrop-blur-sm">
      {/* Refreshing indicator */}
      {isRefreshing && (
        <div className="absolute top-1 right-2 z-10">
          <RefreshCw className="h-3 w-3 animate-spin text-gold-400" />
        </div>
      )}

      {/* Gradient fade edges for better visual */}
      <div className="absolute left-0 top-0 bottom-0 w-8 sm:w-16 bg-gradient-to-r from-background to-transparent z-10 pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-8 sm:w-16 bg-gradient-to-l from-background to-transparent z-10 pointer-events-none" />

      <div className="flex animate-ticker-scroll">
        {tickerContent.map((crypto, index) => {
          const isFlashing = flashingCoins[crypto.symbol];
          
          return (
            <div
              key={`${crypto.symbol}-${index}`}
              className={cn(
                "flex items-center gap-2 sm:gap-3 px-4 sm:px-6 py-2.5 sm:py-3 whitespace-nowrap transition-all duration-300",
                isFlashing === 'up' && "bg-emerald-500/10",
                isFlashing === 'down' && "bg-red-500/10"
              )}
              data-testid={`ticker-${crypto.symbol}`}
            >
              {/* Coin Image (optional, shown on larger screens) */}
              {crypto.image && (
                <img 
                  src={crypto.image} 
                  alt={crypto.name}
                  className="hidden sm:block h-5 w-5 rounded-full"
                />
              )}
              
              <span className="font-semibold text-gold-400 text-sm sm:text-base">
                {crypto.symbol}
              </span>
              
              <span className={cn(
                "text-xs sm:text-sm font-mono transition-colors duration-300",
                isFlashing === 'up' && "text-emerald-400",
                isFlashing === 'down' && "text-red-400",
                !isFlashing && "text-muted-foreground"
              )}>
                {formatPrice(crypto.price)}
              </span>
              
              <span
                className={cn(
                  "flex items-center gap-0.5 sm:gap-1 text-xs sm:text-sm font-medium",
                  crypto.change_24h >= 0 
                    ? "text-emerald-500" 
                    : "text-red-500"
                )}
              >
                {crypto.change_24h >= 0 ? (
                  <TrendingUp className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                ) : (
                  <TrendingDown className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                )}
                {formatPercentage(crypto.change_24h)}
              </span>
            </div>
          );
        })}
      </div>

      <style>{`
        @keyframes ticker-scroll {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-ticker-scroll {
          animation: ticker-scroll 45s linear infinite;
        }
        .animate-ticker-scroll:hover {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
};

export default PriceTicker;
