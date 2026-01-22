import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { AlertTriangle, TrendingDown, Lock, Scale, Zap, Globe } from "lucide-react";

const RiskDisclosure = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-20 sm:pt-24 pb-16 sm:pb-20">
        <div className="container mx-auto px-4 max-w-4xl">
          {/* Header */}
          <div className="text-center mb-8 sm:mb-12">
            <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-5 sm:mb-6 rounded-2xl bg-destructive/10 flex items-center justify-center">
              <AlertTriangle className="h-6 w-6 sm:h-8 sm:w-8 text-destructive" />
            </div>
            <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
              Risk <span className="bg-gradient-to-r from-gold-400 to-gold-600 bg-clip-text text-transparent">Disclosure</span>
            </h1>
            <p className="text-muted-foreground">Important information about the risks of trading digital assets</p>
            <p className="text-sm text-muted-foreground mt-2">Last updated: June 1, 2025</p>
          </div>

          {/* Warning Banner */}
          <div className="mb-8 sm:mb-12 p-5 sm:p-6 bg-destructive/10 border border-destructive/20 rounded-xl">
            <div className="flex items-start gap-4">
              <AlertTriangle className="h-5 w-5 sm:h-6 sm:w-6 text-destructive shrink-0 mt-1" />
              <div>
                <h2 className="font-bold text-base sm:text-lg mb-2">Important Warning</h2>
                <p className="text-sm leading-relaxed">
                  Trading cryptocurrencies involves significant risk and can result in the loss of your entire investment. Past performance is not indicative of future results. You should carefully consider whether trading is suitable for you in light of your circumstances, knowledge, and financial resources. Only invest funds you can afford to lose entirely.
                </p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="prose prose-invert max-w-none space-y-8">
            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <TrendingDown className="h-5 w-5 text-gold-400" />
                Market Volatility Risk
              </h2>
              <p className="text-muted-foreground leading-relaxed">
                Cryptocurrency markets are highly volatile. Prices can fluctuate significantly within short periods, sometimes moving by 10% or more in a single day. This volatility can result in substantial gains or losses. Factors contributing to volatility include:
              </p>
              <ul className="list-disc list-inside text-sm text-muted-foreground mt-4 space-y-2">
                <li>Market sentiment and speculation</li>
                <li>Regulatory announcements and changes</li>
                <li>Technological developments and security breaches</li>
                <li>Macroeconomic factors and global events</li>
                <li>Large trades by institutional investors ("whales")</li>
                <li>Social media influence and market manipulation</li>
              </ul>
            </section>

            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Lock className="h-5 w-5 text-gold-400" />
                Liquidity Risk
              </h2>
              <p className="text-muted-foreground leading-relaxed">
                Some cryptocurrencies may have limited liquidity, meaning you may not be able to buy or sell assets quickly at the price you want. During periods of high volatility or market stress, liquidity can decrease significantly, potentially resulting in:
              </p>
              <ul className="list-disc list-inside text-sm text-muted-foreground mt-4 space-y-2">
                <li>Inability to execute trades at desired prices</li>
                <li>Significant slippage on large orders</li>
                <li>Delayed order execution</li>
                <li>Partial fills on limit orders</li>
              </ul>
            </section>

            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Scale className="h-5 w-5 text-gold-400" />
                Regulatory Risk
              </h2>
              <p className="text-muted-foreground leading-relaxed">
                The regulatory environment for cryptocurrencies is evolving and varies by jurisdiction. Regulatory changes can significantly impact the value and legality of digital assets. Potential regulatory risks include:
              </p>
              <ul className="list-disc list-inside text-sm text-muted-foreground mt-4 space-y-2">
                <li>New laws restricting or banning cryptocurrency trading</li>
                <li>Changes in tax treatment of digital assets</li>
                <li>Requirements for exchanges to delist certain tokens</li>
                <li>Restrictions on cross-border transactions</li>
                <li>Enhanced compliance requirements</li>
              </ul>
            </section>

            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Zap className="h-5 w-5 text-gold-400" />
                Technology Risk
              </h2>
              <p className="text-muted-foreground leading-relaxed">
                Cryptocurrencies rely on blockchain technology, which is subject to various technological risks:
              </p>
              <ul className="list-disc list-inside text-sm text-muted-foreground mt-4 space-y-2">
                <li>Smart contract bugs or vulnerabilities</li>
                <li>Network congestion and high transaction fees</li>
                <li>Hard forks that may affect asset value</li>
                <li>51% attacks on smaller blockchain networks</li>
                <li>Protocol upgrades that may not go as planned</li>
                <li>Loss of private keys resulting in permanent loss of funds</li>
              </ul>
            </section>

            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Globe className="h-5 w-5 text-gold-400" />
                Counterparty Risk
              </h2>
              <p className="text-muted-foreground leading-relaxed">
                When you use CryptoVault or any cryptocurrency exchange, you are exposed to counterparty risk. While we implement robust security measures and maintain insurance coverage, risks include:
              </p>
              <ul className="list-disc list-inside text-sm text-muted-foreground mt-4 space-y-2">
                <li>Exchange insolvency or bankruptcy</li>
                <li>Security breaches affecting customer funds</li>
                <li>Operational failures or system outages</li>
                <li>Third-party custody provider risks</li>
              </ul>
            </section>

            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4">Acknowledgment</h2>
              <p className="text-muted-foreground leading-relaxed">
                By using CryptoVault's services, you acknowledge that you have read and understood these risk disclosures. You accept that:
              </p>
              <ul className="list-disc list-inside text-sm text-muted-foreground mt-4 space-y-2">
                <li>You may lose some or all of your investment</li>
                <li>Past performance does not guarantee future results</li>
                <li>You are solely responsible for your trading decisions</li>
                <li>CryptoVault does not provide investment advice</li>
                <li>You should consult a financial advisor before investing</li>
              </ul>
            </section>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default RiskDisclosure;
