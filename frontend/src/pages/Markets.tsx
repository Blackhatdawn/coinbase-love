import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import CryptoCard from "@/components/CryptoCard";
import { Search, TrendingUp, TrendingDown } from "lucide-react";
import { api } from "@/lib/api";

interface CryptoData {
  symbol: string;
  name: string;
  price: number;
  change24h: number;
  marketCap: string;
  volume24h: string;
}

const Markets = () => {
  const [marketData, setMarketData] = useState<CryptoData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"price" | "change" | "marketCap">("price");

  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        setIsLoading(true);
        const response = await api.crypto.getAll();
        // Backend returns { cryptocurrencies: [...] }
        const cryptos = response.cryptocurrencies || [];
        
        // Transform backend data to match frontend interface
        const transformedData = cryptos.map((crypto: any) => ({
          symbol: crypto.symbol,
          name: crypto.name,
          price: crypto.price,
          change24h: crypto.change_24h,
          marketCap: `$${(crypto.market_cap / 1e9).toFixed(2)}B`,
          volume24h: `$${(crypto.volume_24h / 1e9).toFixed(2)}B`
        }));
        
        setMarketData(transformedData);
      } catch (error) {
        console.error("Failed to fetch market data:", error);
        // Fallback to empty array if API fails
        setMarketData([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMarketData();
  }, []);

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
        return parseFloat(b.marketCap.replace(/[$BTG,]/g, "")) - parseFloat(a.marketCap.replace(/[$BTG,]/g, ""));
      default:
        return b.price - a.price;
    }
  });

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-24 pb-20">
        <div className="container mx-auto px-4">
          {/* Header */}
          <div className="mb-12 animate-fade-in">
            <h1 className="font-display text-4xl md:text-5xl font-bold mb-3">
              Cryptocurrency <span className="text-gradient">Markets</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl">
              Track the latest prices, charts, and market data for 200+ cryptocurrencies in real-time.
            </p>
          </div>

          {/* Search and Filter */}
          <div className="flex flex-col md:flex-row gap-4 mb-8">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                placeholder="Search cryptocurrencies..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 h-11"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={sortBy === "price" ? "default" : "outline"}
                onClick={() => setSortBy("price")}
              >
                Price
              </Button>
              <Button
                variant={sortBy === "change" ? "default" : "outline"}
                onClick={() => setSortBy("change")}
              >
                <TrendingUp className="h-4 w-4 mr-2" />
                Change
              </Button>
              <Button
                variant={sortBy === "marketCap" ? "default" : "outline"}
                onClick={() => setSortBy("marketCap")}
              >
                <TrendingDown className="h-4 w-4 mr-2" />
                Market Cap
              </Button>
            </div>
          </div>

          {/* Markets Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {isLoading ? (
              <div className="col-span-full text-center py-12">
                <p className="text-muted-foreground text-lg">Loading market data...</p>
              </div>
            ) : sortedData.length > 0 ? (
              sortedData.map((crypto, index) => (
                <CryptoCard
                  key={crypto.symbol}
                  symbol={crypto.symbol}
                  name={crypto.name}
                  price={crypto.price}
                  change={crypto.change24h}
                  marketCap={crypto.marketCap}
                  volume={crypto.volume24h}
                  icon="₿"
                  index={index}
                />
              ))
            ) : (
              <div className="col-span-full text-center py-12">
                <p className="text-muted-foreground text-lg">No cryptocurrencies found matching your search.</p>
              </div>
            )}
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Markets;
