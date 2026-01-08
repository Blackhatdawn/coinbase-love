import { useState } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import CryptoCard from "@/components/CryptoCard";
import { Search, TrendingUp, TrendingDown } from "lucide-react";

const marketData = [
  { symbol: "BTC", name: "Bitcoin", price: 97423.50, change: 2.34, marketCap: "$1.9T", volume: "$42B", icon: "₿" },
  { symbol: "ETH", name: "Ethereum", price: 3456.78, change: -1.23, marketCap: "$415B", volume: "$18B", icon: "Ξ" },
  { symbol: "SOL", name: "Solana", price: 189.45, change: 5.67, marketCap: "$82B", volume: "$4.2B", icon: "◎" },
  { symbol: "XRP", name: "Ripple", price: 2.34, change: 3.21, marketCap: "$134B", volume: "$8.1B", icon: "✕" },
  { symbol: "ADA", name: "Cardano", price: 0.89, change: -0.45, marketCap: "$31B", volume: "$890M", icon: "₳" },
  { symbol: "DOGE", name: "Dogecoin", price: 0.31, change: 4.56, marketCap: "$45B", volume: "$2.1B", icon: "🐕" },
  { symbol: "AVAX", name: "Avalanche", price: 38.67, change: 1.56, marketCap: "$15B", volume: "$512M", icon: "🔺" },
  { symbol: "DOT", name: "Polkadot", price: 7.23, change: -2.34, marketCap: "$10B", volume: "$312M", icon: "●" },
  { symbol: "LINK", name: "Chainlink", price: 14.89, change: 4.12, marketCap: "$8.7B", volume: "$623M", icon: "⬡" },
  { symbol: "MATIC", name: "Polygon", price: 0.42, change: 2.15, marketCap: "$4.2B", volume: "$287M", icon: "▲" },
  { symbol: "UNI", name: "Uniswap", price: 6.78, change: -0.89, marketCap: "$5.1B", volume: "$145M", icon: "⬢" },
  { symbol: "ATOM", name: "Cosmos", price: 11.34, change: 3.45, marketCap: "$3.4B", volume: "$89M", icon: "⚛" },
];

const Markets = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"price" | "change" | "marketCap">("price");

  const filteredData = marketData.filter(
    (crypto) =>
      crypto.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
      crypto.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const sortedData = [...filteredData].sort((a, b) => {
    switch (sortBy) {
      case "change":
        return b.change - a.change;
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
            {sortedData.length > 0 ? (
              sortedData.map((crypto, index) => (
                <CryptoCard key={crypto.symbol} {...crypto} index={index} />
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
