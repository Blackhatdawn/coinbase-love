import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import {
  Shield,
  Lock,
  Server,
  FileCheck,
  UserCheck,
  AlertTriangle,
  Database,
  ArrowRight,
  Check,
  ExternalLink
} from "lucide-react";

const Security = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-20 sm:pt-24">
        {/* Hero */}
        <section className="section-padding bg-gradient-to-b from-secondary/30 to-background">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-success/10 border border-success/20 mb-6">
                <Shield className="h-4 w-4 text-success" />
                <span className="text-sm text-success font-medium">Enterprise Security</span>
              </div>
              <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold mb-6">
                Security & <span className="text-gradient">Compliance</span>
              </h1>
              <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto">
                Bank-grade security infrastructure with institutional compliance standards.
                Your assets are protected by multiple layers of security.
              </p>
            </div>
          </div>
        </section>

        {/* Security Features */}
        <section className="section-padding">
          <div className="container mx-auto px-4">
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
              {/* Cold Storage */}
              <div className="glass-card p-6 sm:p-8" data-testid="security-cold-storage">
                <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-primary/10 flex items-center justify-center mb-6">
                  <Server className="h-6 w-6 sm:h-7 sm:w-7 text-primary" />
                </div>
                <h3 className="font-display text-xl font-semibold mb-3">95%+ Cold Storage</h3>
                <p className="text-muted-foreground text-sm mb-4">
                  The vast majority of digital assets are stored in air-gapped, offline
                  cold storage vaults with Hardware Security Modules (HSM).
                </p>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-success" /> Air-gapped systems
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-success" /> HSM-backed keys
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-success" /> Geographic distribution
                  </li>
                </ul>
              </div>

              {/* Multi-Sig */}
              <div className="glass-card p-6 sm:p-8" data-testid="security-multisig">
                <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-primary/10 flex items-center justify-center mb-6">
                  <Lock className="h-6 w-6 sm:h-7 sm:w-7 text-primary" />
                </div>
                <h3 className="font-display text-xl font-semibold mb-3">Multi-Signature</h3>
                <p className="text-muted-foreground text-sm mb-4">
                  All withdrawals require multiple signatures from independent key holders,
                  preventing single points of compromise.
                </p>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-success" /> 2-of-3 standard
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-success" /> 3-of-5 institutional
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-success" /> Custom configurations
                  </li>
                </ul>
              </div>

              {/* SOC 2 */}
              <div className="glass-card p-6 sm:p-8" data-testid="security-soc2">
                <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-primary/10 flex items-center justify-center mb-6">
                  <FileCheck className="h-6 w-6 sm:h-7 sm:w-7 text-primary" />
                </div>
                <h3 className="font-display text-xl font-semibold mb-3">SOC 2 Type II</h3>
                <p className="text-muted-foreground text-sm mb-4">
                  Currently undergoing SOC 2 Type II certification to validate our
                  security controls and operational procedures.
                </p>
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-yellow-500/10 text-yellow-500 text-xs font-medium">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-500 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-yellow-500"></span>
                  </span>
                  In Progress
                </div>
              </div>

              {/* KYC/AML */}
              <div className="glass-card p-6 sm:p-8" data-testid="security-kyc-aml">
                <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-primary/10 flex items-center justify-center mb-6">
                  <UserCheck className="h-6 w-6 sm:h-7 sm:w-7 text-primary" />
                </div>
                <h3 className="font-display text-xl font-semibold mb-3">KYC/AML Compliance</h3>
                <p className="text-muted-foreground text-sm mb-4">
                  Comprehensive identity verification and anti-money laundering procedures
                  powered by industry-leading providers.
                </p>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-success" /> SumSub integration
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-success" /> Persona verification
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-success" /> Ongoing monitoring
                  </li>
                </ul>
              </div>

              {/* Risk Disclosures */}
              <div className="glass-card p-6 sm:p-8" data-testid="security-risk">
                <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-primary/10 flex items-center justify-center mb-6">
                  <AlertTriangle className="h-6 w-6 sm:h-7 sm:w-7 text-primary" />
                </div>
                <h3 className="font-display text-xl font-semibold mb-3">Risk Disclosures</h3>
                <p className="text-muted-foreground text-sm mb-4">
                  Clear and transparent risk disclosures following industry best practices
                  (Coinbase/Binance-style compliance).
                </p>
                <Button variant="ghost" size="sm" className="p-0 h-auto text-primary" asChild>
                  <Link to="/terms">
                    View Risk Disclosures
                    <ExternalLink className="h-3 w-3 ml-1" />
                  </Link>
                </Button>
              </div>

              {/* Proof of Reserves */}
              <div className="glass-card p-6 sm:p-8" data-testid="security-por">
                <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-primary/10 flex items-center justify-center mb-6">
                  <Database className="h-6 w-6 sm:h-7 sm:w-7 text-primary" />
                </div>
                <h3 className="font-display text-xl font-semibold mb-3">Proof-of-Reserves</h3>
                <p className="text-muted-foreground text-sm mb-4">
                  Cryptographic proof-of-reserves using Merkle trees and oracle verification
                  for full transparency.
                </p>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-success" /> Merkle tree proofs
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-success" /> Oracle verification
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-success" /> Monthly attestations
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Insurance */}
        <section className="section-padding bg-secondary/20">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              <div className="glass-card p-8 sm:p-10 text-center">
                <Shield className="h-12 w-12 sm:h-16 sm:w-16 text-primary mx-auto mb-6" />
                <h2 className="font-display text-2xl sm:text-3xl font-bold mb-4">$500M Insurance Coverage</h2>
                <p className="text-muted-foreground max-w-2xl mx-auto mb-6">
                  Digital assets under custody are protected by comprehensive insurance coverage
                  against theft, hacking, and other security breaches.
                </p>
                <p className="text-xs text-muted-foreground">
                  * Insurance coverage subject to policy terms and conditions. Coverage may not apply to all loss scenarios.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Important Risk Notice */}
        <section className="section-padding">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              <div className="border border-yellow-500/30 bg-yellow-500/5 rounded-xl p-8">
                <div className="flex items-start gap-4">
                  <AlertTriangle className="h-6 w-6 text-yellow-500 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-display text-lg font-semibold text-yellow-500 mb-2">
                      Important Risk Notice
                    </h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Digital asset investments are subject to high market risk. Past performance
                      is not indicative of future results. The value of your investments can go
                      down as well as up, and you may lose the entire principal amount invested.
                    </p>
                    <p className="text-sm text-muted-foreground mb-4">
                      CryptoVault Financial does not provide investment advice. All trading decisions
                      are made solely by users. Please ensure you fully understand the risks involved
                      before trading.
                    </p>
                    <p className="text-sm text-muted-foreground">
                      <strong>No Guaranteed Returns:</strong> We do not promise or guarantee any returns
                      on your digital asset holdings. Staking rewards and yields are variable and subject
                      to market conditions.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="section-padding bg-secondary/20">
          <div className="container mx-auto px-4">
            <div className="max-w-2xl mx-auto text-center">
              <h2 className="font-display text-3xl font-bold mb-4">
                Questions About Our Security?
              </h2>
              <p className="text-muted-foreground mb-8">
                Our security team is available to answer your questions and provide
                detailed information about our custody infrastructure.
              </p>
              <Button variant="hero" size="xl" asChild>
                <Link to="/contact">
                  Contact Security Team
                  <ArrowRight className="h-5 w-5 ml-2" />
                </Link>
              </Button>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Security;
