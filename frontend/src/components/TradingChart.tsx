import React, { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, LineStyle } from 'lightweight-charts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, TrendingUp, TrendingDown } from 'lucide-react';
import { api } from '@/lib/api';

interface PriceData {
  timestamp: number;
  price: number;
}

interface TradingChartProps {
  coinId: string;
  coinName: string;
  currentPrice: number;
  priceChange24h: number;
}

const TIME_RANGES = [
  { label: '1D', days: 1 },
  { label: '7D', days: 7 },
  { label: '30D', days: 30 },
  { label: '90D', days: 90 },
  { label: '1Y', days: 365 }
];

export const TradingChart: React.FC<TradingChartProps> = ({
  coinId,
  coinName,
  currentPrice,
  priceChange24h
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Area'> | null>(null);
  
  const [selectedRange, setSelectedRange] = useState(7);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch price history
  const fetchPriceHistory = async (days: number) => {
    setIsLoading(true);
    setError(null);

    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${backendUrl}/api/crypto/${coinId}/history?days=${days}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch price history');
      }

      const data = await response.json();
      return data.history as PriceData[];
    } catch (err) {
      console.error('Error fetching price history:', err);
      setError('Failed to load chart data');
      return [];
    } finally {
      setIsLoading(false);
    }
  };

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: 'transparent' },
        textColor: '#d1d5db'
      },
      grid: {
        vertLines: { color: 'rgba(42, 46, 57, 0.3)' },
        horzLines: { color: 'rgba(42, 46, 57, 0.3)' }
      },
      crosshair: {
        mode: 1,
        vertLine: {
          labelBackgroundColor: '#667eea'
        },
        horzLine: {
          labelBackgroundColor: '#667eea'
        }
      },
      timeScale: {
        borderColor: '#2B2B43',
        timeVisible: true,
        secondsVisible: false
      },
      rightPriceScale: {
        borderColor: '#2B2B43'
      }
    });

    const areaSeries = chart.addAreaSeries({
      lineColor: priceChange24h >= 0 ? '#10b981' : '#ef4444',
      topColor: priceChange24h >= 0 ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)',
      bottomColor: 'rgba(16, 185, 129, 0.0)',
      lineWidth: 2,
      priceFormat: {
        type: 'price',
        precision: 2,
        minMove: 0.01
      }
    });

    chartRef.current = chart;
    seriesRef.current = areaSeries;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: 400
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [priceChange24h]);

  // Load data when range changes
  useEffect(() => {
    const loadData = async () => {
      const history = await fetchPriceHistory(selectedRange);
      
      if (history.length > 0 && seriesRef.current) {
        const formattedData = history.map(point => ({
          time: point.timestamp as any,
          value: point.price
        }));

        seriesRef.current.setData(formattedData);
        
        if (chartRef.current) {
          chartRef.current.timeScale().fitContent();
        }
      }
    };

    loadData();
  }, [selectedRange, coinId]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-2xl">{coinName} Price Chart</CardTitle>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-3xl font-bold">${currentPrice.toLocaleString()}</span>
              <div className={`flex items-center gap-1 ${priceChange24h >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {priceChange24h >= 0 ? (
                  <TrendingUp className="h-5 w-5" />
                ) : (
                  <TrendingDown className="h-5 w-5" />
                )}
                <span className="text-lg font-semibold">
                  {priceChange24h >= 0 ? '+' : ''}{priceChange24h.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex gap-2">
            {TIME_RANGES.map(range => (
              <Button
                key={range.days}
                variant={selectedRange === range.days ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedRange(range.days)}
                disabled={isLoading}
              >
                {range.label}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="flex items-center justify-center h-[400px]">
            <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
          </div>
        )}
        
        {error && (
          <div className="flex items-center justify-center h-[400px] text-red-600">
            {error}
          </div>
        )}
        
        <div 
          ref={chartContainerRef} 
          className={isLoading || error ? 'hidden' : ''}
          style={{ height: '400px', width: '100%' }}
        />
      </CardContent>
    </Card>
  );
};
