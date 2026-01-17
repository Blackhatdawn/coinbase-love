import { useState, useEffect, useCallback, useRef } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, TrendingUp, TrendingDown, RefreshCw, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import { api } from "@/lib/apiClient";
import { cn } from "@/lib/utils";
import { usePriceWebSocket } from "@/hooks/usePriceWebSocket";
import { PriceStreamStatus } from "@/components/PriceStreamStatus";
import { Link } from "react-router-dom";

interface CryptoData {
  id: string;
  symbol: string;
  name: string;
  price: number;
  change24h: number;
  marketCap: string;
  marketCapRaw: number;
  volume24h: string;
  image?: string;
  previousPrice?: number;
  priceDirection?: 'up' | 'down' | 'neutral';
  flashClass?: string;
}

const Markets = () => {
  const [marketData, setMarketData] = useState<CryptoData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"price" | "change" | "marketCap">("marketCap");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const { prices, status } = usePriceWebSocket();
  const previousPricesRef = useRef<Record<string, number>>({});

  const fetchMarketData = useCallback(async (isBackground = false) => {
    try {
      if (!isBackground) {
        setIsLoading(true);
        setError(null);
      } else {
        setIsRefreshing(true);
      }

      const response = await api.crypto.getAll();
      const cryptos = Array.isArray(response?.cryptocurrencies) ? response.cryptocurrencies : [];

      if (cryptos.length === 0) {
        throw new Error('No cryptocurrency data available');
      }

      const transformedData = cryptos.map((crypto: any) => {
        const id = crypto.id || crypto.symbol?.toLowerCase() || '';
        const currentPrice = crypto.price || 0;
        const previousPrice = previousPricesRef.current[id];
        
        let priceDirection: 'up' | 'down' | 'neutral' = 'neutral';
        if (previousPrice !== undefined && currentPrice !== previousPrice) {
          priceDirection = currentPrice > previousPrice ? 'up' : 'down';
        }
        
        // Store current price for next comparison
        previousPricesRef.current[id] = currentPrice;

        return {
          id,
          symbol: crypto.symbol?.toUpperCase() || crypto.id?.toUpperCase() || '',
          name: crypto.name || '',
          price: currentPrice,
          change24h: crypto.change_24h || 0,
          marketCap: formatMarketCap(crypto.market_cap || 0),
          marketCapRaw: crypto.market_cap || 0,
          volume24h: formatMarketCap(crypto.volume_24h || 0),
          image: crypto.image || '',
          previousPrice,
          priceDirection,
          flashClass: priceDirection === 'up' ? 'flash-green' : priceDirection === 'down' ? 'flash-red' : ''
        };
      });

      setMarketData(transformedData);
      setLastUpdated(new Date());
    } catch (error: any) {
      const errorMessage = error?.message || 'Failed to fetch cryptocurrency data. Please try again.';
      console.error("Failed to fetch market data:", error);
      setError(errorMessage);
      setMarketData([]);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchMarketData();
  }, [fetchMarketData]);

  // Auto-refresh every 3 seconds for live fluctuation
  useEffect(() => {
    const interval = setInterval(() => {
      fetchMarketData(true);
    }, 3000);
    
    return () => clearInterval(interval);
  }, [fetchMarketData]);

  const formatMarketCap = (num: number): string => {
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return `$${num.toLocaleString()}`;
  };

  const formatPrice = (price: number): string => {
    if (price >= 1000) {
      return price.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 });
    } else if (price >= 1) {
      return price.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 4 });
    } else {
      return price.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 4, maximumFractionDigits: 8 });
    }
  };

  const filteredData = marketData.filter(
    (crypto) =>
      crypto.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
      crypto.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const sortedData = [...filteredData].sort((a, b) => {
    switch (sortBy) {
      case "change":
        return b.change24h - a.change24h;
      case "marketCap":
        return b.marketCapRaw - a.marketCapRaw;
      default:
        return b.price - a.price;
    }
  });

  return (
    <div className="min-h-screen bg-background">
      <style>{`
        @keyframes flash-green {
          0%, 100% { background-color: transparent; }
          50% { background-color: rgba(34, 197, 94, 0.15); }
        }
        @keyframes flash-red {
          0%, 100% { background-color: transparent; }
          50% { background-color: rgba(239, 68, 68, 0.15); }
        }
        @keyframes price-pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
        .flash-green {
          animation: flash-green 0.6s ease-in-out;
        }
        .flash-red {
          animation: flash-red 0.6s ease-in-out;
        }
        .price-pulse {
          animation: price-pulse 0.3s ease-in-out;
        }
      `}</style>
      <Header />
      <main className="pt-20 sm:pt-24 pb-16 sm:pb-20">
        <div className="container mx-auto px-4 sm:px-6">
          {/* Header */}
          <div className="mb-8 sm:mb-12 animate-fade-in">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-3">
              <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold">
                Cryptocurrency <span className="text-gradient">Markets</span>
              </h1>

              {/* Status & Controls */}
              <div className="flex flex-col sm:flex-row sm:items-center gap-3 text-xs sm:text-sm">
                {/* Price Stream Status */}
                <PriceStreamStatus status={status} />

                {/* Live indicator */}
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/30">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                  </span>
                  <span className="text-green-400 font-mono text-xs">LIVE</span>
                </div>

                {/* Refresh Button */}
                <button
                  onClick={() => fetchMarketData(true)}
                  disabled={isRefreshing}
                  className="p-2 hover:bg-gold-500/10 rounded-lg transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
                  aria-label="Refresh data"
                >
                  <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin text-gold-400")} />
                </button>
              </div>
            </div>
            <p className="text-base sm:text-lg text-muted-foreground max-w-2xl">
              Track the latest prices and market data for cryptocurrencies in real-time. Prices update every 3 seconds.
            </p>
            {lastUpdated && (
              <p className="text-xs text-muted-foreground mt-2">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </p>
            )}
          </div>

          {/* Search and Filter */}
          <div className="flex flex-col gap-4 mb-6 sm:mb-8">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                placeholder="Search cryptocurrencies..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 h-12 text-base"
                data-testid="markets-search"
              />
            </div>
            
            {/* Sort Buttons */}
            <div className="flex gap-2 overflow-x-auto pb-2 -mx-4 px-4 sm:mx-0 sm:px-0 sm:overflow-visible">
              <Button
                variant={sortBy === "marketCap" ? "default" : "outline"}
                onClick={() => setSortBy("marketCap")}
                className={cn(
                  "flex-shrink-0 min-h-[44px]",
                  sortBy === "marketCap" && "bg-gold-500 hover:bg-gold-600 text-black"
                )}
              >
                <ArrowUpDown className="h-4 w-4 mr-2" />
                Market Cap
              </Button>
              <Button
                variant={sortBy === "price" ? "default" : "outline"}
                onClick={() => setSortBy("price")}
                className={cn(
                  "flex-shrink-0 min-h-[44px]",
                  sortBy === "price" && "bg-gold-500 hover:bg-gold-600 text-black"
                )}
              >
                Price
              </Button>
              <Button
                variant={sortBy === "change" ? "default" : "outline"}
                onClick={() => setSortBy("change")}
                className={cn(
                  "flex-shrink-0 min-h-[44px]",
                  sortBy === "change" && "bg-gold-500 hover:bg-gold-600 text-black"
                )}
              >
                <TrendingUp className="h-4 w-4 mr-2" />
                24h Change
              </Button>
            </div>
          </div>

          {/* Error State */}
          {error && (
            <div className="mb-6 p-4 sm:p-6 rounded-xl border border-red-500/30 bg-red-500/10">
              <div className="flex items-start gap-3">
                <div className="text-red-500 text-lg">⚠</div>
                <div>
                  <p className="font-semibold text-red-400 text-base sm:text-lg">{error}</p>
                  <button
                    onClick={() => fetchMarketData()}
                    className="mt-2 text-red-400 hover:text-red-300 hover:underline text-sm min-h-[44px]"
                  >
                    Try again
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Markets Table/Cards */}
          {isLoading && !error ? (
            <div className="space-y-4">
              {Array.from({ length: 6 }).map((_, index) => (
                <div 
                  key={index} 
                  className="glass-card p-4 sm:p-6 rounded-xl border border-gold-500/10 animate-pulse"
                >
                  <div className="flex items-center gap-4">
                    <div className="h-10 w-10 sm:h-12 sm:w-12 rounded-full bg-gold-500/10" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 w-20 bg-gold-500/10 rounded" />
                      <div className="h-3 w-16 bg-gold-500/10 rounded" />
                    </div>
                    <div className="text-right space-y-2">
                      <div className="h-5 w-24 bg-gold-500/10 rounded ml-auto" />
                      <div className="h-4 w-16 bg-gold-500/10 rounded ml-auto" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : sortedData.length === 0 ? (
            <div className="text-center py-12 sm:py-16">
              <div className="text-5xl sm:text-6xl mb-4">🔍</div>
              <h3 className="text-lg sm:text-xl font-semibold mb-2">No cryptocurrencies found</h3>
              <p className="text-muted-foreground">Try adjusting your search query</p>
            </div>
          ) : (
            <div className="space-y-3">
              {sortedData.map((crypto) => (
                <Link
                  key={crypto.id}
                  to={`/trade?coin=${crypto.id}`}
                  className={cn(
                    "glass-card p-4 sm:p-6 rounded-xl border border-gold-500/10 hover:border-gold-500/30 transition-all hover:scale-[1.01] cursor-pointer block",
                    crypto.flashClass
                  )}
                  data-testid={`crypto-card-${crypto.symbol.toLowerCase()}`}
                >
                  <div className="flex items-center gap-3 sm:gap-4">
                    {/* Icon/Logo */}
                    <div className="flex-shrink-0">
                      <div className="h-10 w-10 sm:h-12 sm:w-12 rounded-full bg-gradient-to-br from-gold-400/20 to-gold-600/20 flex items-center justify-center border border-gold-500/20">
                        <span className="text-base sm:text-lg font-bold text-gold-400">
                          {crypto.symbol.substring(0, 2)}
                        </span>
                      </div>
                    </div>

                    {/* Name & Symbol */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-base sm:text-lg truncate">{crypto.name}</h3>
                        {crypto.priceDirection !== 'neutral' && (
                          <span className="price-pulse">
                            {crypto.priceDirection === 'up' ? (
                              <ArrowUp className="h-4 w-4 text-green-500" />
                            ) : (
                              <ArrowDown className="h-4 w-4 text-red-500" />
                            )}
                          </span>
                        )}
                      </div>
                      <p className="text-xs sm:text-sm text-muted-foreground font-mono">{crypto.symbol}</p>
                    </div>

                    {/* Price & Change */}
                    <div className="text-right">
                      <p className={cn(
                        "text-base sm:text-xl font-bold font-mono transition-all",
                        crypto.priceDirection === 'up' && "text-green-500",
                        crypto.priceDirection === 'down' && "text-red-500"
                      )}>
                        {formatPrice(crypto.price)}
                      </p>
                      <p className={cn(
                        "text-xs sm:text-sm font-semibold flex items-center justify-end gap-1",
                        crypto.change24h >= 0 ? "text-green-500" : "text-red-500"
                      )}>
                        {crypto.change24h >= 0 ? (
                          <TrendingUp className="h-3 w-3" />
                        ) : (
                          <TrendingDown className="h-3 w-3" />
                        )}
                        {crypto.change24h >= 0 ? "+" : ""}{crypto.change24h.toFixed(2)}%
                      </p>
                    </div>
                  </div>

                  {/* Additional Info */}
                  <div className="mt-3 pt-3 border-t border-gold-500/10 grid grid-cols-2 gap-2 text-xs sm:text-sm">
                    <div>
                      <p className="text-muted-foreground">Market Cap</p>
                      <p className="font-semibold font-mono">{crypto.marketCap}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-muted-foreground">24h Volume</p>
                      <p className="font-semibold font-mono">{crypto.volume24h}</p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Markets;