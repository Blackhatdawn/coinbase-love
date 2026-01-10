import CryptoCard from "./CryptoCard";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

const marketData = [
  { symbol: "BTC", name: "Bitcoin", price: 97423.50, change: 2.34, marketCap: "$1.9T", volume: "$42B", icon: "₿" },
  { symbol: "ETH", name: "Ethereum", price: 3456.78, change: -1.23, marketCap: "$415B", volume: "$18B", icon: "Ξ" },
  { symbol: "SOL", name: "Solana", price: 189.45, change: 5.67, marketCap: "$82B", volume: "$4.2B", icon: "◎" },
  { symbol: "XRP", name: "Ripple", price: 2.34, change: 3.21, marketCap: "$134B", volume: "$8.1B", icon: "✕" },
  { symbol: "ADA", name: "Cardano", price: 0.89, change: -0.45, marketCap: "$31B", volume: "$890M", icon: "₳" },
  { symbol: "AVAX", name: "Avalanche", price: 38.67, change: 1.56, marketCap: "$15B", volume: "$512M", icon: "🔺" },
  { symbol: "DOT", name: "Polkadot", price: 7.23, change: -2.34, marketCap: "$10B", volume: "$312M", icon: "●" },
  { symbol: "LINK", name: "Chainlink", price: 14.89, change: 4.12, marketCap: "$8.7B", volume: "$623M", icon: "⬡" },
];

const MarketSection = () => {
  return (
    <section className="py-20">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10">
          <div>
            <h2 className="font-display text-3xl md:text-4xl font-bold mb-3">
              Live <span className="text-gradient">Market</span> Prices
            </h2>
            <p className="text-muted-foreground max-w-xl">
              Track real-time prices across 200+ cryptocurrencies. Trade with confidence using advanced charts and analytics.
            </p>
          </div>
          <Button variant="outline" className="mt-4 md:mt-0" asChild>
            <Link to="/markets">
              View All Markets
            </Link>
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {marketData.map((crypto, index) => (
            <CryptoCard key={crypto.symbol} {...crypto} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
};

export default MarketSection;
