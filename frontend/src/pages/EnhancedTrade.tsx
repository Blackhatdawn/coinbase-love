/**
 * EnhancedTrade - Professional Trading Dashboard
 * Bybit-style trading interface with charts and order book
 */
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { TradingChart } from "@/components/TradingChart";
import { GasEstimator } from "@/components/GasEstimator";
import { TransactionSigner } from "@/components/TransactionSigner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useWeb3 } from "@/contexts/Web3Context";
import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/lib/apiClient";
import { 
  Wallet, 
  TrendingUp, 
  TrendingDown,
  BarChart3, 
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  Zap,
  Info,
  Loader2
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import DashboardCard from "@/components/dashboard/DashboardCard";

interface CryptoData {
  id: string;
  symbol: string;
  name: string;
  price: number;
  change_24h: number;
  market_cap: number;
  volume_24h: number;
  image: string;
}

const EnhancedTrade = () => {
  const auth = useAuth();
  const user = auth?.user ?? null;
  const { isConnected, account } = useWeb3();

  const [cryptoList, setCryptoList] = useState<CryptoData[]>([]);
  const [selectedCoin, setSelectedCoin] = useState<CryptoData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showBuyModal, setShowBuyModal] = useState(false);
  const [showSellModal, setShowSellModal] = useState(false);
  
  // Order form state
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market');
  const [orderSide, setOrderSide] = useState<'buy' | 'sell'>('buy');
  const [orderAmount, setOrderAmount] = useState('');
  const [limitPrice, setLimitPrice] = useState('');

  // Fetch cryptocurrencies
  useEffect(() => {
    const fetchCryptos = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await api.crypto.getAll();
        const cryptos = Array.isArray(response?.cryptocurrencies)
          ? response.cryptocurrencies
          : [];

        if (cryptos.length === 0) {
          throw new Error('No cryptocurrency data available');
        }

        setCryptoList(cryptos);
        if (cryptos.length > 0) {
          setSelectedCoin(cryptos[0]);
        }
      } catch (error: any) {
        console.error("Failed to fetch cryptocurrencies:", error);
        const errorMessage = error?.message || 'Failed to load market data';
        setError(errorMessage);
        if (error.statusCode !== 401) {
          toast.error(errorMessage);
        }
        setCryptoList([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCryptos();
  }, []);

  const handleCoinChange = (coinId: string) => {
    const coin = cryptoList.find(c => c.id === coinId);
    if (coin) {
      setSelectedCoin(coin);
    }
  };

  const handlePlaceOrder = () => {
    if (!user) {
      toast.error("Please sign in to trade");
      return;
    }
    if (!isConnected) {
      toast.error("Please connect your wallet to trade");
      return;
    }
    if (orderSide === 'buy') {
      setShowBuyModal(true);
    } else {
      setShowSellModal(true);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="w-16 h-16 rounded-full border-2 border-gold-500/20" />
            <div className="absolute inset-0 w-16 h-16 rounded-full border-2 border-transparent border-t-gold-500 animate-spin" />
          </div>
          <p className="text-gray-400">Loading trading data...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <DashboardCard glowColor="red">
        <div className="text-center py-8">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-red-400 mb-2">Failed to Load Trading Data</h2>
          <p className="text-gray-400 mb-4">{error}</p>
          <Button onClick={() => window.location.reload()} variant="outline" className="border-red-500/30 text-red-400 hover:bg-red-500/10">
            <RefreshCw className="h-4 w-4 mr-2" />
            Reload Page
          </Button>
        </div>
      </DashboardCard>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-display font-bold text-white flex items-center gap-3">
            <BarChart3 className="h-7 w-7 text-gold-400" />
            Trade
          </h1>
          <p className="text-gray-400 mt-1">Professional trading with real-time charts</p>
        </div>

        {/* Trading Pair Selector */}
        <Select value={selectedCoin?.id} onValueChange={handleCoinChange}>
          <SelectTrigger className="w-full sm:w-[250px] bg-white/5 border-white/10">
            <SelectValue placeholder="Select pair" />
          </SelectTrigger>
          <SelectContent className="bg-[#1a1a2e] border-white/10">
            {cryptoList.map((crypto) => (
              <SelectItem key={crypto.id} value={crypto.id}>
                <div className="flex items-center gap-2">
                  {crypto.image && (
                    <img src={crypto.image} alt={crypto.name} className="w-5 h-5 rounded-full" />
                  )}
                  <span className="font-medium">{crypto.symbol}/USD</span>
                  <span className={cn(
                    "text-xs",
                    crypto.change_24h >= 0 ? "text-emerald-400" : "text-red-400"
                  )}>
                    {crypto.change_24h >= 0 ? "+" : ""}{crypto.change_24h.toFixed(2)}%
                  </span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {selectedCoin && (
        <>
          {/* Price Header */}
          <DashboardCard noPadding>
            <div className="p-4 flex flex-wrap items-center gap-6">
              <div className="flex items-center gap-3">
                {selectedCoin.image && (
                  <img src={selectedCoin.image} alt={selectedCoin.name} className="w-10 h-10 rounded-full" />
                )}
                <div>
                  <h2 className="text-xl font-bold text-white">{selectedCoin.symbol}/USD</h2>
                  <p className="text-sm text-gray-400">{selectedCoin.name}</p>
                </div>
              </div>

              <div className="flex items-baseline gap-3">
                <span className="text-3xl font-bold text-white font-mono">
                  ${selectedCoin.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span className={cn(
                  "flex items-center gap-1 px-2 py-1 rounded text-sm font-semibold",
                  selectedCoin.change_24h >= 0
                    ? "bg-emerald-500/10 text-emerald-400"
                    : "bg-red-500/10 text-red-400"
                )}>
                  {selectedCoin.change_24h >= 0 ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : (
                    <TrendingDown className="h-4 w-4" />
                  )}
                  {selectedCoin.change_24h >= 0 ? "+" : ""}{selectedCoin.change_24h.toFixed(2)}%
                </span>
              </div>

              <div className="flex gap-6 ml-auto text-sm">
                <div>
                  <p className="text-gray-500">24h High</p>
                  <p className="text-emerald-400 font-mono">${(selectedCoin.price * 1.05).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-500">24h Low</p>
                  <p className="text-red-400 font-mono">${(selectedCoin.price * 0.95).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-500">24h Volume</p>
                  <p className="text-white font-mono">${(selectedCoin.volume_24h / 1e9).toFixed(2)}B</p>
                </div>
              </div>
            </div>
          </DashboardCard>

          {/* Main Trading Grid */}
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            {/* Chart - 3 columns */}
            <div className="xl:col-span-3">
              <DashboardCard noPadding className="h-[500px]">
                <TradingChart
                  coinId={selectedCoin.id}
                  coinName={selectedCoin.name}
                  currentPrice={selectedCoin.price}
                  priceChange24h={selectedCoin.change_24h}
                />
              </DashboardCard>
            </div>

            {/* Order Panel - 1 column */}
            <div className="space-y-4">
              <DashboardCard>
                <Tabs defaultValue="buy" className="w-full" onValueChange={(v) => setOrderSide(v as 'buy' | 'sell')}>
                  <TabsList className="w-full bg-white/5 p-1">
                    <TabsTrigger 
                      value="buy" 
                      className="flex-1 data-[state=active]:bg-emerald-500 data-[state=active]:text-white"
                    >
                      Buy
                    </TabsTrigger>
                    <TabsTrigger 
                      value="sell"
                      className="flex-1 data-[state=active]:bg-red-500 data-[state=active]:text-white"
                    >
                      Sell
                    </TabsTrigger>
                  </TabsList>

                  <div className="mt-4 space-y-4">
                    {/* Order Type */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => setOrderType('market')}
                        className={cn(
                          "flex-1 py-2 text-sm font-medium rounded-lg transition-colors",
                          orderType === 'market'
                            ? "bg-white/10 text-white"
                            : "text-gray-500 hover:text-white"
                        )}
                      >
                        Market
                      </button>
                      <button
                        onClick={() => setOrderType('limit')}
                        className={cn(
                          "flex-1 py-2 text-sm font-medium rounded-lg transition-colors",
                          orderType === 'limit'
                            ? "bg-white/10 text-white"
                            : "text-gray-500 hover:text-white"
                        )}
                      >
                        Limit
                      </button>
                    </div>

                    {/* Limit Price (if limit order) */}
                    {orderType === 'limit' && (
                      <div className="space-y-2">
                        <Label className="text-gray-400 text-xs">Price (USD)</Label>
                        <Input
                          type="number"
                          placeholder={selectedCoin.price.toFixed(2)}
                          value={limitPrice}
                          onChange={(e) => setLimitPrice(e.target.value)}
                          className="bg-white/5 border-white/10 font-mono"
                        />
                      </div>
                    )}

                    {/* Amount */}
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <Label className="text-gray-400 text-xs">Amount ({selectedCoin.symbol})</Label>
                        <span className="text-xs text-gray-500">Available: 0.00</span>
                      </div>
                      <Input
                        type="number"
                        placeholder="0.00"
                        value={orderAmount}
                        onChange={(e) => setOrderAmount(e.target.value)}
                        className="bg-white/5 border-white/10 font-mono"
                      />
                      <div className="flex gap-1">
                        {[25, 50, 75, 100].map((pct) => (
                          <button
                            key={pct}
                            className="flex-1 py-1 text-xs text-gray-400 hover:text-white bg-white/5 hover:bg-white/10 rounded transition-colors"
                          >
                            {pct}%
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Total */}
                    <div className="p-3 bg-white/5 rounded-lg">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Total</span>
                        <span className="text-white font-mono">
                          ${orderAmount ? (parseFloat(orderAmount) * selectedCoin.price).toLocaleString() : '0.00'}
                        </span>
                      </div>
                    </div>

                    {/* Wallet Status */}
                    {!isConnected && (
                      <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                        <div className="flex items-center gap-2 text-amber-400 text-sm">
                          <Wallet className="h-4 w-4" />
                          <span>Connect wallet to trade</span>
                        </div>
                      </div>
                    )}

                    {/* Submit Button */}
                    <Button
                      onClick={handlePlaceOrder}
                      disabled={!user || !isConnected || !orderAmount}
                      className={cn(
                        "w-full h-12 font-semibold",
                        orderSide === 'buy'
                          ? "bg-emerald-500 hover:bg-emerald-400 text-white"
                          : "bg-red-500 hover:bg-red-400 text-white"
                      )}
                    >
                      {orderSide === 'buy' ? (
                        <>
                          <ArrowDownRight className="h-4 w-4 mr-2" />
                          Buy {selectedCoin.symbol}
                        </>
                      ) : (
                        <>
                          <ArrowUpRight className="h-4 w-4 mr-2" />
                          Sell {selectedCoin.symbol}
                        </>
                      )}
                    </Button>
                  </div>
                </Tabs>
              </DashboardCard>

              {/* Gas Estimator */}
              {isConnected && (
                <DashboardCard title="Gas Estimate" icon={<Zap className="h-5 w-5" />}>
                  <GasEstimator ethPriceUSD={selectedCoin.price} />
                </DashboardCard>
              )}
            </div>
          </div>

          {/* Market Info */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <DashboardCard>
              <div className="text-center">
                <p className="text-xs text-gray-500 mb-1">Market Cap</p>
                <p className="text-xl font-bold text-white">${(selectedCoin.market_cap / 1e9).toFixed(2)}B</p>
              </div>
            </DashboardCard>
            <DashboardCard>
              <div className="text-center">
                <p className="text-xs text-gray-500 mb-1">24h Trading Volume</p>
                <p className="text-xl font-bold text-white">${(selectedCoin.volume_24h / 1e9).toFixed(2)}B</p>
              </div>
            </DashboardCard>
            <DashboardCard>
              <div className="text-center">
                <p className="text-xs text-gray-500 mb-1">Circulating Supply</p>
                <p className="text-xl font-bold text-white">21M {selectedCoin.symbol}</p>
              </div>
            </DashboardCard>
          </div>
        </>
      )}

      {/* Transaction Modals */}
      {selectedCoin && (
        <>
          <TransactionSigner
            open={showBuyModal}
            onOpenChange={setShowBuyModal}
            type="buy"
            coinSymbol={selectedCoin.symbol}
            coinName={selectedCoin.name}
            currentPrice={selectedCoin.price}
          />
          <TransactionSigner
            open={showSellModal}
            onOpenChange={setShowSellModal}
            type="sell"
            coinSymbol={selectedCoin.symbol}
            coinName={selectedCoin.name}
            currentPrice={selectedCoin.price}
          />
        </>
      )}
    </div>
  );
};

export default EnhancedTrade;
