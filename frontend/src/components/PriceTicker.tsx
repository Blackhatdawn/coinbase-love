import { TrendingUp, TrendingDown, RefreshCw, AlertCircle } from "lucide-react";
import { useCryptoData, formatPrice, formatPercentage } from "@/hooks/useCryptoData";
import { cn } from "@/lib/utils";

/**
 * PriceTicker - Real-time cryptocurrency price ticker
 * Displays live prices from CoinGecko via backend proxy
 * NO HARDCODED DATA - All prices are fetched live
 */
const PriceTicker = () => {
  const { data, isLoading, error, isRefreshing } = useCryptoData({
    refreshInterval: 30000, // Refresh every 30 seconds
    autoRefresh: true,
  });

  // Show skeleton loader while loading
  if (isLoading && data.length === 0) {
    return (
      <div className="bg-background/80 border-y border-gold-500/10 overflow-hidden backdrop-blur-sm">
        <div className="flex animate-ticker-scroll">
          {Array.from({ length: 16 }).map((_, index) => (
            <div
              key={index}
              className="flex items-center gap-3 px-6 py-3 whitespace-nowrap"
            >
              <div className="h-4 w-10 bg-gold-500/10 animate-pulse rounded" />
              <div className="h-4 w-20 bg-gold-500/10 animate-pulse rounded" />
              <div className="h-4 w-14 bg-gold-500/10 animate-pulse rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Show error state with retry option
  if (error && data.length === 0) {
    return (
      <div className="bg-destructive/10 border-y border-destructive/20 py-3">
        <div className="container mx-auto px-4 flex items-center justify-center gap-3 text-sm">
          <AlertCircle className="h-4 w-4 text-destructive" />
          <span className="text-destructive">Failed to load market data</span>
          <button
            onClick={() => window.location.reload()}
            className="text-gold-400 hover:text-gold-300 hover:underline flex items-center gap-1"
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

      <div className="flex animate-ticker-scroll">
        {tickerContent.map((crypto, index) => (
          <div
            key={`${crypto.symbol}-${index}`}
            className="flex items-center gap-3 px-6 py-3 whitespace-nowrap"
            data-testid={`ticker-${crypto.symbol}`}
          >
            <span className="font-semibold text-gold-400">
              {crypto.symbol}
            </span>
            <span className="text-muted-foreground text-sm">
              {formatPrice(crypto.price)}
            </span>
            <span
              className={cn(
                "flex items-center gap-1 text-sm",
                crypto.change_24h >= 0 ? "text-success" : "text-destructive"
              )}
            >
              {crypto.change_24h >= 0 ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              {formatPercentage(crypto.change_24h)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PriceTicker;
