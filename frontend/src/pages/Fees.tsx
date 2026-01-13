import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Check, Info, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

const Fees = () => {
  const tradingFees = [
    { tier: "VIP 0", volume: "< $10,000", maker: "0.10%", taker: "0.15%" },
    { tier: "VIP 1", volume: "$10,000 - $50,000", maker: "0.08%", taker: "0.12%" },
    { tier: "VIP 2", volume: "$50,000 - $250,000", maker: "0.06%", taker: "0.10%" },
    { tier: "VIP 3", volume: "$250,000 - $1,000,000", maker: "0.04%", taker: "0.08%" },
    { tier: "VIP 4", volume: "> $1,000,000", maker: "0.02%", taker: "0.05%" },
  ];

  const withdrawalFees = [
    { asset: "BTC", network: "Bitcoin", fee: "0.0005 BTC", minWithdraw: "0.001 BTC" },
    { asset: "ETH", network: "Ethereum", fee: "0.005 ETH", minWithdraw: "0.01 ETH" },
    { asset: "USDT", network: "TRC20", fee: "1 USDT", minWithdraw: "10 USDT" },
    { asset: "USDT", network: "ERC20", fee: "10 USDT", minWithdraw: "20 USDT" },
    { asset: "SOL", network: "Solana", fee: "0.01 SOL", minWithdraw: "0.1 SOL" },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-24 pb-20">
        <div className="container mx-auto px-4">
          {/* Hero */}
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h1 className="font-display text-4xl md:text-5xl font-bold mb-6">
              Transparent <span className="bg-gradient-to-r from-gold-400 to-gold-600 bg-clip-text text-transparent">Fee Structure</span>
            </h1>
            <p className="text-lg text-muted-foreground">
              At CryptoVault, we believe in complete transparency. Our competitive fee structure rewards active traders with lower costs.
            </p>
          </div>

          {/* Trading Fees */}
          <section className="mb-16">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <span className="h-8 w-1 bg-gradient-to-b from-gold-400 to-gold-600 rounded-full"></span>
              Trading Fees
            </h2>
            <div className="glass-card border border-gold-500/10 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gold-500/5">
                    <tr>
                      <th className="text-left px-6 py-4 text-sm font-semibold text-gold-400">Tier</th>
                      <th className="text-left px-6 py-4 text-sm font-semibold text-gold-400">30-Day Volume (USD)</th>
                      <th className="text-left px-6 py-4 text-sm font-semibold text-gold-400">Maker Fee</th>
                      <th className="text-left px-6 py-4 text-sm font-semibold text-gold-400">Taker Fee</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tradingFees.map((fee, index) => (
                      <tr key={fee.tier} className={index % 2 === 0 ? "bg-background/50" : ""}>
                        <td className="px-6 py-4 font-medium">{fee.tier}</td>
                        <td className="px-6 py-4 text-muted-foreground">{fee.volume}</td>
                        <td className="px-6 py-4 text-success">{fee.maker}</td>
                        <td className="px-6 py-4 text-gold-400">{fee.taker}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="mt-4 flex items-start gap-2 text-sm text-muted-foreground">
              <Info className="h-4 w-4 mt-0.5 text-gold-400" />
              <p>Maker orders add liquidity to the order book. Taker orders remove liquidity. Your fee tier is calculated based on your 30-day rolling trading volume.</p>
            </div>
          </section>

          {/* Withdrawal Fees */}
          <section className="mb-16">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <span className="h-8 w-1 bg-gradient-to-b from-gold-400 to-gold-600 rounded-full"></span>
              Withdrawal Fees
            </h2>
            <div className="glass-card border border-gold-500/10 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gold-500/5">
                    <tr>
                      <th className="text-left px-6 py-4 text-sm font-semibold text-gold-400">Asset</th>
                      <th className="text-left px-6 py-4 text-sm font-semibold text-gold-400">Network</th>
                      <th className="text-left px-6 py-4 text-sm font-semibold text-gold-400">Withdrawal Fee</th>
                      <th className="text-left px-6 py-4 text-sm font-semibold text-gold-400">Minimum Withdrawal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {withdrawalFees.map((fee, index) => (
                      <tr key={`${fee.asset}-${fee.network}`} className={index % 2 === 0 ? "bg-background/50" : ""}>
                        <td className="px-6 py-4 font-medium">{fee.asset}</td>
                        <td className="px-6 py-4 text-muted-foreground">{fee.network}</td>
                        <td className="px-6 py-4">{fee.fee}</td>
                        <td className="px-6 py-4 text-muted-foreground">{fee.minWithdraw}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="mt-4 flex items-start gap-2 text-sm text-muted-foreground">
              <Info className="h-4 w-4 mt-0.5 text-gold-400" />
              <p>Withdrawal fees cover blockchain network costs. Deposits are always free. Fees may vary based on network congestion.</p>
            </div>
          </section>

          {/* Zero Fee Benefits */}
          <section className="mb-16">
            <div className="glass-card p-8 border border-gold-500/20 bg-gradient-to-br from-gold-500/5 to-transparent">
              <h3 className="text-xl font-bold mb-4">Zero Fee Benefits</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="flex items-start gap-3">
                  <Check className="h-5 w-5 text-success mt-0.5" />
                  <div>
                    <p className="font-medium">Free Deposits</p>
                    <p className="text-sm text-muted-foreground">All cryptocurrency deposits are completely free</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Check className="h-5 w-5 text-success mt-0.5" />
                  <div>
                    <p className="font-medium">Free P2P Transfers</p>
                    <p className="text-sm text-muted-foreground">Send crypto to other CryptoVault users instantly</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Check className="h-5 w-5 text-success mt-0.5" />
                  <div>
                    <p className="font-medium">Free Account Maintenance</p>
                    <p className="text-sm text-muted-foreground">No monthly fees or hidden charges</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Check className="h-5 w-5 text-success mt-0.5" />
                  <div>
                    <p className="font-medium">Free API Access</p>
                    <p className="text-sm text-muted-foreground">Build and trade with our robust API</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* CTA */}
          <section className="text-center">
            <h3 className="text-2xl font-bold mb-4">Start Trading Today</h3>
            <p className="text-muted-foreground mb-6">Join millions of traders enjoying our competitive fees</p>
            <Button className="bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black" asChild>
              <Link to="/auth">
                Create Account <ArrowRight className="h-4 w-4 ml-2" />
              </Link>
            </Button>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Fees;
