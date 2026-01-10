import React, { useEffect, useState } from 'react';
import { useWeb3 } from '@/contexts/Web3Context';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Fuel, TrendingUp, TrendingDown, Zap, Clock, DollarSign } from 'lucide-react';
import { Separator } from '@/components/ui/separator';

interface GasEstimate {
  slow: string;
  average: string;
  fast: string;
  timestamp: number;
}

interface GasEstimatorProps {
  transactionTo?: string;
  transactionAmount?: string;
  ethPriceUSD?: number;
}

export const GasEstimator: React.FC<GasEstimatorProps> = ({
  transactionTo,
  transactionAmount,
  ethPriceUSD = 2500 // Default ETH price
}) => {
  const { provider, chainId, networkName } = useWeb3();
  const [gasPrice, setGasPrice] = useState<string>('0');
  const [gasEstimate, setGasEstimate] = useState<string>('21000'); // Default gas limit
  const [isLoading, setIsLoading] = useState(false);
  const [gasTrend, setGasTrend] = useState<'up' | 'down' | 'stable'>('stable');

  // Fetch current gas price
  const fetchGasPrice = async () => {
    if (!provider) return;

    try {
      setIsLoading(true);
      const feeData = await provider.getFeeData();
      
      if (feeData.gasPrice) {
        const gasPriceGwei = Number(feeData.gasPrice) / 1e9;
        setGasPrice(gasPriceGwei.toFixed(2));
        
        // Determine trend (simplified - in production, compare with historical data)
        if (gasPriceGwei > 50) {
          setGasTrend('up');
        } else if (gasPriceGwei < 20) {
          setGasTrend('down');
        } else {
          setGasTrend('stable');
        }
      }
    } catch (error) {
      console.error('Error fetching gas price:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Estimate gas for specific transaction
  const estimateTransactionGas = async () => {
    if (!provider || !transactionTo || !transactionAmount) {
      setGasEstimate('21000'); // Default for simple ETH transfer
      return;
    }

    try {
      const gasEstimate = await provider.estimateGas({
        to: transactionTo,
        value: BigInt(Math.floor(parseFloat(transactionAmount) * 1e18))
      });
      setGasEstimate(gasEstimate.toString());
    } catch (error) {
      console.error('Error estimating gas:', error);
      setGasEstimate('21000');
    }
  };

  // Calculate gas estimates
  const calculateGasOptions = (): GasEstimate => {
    const baseGas = parseFloat(gasPrice);
    return {
      slow: (baseGas * 0.8).toFixed(2),
      average: baseGas.toFixed(2),
      fast: (baseGas * 1.3).toFixed(2),
      timestamp: Date.now()
    };
  };

  // Calculate USD cost
  const calculateUSDCost = (gasPriceGwei: string): string => {
    const gasCost = (parseFloat(gasPriceGwei) * parseFloat(gasEstimate)) / 1e9; // ETH
    const usdCost = gasCost * ethPriceUSD;
    return usdCost.toFixed(2);
  };

  // Auto-refresh gas price every 15 seconds
  useEffect(() => {
    fetchGasPrice();
    const interval = setInterval(fetchGasPrice, 15000);
    return () => clearInterval(interval);
  }, [provider]);

  // Estimate gas when transaction params change
  useEffect(() => {
    estimateTransactionGas();
  }, [transactionTo, transactionAmount, provider]);

  const gasOptions = calculateGasOptions();

  // Don't show for non-EVM networks
  if (networkName && !['Ethereum', 'Polygon', 'Sepolia'].includes(networkName)) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Fuel className="h-5 w-5" />
            Gas Price Tracker
          </CardTitle>
          <Badge variant={gasTrend === 'up' ? 'destructive' : gasTrend === 'down' ? 'default' : 'secondary'}>
            {gasTrend === 'up' && <TrendingUp className="h-3 w-3 mr-1" />}
            {gasTrend === 'down' && <TrendingDown className="h-3 w-3 mr-1" />}
            {gasTrend === 'stable' && '━'}
            {gasTrend === 'up' ? 'High' : gasTrend === 'down' ? 'Low' : 'Normal'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Gas Price */}
        <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-lg">
          <div>
            <p className="text-sm text-muted-foreground">Current Gas Price</p>
            <p className="text-2xl font-bold">{gasPrice} Gwei</p>
            <p className="text-xs text-muted-foreground">≈ ${calculateUSDCost(gasPrice)}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-muted-foreground">Network</p>
            <p className="text-lg font-semibold">{networkName || 'Ethereum'}</p>
          </div>
        </div>

        <Separator />

        {/* Gas Options */}
        <div className="grid grid-cols-3 gap-3">
          {/* Slow */}
          <div className="p-3 border rounded-lg hover:border-purple-500 transition-colors cursor-pointer">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium">Slow</span>
            </div>
            <p className="text-xl font-bold">{gasOptions.slow}</p>
            <p className="text-xs text-muted-foreground">Gwei</p>
            <p className="text-xs text-green-600 mt-1">
              ${calculateUSDCost(gasOptions.slow)}
            </p>
            <p className="text-xs text-muted-foreground mt-1">~5 min</p>
          </div>

          {/* Average */}
          <div className="p-3 border-2 border-purple-500 rounded-lg bg-purple-500/5">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="h-4 w-4 text-purple-500" />
              <span className="text-sm font-medium">Average</span>
            </div>
            <p className="text-xl font-bold">{gasOptions.average}</p>
            <p className="text-xs text-muted-foreground">Gwei</p>
            <p className="text-xs text-green-600 mt-1">
              ${calculateUSDCost(gasOptions.average)}
            </p>
            <p className="text-xs text-muted-foreground mt-1">~2 min</p>
          </div>

          {/* Fast */}
          <div className="p-3 border rounded-lg hover:border-purple-500 transition-colors cursor-pointer">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-red-500" />
              <span className="text-sm font-medium">Fast</span>
            </div>
            <p className="text-xl font-bold">{gasOptions.fast}</p>
            <p className="text-xs text-muted-foreground">Gwei</p>
            <p className="text-xs text-green-600 mt-1">
              ${calculateUSDCost(gasOptions.fast)}
            </p>
            <p className="text-xs text-muted-foreground mt-1">~30 sec</p>
          </div>
        </div>

        {/* Transaction Estimate */}
        {transactionTo && transactionAmount && (
          <>
            <Separator />
            <div className="p-3 bg-secondary/30 rounded-lg">
              <p className="text-sm font-medium mb-2">Estimated Transaction Cost</p>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Gas Limit:</span>
                  <span className="font-mono">{gasEstimate}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Gas Price:</span>
                  <span className="font-mono">{gasOptions.average} Gwei</span>
                </div>
                <Separator className="my-2" />
                <div className="flex justify-between font-semibold text-base">
                  <span>Total Cost:</span>
                  <div className="text-right">
                    <p>${calculateUSDCost(gasOptions.average)}</p>
                    <p className="text-xs text-muted-foreground font-normal">
                      {((parseFloat(gasOptions.average) * parseFloat(gasEstimate)) / 1e9).toFixed(6)} ETH
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        <p className="text-xs text-muted-foreground text-center">
          Gas prices update every 15 seconds
        </p>
      </CardContent>
    </Card>
  );
};
