import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { format } from "date-fns";
import { ArrowLeft, ArrowUpRight, ArrowDownLeft, Filter, CalendarIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { cn } from "@/lib/utils";

interface Transaction {
  id: string;
  type: "buy" | "sell";
  coin: string;
  symbol: string;
  amount: number;
  price: number;
  total: number;
  date: Date;
}

const mockTransactions: Transaction[] = [
  { id: "1", type: "buy", coin: "Bitcoin", symbol: "BTC", amount: 0.5, price: 67234, total: 33617, date: new Date("2026-01-05") },
  { id: "2", type: "sell", coin: "Ethereum", symbol: "ETH", amount: 2.0, price: 3456, total: 6912, date: new Date("2026-01-04") },
  { id: "3", type: "buy", coin: "Solana", symbol: "SOL", amount: 25, price: 178, total: 4450, date: new Date("2026-01-03") },
  { id: "4", type: "buy", coin: "Cardano", symbol: "ADA", amount: 1000, price: 0.89, total: 890, date: new Date("2026-01-02") },
  { id: "5", type: "sell", coin: "Bitcoin", symbol: "BTC", amount: 0.2, price: 65890, total: 13178, date: new Date("2025-12-28") },
  { id: "6", type: "buy", coin: "Ethereum", symbol: "ETH", amount: 1.5, price: 3234, total: 4851, date: new Date("2025-12-25") },
  { id: "7", type: "sell", coin: "Solana", symbol: "SOL", amount: 10, price: 165, total: 1650, date: new Date("2025-12-20") },
  { id: "8", type: "buy", coin: "Bitcoin", symbol: "BTC", amount: 0.3, price: 62500, total: 18750, date: new Date("2025-12-15") },
];

const TransactionHistory = () => {
  const navigate = useNavigate();
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [startDate, setStartDate] = useState<Date | undefined>();
  const [endDate, setEndDate] = useState<Date | undefined>();

  const filteredTransactions = mockTransactions.filter((tx) => {
    if (typeFilter !== "all" && tx.type !== typeFilter) return false;
    if (startDate && tx.date < startDate) return false;
    if (endDate && tx.date > endDate) return false;
    return true;
  });

  const clearFilters = () => {
    setTypeFilter("all");
    setStartDate(undefined);
    setEndDate(undefined);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Button variant="ghost" size="icon" onClick={() => navigate("/dashboard")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-3xl font-bold">Transaction History</h1>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4 items-end">
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Type</label>
                <Select value={typeFilter} onValueChange={setTypeFilter}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="All" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="buy">Buy</SelectItem>
                    <SelectItem value="sell">Sell</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">From</label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "w-[160px] justify-start text-left font-normal",
                        !startDate && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {startDate ? format(startDate, "PP") : "Start date"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={startDate}
                      onSelect={setStartDate}
                      initialFocus
                      className="pointer-events-auto"
                    />
                  </PopoverContent>
                </Popover>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">To</label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "w-[160px] justify-start text-left font-normal",
                        !endDate && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {endDate ? format(endDate, "PP") : "End date"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={endDate}
                      onSelect={setEndDate}
                      initialFocus
                      className="pointer-events-auto"
                    />
                  </PopoverContent>
                </Popover>
              </div>

              <Button variant="ghost" onClick={clearFilters}>
                Clear
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Transactions List */}
        <Card>
          <CardHeader>
            <CardTitle>Transactions ({filteredTransactions.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {filteredTransactions.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">No transactions found</p>
            ) : (
              <div className="space-y-3">
                {filteredTransactions.map((tx) => (
                  <div
                    key={tx.id}
                    className="flex items-center justify-between p-4 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={cn(
                          "p-2 rounded-full",
                          tx.type === "buy" ? "bg-green-500/20" : "bg-red-500/20"
                        )}
                      >
                        {tx.type === "buy" ? (
                          <ArrowDownLeft className="h-5 w-5 text-green-500" />
                        ) : (
                          <ArrowUpRight className="h-5 w-5 text-red-500" />
                        )}
                      </div>
                      <div>
                        <p className="font-semibold">
                          {tx.type === "buy" ? "Bought" : "Sold"} {tx.coin}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {tx.amount} {tx.symbol} @ ${tx.price.toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p
                        className={cn(
                          "font-semibold",
                          tx.type === "buy" ? "text-green-500" : "text-red-500"
                        )}
                      >
                        {tx.type === "buy" ? "-" : "+"}${tx.total.toLocaleString()}
                      </p>
                      <p className="text-sm text-muted-foreground">{format(tx.date, "MMM d, yyyy")}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TransactionHistory;
