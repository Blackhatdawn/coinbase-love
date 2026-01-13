import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { TradingChart } from "@/components/TradingChart";
import { GasEstimator } from "@/components/GasEstimator";
import { TransactionSigner } from "@/components/TransactionSigner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useWeb3 } from "@/contexts/Web3Context";
import { useAuth } from "@/contexts/AuthContext";
import { api } from "@/lib/apiClient";
import { Wallet, TrendingUp, BarChart3, DollarSign } from "lucide-react";
import { toast } from "sonner";

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
  // Auth is optional - trading page works without login
  const auth = useAuth();
  const user = auth?.user ?? null;
  
  const { isConnected, account } = useWeb3();
  
  const [cryptoList, setCryptoList] = useState<CryptoData[]>([]);
  const [selectedCoin, setSelectedCoin] = useState<CryptoData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showBuyModal, setShowBuyModal] = useState(false);
  const [showSellModal, setShowSellModal] = useState(false);

  // Fetch cryptocurrencies
  useEffect(() => {
    const fetchCryptos = async () => {
      try {
        setIsLoading(true);
        const response = await api.crypto.getAll();
        // Backend returns { cryptocurrencies: [...] }
        const cryptos = response.cryptocurrencies || [];
        setCryptoList(cryptos);
        
        // Select Bitcoin by default
        if (cryptos.length > 0) {
          setSelectedCoin(cryptos[0]);
        }
      } catch (error: any) {
        console.error("Failed to fetch cryptocurrencies:", error);
        // Don't show error toast for 401 - it's expected when not logged in
        if (error.status !== 401) {
          toast.error("Failed to load market data");
        }
        // Use empty array to prevent crash
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

  const handleBuy = () => {
    if (!user) {
      toast.error("Please sign in to trade");
      return;
    }
    if (!isConnected) {
      toast.error("Please connect your wallet to trade");
      return;
    }
    setShowBuyModal(true);
  };

  const handleSell = () => {
    if (!user) {
      toast.error("Please sign in to trade");
      return;
    }
    if (!isConnected) {
      toast.error("Please connect your wallet to trade");
      return;
    }
    setShowSellModal(true);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="pt-24 pb-20 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading trading dashboard...</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-24 pb-20">
        <div className="container mx-auto px-4">
          {/* Header */}
          <div className="mb-8">
            <h1 className="font-display text-4xl md:text-5xl font-bold mb-3">
              Advanced <span className="text-gradient">Trading</span>
            </h1>
            <p className="text-lg text-muted-foreground">
              Professional trading tools with real-time charts and on-chain transactions
            </p>
          </div>

          {/* Coin Selector */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Select Trading Pair
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Select value={selectedCoin?.id} onValueChange={handleCoinChange}>
                <SelectTrigger className="w-full md:w-[300px]">
                  <SelectValue placeholder="Select cryptocurrency" />
                </SelectTrigger>
                <SelectContent>
                  {cryptoList.map((crypto) => (
                    <SelectItem key={crypto.id} value={crypto.id}>
                      <div className="flex items-center gap-2">
                        {crypto.image && (
                          <img src={crypto.image} alt={crypto.name} className="w-5 h-5" />
                        )}
                        <span>{crypto.name} ({crypto.symbol})</span>
                        <span className="text-muted-foreground ml-2">
                          ${crypto.price.toLocaleString()}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          {selectedCoin && (
            <>
              {/* Trading Chart */}
              <div className="mb-6">
                <TradingChart
                  coinId={selectedCoin.id}
                  coinName={selectedCoin.name}
                  currentPrice={selectedCoin.price}
                  priceChange24h={selectedCoin.change_24h}
                />
              </div>

              {/* Trading Panel & Gas Estimator */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Trading Panel */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <DollarSign className="h-5 w-5" />
                      Place Order
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Price Display */}
                    <div className="p-4 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-muted-foreground">Current Price</span>
                        <div className={`flex items-center gap-1 ${selectedCoin.change_24h >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          <TrendingUp className="h-4 w-4" />
                          <span className="text-sm font-semibold">
                            {selectedCoin.change_24h >= 0 ? '+' : ''}{selectedCoin.change_24h.toFixed(2)}%
                          </span>
                        </div>
                      </div>
                      <p className="text-3xl font-bold">${selectedCoin.price.toLocaleString()}</p>
                    </div>

                    {/* Wallet Status */}
                    {!isConnected ? (
                      <div className="p-4 border-2 border-dashed border-purple-500/50 rounded-lg text-center">
                        <Wallet className="h-8 w-8 mx-auto mb-2 text-purple-500" />
                        <p className="text-sm font-medium mb-1">Wallet Not Connected</p>
                        <p className="text-xs text-muted-foreground mb-3">
                          Connect your MetaMask wallet to start trading
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Use the "Connect Wallet" button in the header
                        </p>
                      </div>
                    ) : (
                      <div className="p-4 bg-secondary/30 rounded-lg">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-muted-foreground">Connected Wallet</span>
                          <span className="text-sm font-mono">
                            {account?.slice(0, 6)}...{account?.slice(-4)}
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Trading Actions */}
                    <div className="grid grid-cols-2 gap-3">
                      <Button
                        onClick={handleBuy}
                        disabled={!user || !isConnected}
                        className="w-full bg-green-600 hover:bg-green-700"
                        size="lg"
                      >
                        <TrendingUp className="h-4 w-4 mr-2" />
                        Buy {selectedCoin.symbol}
                      </Button>
                      <Button
                        onClick={handleSell}
                        disabled={!user || !isConnected}
                        variant="destructive"
                        className="w-full"
                        size="lg"
                      >
                        <TrendingUp className="h-4 w-4 mr-2 rotate-180" />
                        Sell {selectedCoin.symbol}
                      </Button>
                    </div>

                    {/* Market Stats */}
                    <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Market Cap</p>
                        <p className="text-sm font-semibold">
                          ${(selectedCoin.market_cap / 1e9).toFixed(2)}B
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">24h Volume</p>
                        <p className="text-sm font-semibold">
                          ${(selectedCoin.volume_24h / 1e9).toFixed(2)}B
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Gas Estimator */}
                {isConnected && (
                  <GasEstimator ethPriceUSD={selectedCoin.price} />
                )}
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
      </main>
      <Footer />
    </div>
  );
};

export default EnhancedTrade;
