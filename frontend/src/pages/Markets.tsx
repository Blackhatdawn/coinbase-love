import { useState, useEffect, useCallback } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import CryptoCard from "@/components/CryptoCard";
import { Search, TrendingUp, TrendingDown, RefreshCw, ArrowUpDown } from "lucide-react";
import { api } from "@/lib/apiClient";
import { cn } from "@/lib/utils";

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
}

const Markets = () => {
  const [marketData, setMarketData] = useState<CryptoData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"price" | "change" | "marketCap">("marketCap");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchMarketData = useCallback(async (isBackground = false) => {
    try {
      if (!isBackground) {
        setIsLoading(true);
      } else {
        setIsRefreshing(true);
      }
      
      const response = await api.crypto.getAll();
      
      let cryptos: any[] = [];
      
      if (response?.cryptocurrencies?.value) {
        try {
          cryptos = JSON.parse(response.cryptocurrencies.value);
        } catch {
          cryptos = response.cryptocurrencies.value;
        }
      } else if (Array.isArray(response?.cryptocurrencies)) {
        cryptos = response.cryptocurrencies;
      } else if (Array.isArray(response)) {
        cryptos = response;
      }
      
      const transformedData = cryptos.map((crypto: any) => ({
        id: crypto.id || crypto.symbol?.toLowerCase() || '',
        symbol: crypto.symbol?.toUpperCase() || crypto.id?.toUpperCase() || '',
        name: crypto.name || '',
        price: crypto.price || 0,
        change24h: crypto.change_24h || 0,
        marketCap: formatMarketCap(crypto.market_cap || 0),
        marketCapRaw: crypto.market_cap || 0,
        volume24h: formatMarketCap(crypto.volume_24h || 0),
        image: crypto.image || ''
      }));
      
      setMarketData(transformedData);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to fetch market data:", error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchMarketData();
  }, [fetchMarketData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchMarketData(true);
    }, 30000);
    
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
      <Header />
      <main className="pt-20 sm:pt-24 pb-16 sm:pb-20">
        <div className="container mx-auto px-4 sm:px-6">
          {/* Header */}
          <div className="mb-8 sm:mb-12 animate-fade-in">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-3">
              <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold">
                Cryptocurrency <span className="text-gradient">Markets</span>
              </h1>
              
              {/* Last Updated & Refresh */}
              <div className="flex items-center gap-2 text-xs sm:text-sm text-muted-foreground">
                {lastUpdated && (
                  <span>Updated {lastUpdated.toLocaleTimeString()}</span>
                )}
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
              Track the latest prices, charts, and market data for 200+ cryptocurrencies in real-time.
            </p>
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
            
            {/* Sort Buttons - Scrollable on mobile */}
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

          {/* Markets Table/Cards */}
          {isLoading ? (
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
          ) : sortedData.length > 0 ? (
            <div className="space-y-3 sm:space-y-4">
              {sortedData.map((crypto, index) => (
                <div
                  key={crypto.id}
                  className="glass-card p-4 sm:p-6 rounded-xl border border-gold-500/10 hover:border-gold-500/30 transition-all duration-300 hover:shadow-lg hover:shadow-gold-500/5 cursor-pointer"
                  style={{ animationDelay: `${index * 50}ms` }}
                  data-testid={`market-card-${crypto.symbol}`}
                >
                  <div className="flex items-center gap-3 sm:gap-4">
                    {/* Rank */}
                    <div className="hidden sm:flex h-8 w-8 items-center justify-center text-sm text-muted-foreground font-mono">
                      #{index + 1}
                    </div>
                    
                    {/* Coin Icon & Name */}
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      {crypto.image ? (
                        <img 
                          src={crypto.image} 
                          alt={crypto.name}
                          className="h-10 w-10 sm:h-12 sm:w-12 rounded-full flex-shrink-0"
                        />
                      ) : (
                        <div className="h-10 w-10 sm:h-12 sm:w-12 rounded-full bg-gold-500/20 flex items-center justify-center text-gold-400 font-bold flex-shrink-0">
                          {crypto.symbol.charAt(0)}
                        </div>
                      )}
                      <div className="min-w-0">
                        <div className="font-semibold text-base sm:text-lg truncate">{crypto.name}</div>
                        <div className="text-sm text-muted-foreground">{crypto.symbol}</div>
                      </div>
                    </div>
                    
                    {/* Price & Change */}
                    <div className="text-right flex-shrink-0">
                      <div className="font-mono font-semibold text-base sm:text-lg">
                        {formatPrice(crypto.price)}
                      </div>
                      <div className={cn(
                        "flex items-center justify-end gap-1 text-sm sm:text-base font-medium",
                        crypto.change24h >= 0 
                          ? "text-emerald-500" 
                          : "text-red-500"
                      )}>
                        {crypto.change24h >= 0 ? (
                          <TrendingUp className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                        ) : (
                          <TrendingDown className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                        )}
                        <span className={cn(
                          "px-1.5 py-0.5 rounded text-xs sm:text-sm",
                          crypto.change24h >= 0 
                            ? "bg-emerald-500/10" 
                            : "bg-red-500/10"
                        )}>
                          {crypto.change24h >= 0 ? '+' : ''}{crypto.change24h.toFixed(2)}%
                        </span>
                      </div>
                    </div>
                    
                    {/* Market Cap & Volume - Hidden on small screens */}
                    <div className="hidden md:block text-right min-w-[100px]">
                      <div className="text-sm text-muted-foreground">Market Cap</div>
                      <div className="font-mono text-sm">{crypto.marketCap}</div>
                    </div>
                    
                    <div className="hidden lg:block text-right min-w-[100px]">
                      <div className="text-sm text-muted-foreground">24h Volume</div>
                      <div className="font-mono text-sm">{crypto.volume24h}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 sm:py-16">
              <Search className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
              <p className="text-muted-foreground text-base sm:text-lg">
                No cryptocurrencies found matching "{searchQuery}"
              </p>
              <button 
                onClick={() => setSearchQuery("")}
                className="mt-4 text-gold-400 hover:text-gold-300 hover:underline min-h-[44px]"
              >
                Clear search
              </button>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Markets;
