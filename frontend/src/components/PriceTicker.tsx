import { TrendingUp, TrendingDown } from "lucide-react";

const cryptoData = [
  { symbol: "BTC", name: "Bitcoin", price: 97423.50, change: 2.34 },
  { symbol: "ETH", name: "Ethereum", price: 3456.78, change: -1.23 },
  { symbol: "SOL", name: "Solana", price: 189.45, change: 5.67 },
  { symbol: "XRP", name: "Ripple", price: 2.34, change: 3.21 },
  { symbol: "ADA", name: "Cardano", price: 0.89, change: -0.45 },
  { symbol: "DOGE", name: "Dogecoin", price: 0.32, change: 8.92 },
  { symbol: "AVAX", name: "Avalanche", price: 38.67, change: 1.56 },
  { symbol: "DOT", name: "Polkadot", price: 7.23, change: -2.34 },
];

const PriceTicker = () => {
  const tickerContent = [...cryptoData, ...cryptoData];

  return (
    <div className="bg-secondary/50 border-y border-border/50 overflow-hidden">
      <div className="flex animate-ticker-scroll">
        {tickerContent.map((crypto, index) => (
          <div 
            key={`${crypto.symbol}-${index}`}
            className="flex items-center gap-3 px-6 py-3 whitespace-nowrap"
          >
            <span className="font-semibold text-foreground">{crypto.symbol}</span>
            <span className="text-muted-foreground text-sm">${crypto.price.toLocaleString()}</span>
            <span className={`flex items-center gap-1 text-sm ${crypto.change >= 0 ? 'price-up' : 'price-down'}`}>
              {crypto.change >= 0 ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              {crypto.change >= 0 ? '+' : ''}{crypto.change}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PriceTicker;
