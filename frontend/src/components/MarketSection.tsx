import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { RefreshCw, AlertCircle, TrendingUp, TrendingDown, ExternalLink } from "lucide-react";
import { useCryptoData, formatPrice, formatCompactNumber, formatPercentage } from "@/hooks/useCryptoData";
import { cn } from "@/lib/utils";

/**
 * MarketSection - Live market prices section for homepage
 * Displays real-time prices from CoinGecko via backend proxy
 * NO HARDCODED DATA - All prices are fetched live
 */
const MarketSection = () => {
  const { data, isLoading, error, lastUpdated, refetch, isRefreshing } = useCryptoData({
    refreshInterval: 60000, // Refresh every 60 seconds
    autoRefresh: true,
  });

  // Get top 8 coins for display
  const displayCoins = data.slice(0, 8);

  return (
    <section className="py-20" data-testid="market-section">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10">
          <div>
            <h2 className="font-display text-3xl md:text-4xl font-bold mb-3">
              Live <span className="text-gradient">Market</span> Prices
            </h2>
            <p className="text-muted-foreground max-w-xl">
              Track real-time prices across 200+ cryptocurrencies. Trade with
              confidence using advanced charts and analytics.
            </p>
            {lastUpdated && (
              <p className="text-xs text-muted-foreground mt-2 flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
                </span>
                Live data • Updated {lastUpdated.toLocaleTimeString()}
              </p>
            )}
          </div>
          <div className="flex items-center gap-3 mt-4 md:mt-0">
            <Button
              variant="ghost"
              size="sm"
              onClick={refetch}
              disabled={isRefreshing}
              className="text-muted-foreground"
            >
              <RefreshCw
                className={cn("h-4 w-4 mr-2", isRefreshing && "animate-spin")}
              />
              Refresh
            </Button>
            <Button variant="outline" asChild>
              <Link to="/markets">View All Markets</Link>
            </Button>
          </div>
        </div>

        {/* Loading State - Skeleton Grid */}
        {isLoading && data.length === 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, index) => (
              <div
                key={index}
                className="glass-card p-6 animate-pulse"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-muted" />
                  <div>
                    <div className="h-4 w-16 bg-muted rounded mb-1" />
                    <div className="h-3 w-20 bg-muted rounded" />
                  </div>
                </div>
                <div className="h-6 w-24 bg-muted rounded mb-2" />
                <div className="h-4 w-16 bg-muted rounded" />
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {error && data.length === 0 && (
          <div className="glass-card p-12 text-center">
            <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Failed to Load Market Data</h3>
            <p className="text-muted-foreground mb-6 max-w-md mx-auto">
              We couldn't fetch the latest prices. This might be due to a network issue or our data provider being temporarily unavailable.
            </p>
            <Button onClick={refetch} disabled={isRefreshing}>
              <RefreshCw className={cn("h-4 w-4 mr-2", isRefreshing && "animate-spin")} />
              Try Again
            </Button>
          </div>
        )}

        {/* Data Grid */}
        {displayCoins.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {displayCoins.map((crypto, index) => (
              <Link
                key={crypto.id}
                to={`/trade?coin=${crypto.id}`}
                className="glass-card p-6 hover:border-primary/50 transition-all duration-300 group"
                data-testid={`crypto-card-${crypto.symbol}`}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    {crypto.image ? (
                      <img
                        src={crypto.image}
                        alt={crypto.name}
                        className="w-10 h-10 rounded-full"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center font-bold text-primary">
                        {crypto.symbol.charAt(0)}
                      </div>
                    )}
                    <div>
                      <h3 className="font-semibold group-hover:text-primary transition-colors">
                        {crypto.symbol}
                      </h3>
                      <p className="text-xs text-muted-foreground">{crypto.name}</p>
                    </div>
                  </div>
                  <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>

                {/* Price */}
                <div className="mb-3">
                  <p className="text-2xl font-bold">{formatPrice(crypto.price)}</p>
                </div>

                {/* Change & Stats */}
                <div className="flex items-center justify-between">
                  <span
                    className={cn(
                      "flex items-center gap-1 text-sm font-medium px-2 py-1 rounded-md",
                      crypto.change_24h >= 0
                        ? "text-success bg-success/10"
                        : "text-destructive bg-destructive/10"
                    )}
                  >
                    {crypto.change_24h >= 0 ? (
                      <TrendingUp className="h-3 w-3" />
                    ) : (
                      <TrendingDown className="h-3 w-3" />
                    )}
                    {formatPercentage(crypto.change_24h)}
                  </span>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">
                      MCap: {formatCompactNumber(crypto.market_cap)}
                    </p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* Data Source Attribution */}
        <p className="text-xs text-muted-foreground text-center mt-8">
          Market data provided by CoinGecko API • Prices update every 60 seconds
        </p>
      </div>
    </section>
  );
};

export default MarketSection;
