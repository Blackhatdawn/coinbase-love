import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Shield, AlertTriangle, FileText, UserCheck, Ban, Flag } from "lucide-react";

const AMLPolicy = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-24 pb-20">
        <div className="container mx-auto px-4 max-w-4xl">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gold-500/10 flex items-center justify-center">
              <Shield className="h-8 w-8 text-gold-400" />
            </div>
            <h1 className="font-display text-4xl md:text-5xl font-bold mb-4">
              AML <span className="bg-gradient-to-r from-gold-400 to-gold-600 bg-clip-text text-transparent">Policy</span>
            </h1>
            <p className="text-muted-foreground">Anti-Money Laundering & Counter-Terrorist Financing Policy</p>
            <p className="text-sm text-muted-foreground mt-2">Last updated: June 1, 2025</p>
          </div>

          {/* Content */}
          <div className="prose prose-invert max-w-none space-y-8">
            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <FileText className="h-5 w-5 text-gold-400" />
                Policy Statement
              </h2>
              <p className="text-muted-foreground leading-relaxed">
                CryptoVault Financial, Inc. ("CryptoVault") is committed to preventing the use of its services for money laundering, terrorist financing, and other financial crimes. This Anti-Money Laundering (AML) and Counter-Terrorist Financing (CTF) Policy outlines our approach to detecting, preventing, and reporting suspicious activities in compliance with applicable laws and regulations.
              </p>
              <p className="text-muted-foreground leading-relaxed mt-4">
                As a registered Money Services Business (MSB) with the Financial Crimes Enforcement Network (FinCEN), CryptoVault maintains a robust compliance program that meets or exceeds all regulatory requirements under the Bank Secrecy Act (BSA) and related regulations.
              </p>
            </section>

            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <UserCheck className="h-5 w-5 text-gold-400" />
                Know Your Customer (KYC)
              </h2>
              <p className="text-muted-foreground leading-relaxed mb-4">
                CryptoVault implements a comprehensive KYC program to verify the identity of all customers. Our KYC procedures include:
              </p>
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold text-gold-400 mb-2">Customer Identification Program (CIP)</h3>
                  <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                    <li>Collection of full legal name, date of birth, and residential address</li>
                    <li>Government-issued photo identification verification</li>
                    <li>Social Security Number or Tax Identification Number</li>
                    <li>Proof of address documentation</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-semibold text-gold-400 mb-2">Enhanced Due Diligence (EDD)</h3>
                  <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                    <li>Additional verification for high-risk customers</li>
                    <li>Source of funds documentation for large transactions</li>
                    <li>Ongoing monitoring of customer activity</li>
                    <li>Periodic review and update of customer information</li>
                  </ul>
                </div>
              </div>
            </section>

            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-gold-400" />
                Transaction Monitoring
              </h2>
              <p className="text-muted-foreground leading-relaxed mb-4">
                CryptoVault employs sophisticated transaction monitoring systems to detect potentially suspicious activity, including:
              </p>
              <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                <li>Real-time transaction screening against sanctions lists (OFAC, UN, EU)</li>
                <li>Pattern analysis to identify unusual transaction behavior</li>
                <li>Velocity checks on deposits, withdrawals, and transfers</li>
                <li>Blockchain analytics to trace the origin and destination of funds</li>
                <li>Cross-referencing with known high-risk wallet addresses</li>
              </ul>
            </section>

            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Flag className="h-5 w-5 text-gold-400" />
                Suspicious Activity Reporting
              </h2>
              <p className="text-muted-foreground leading-relaxed mb-4">
                When suspicious activity is detected, CryptoVault will:
              </p>
              <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                <li>File Suspicious Activity Reports (SARs) with FinCEN within 30 days</li>
                <li>File Currency Transaction Reports (CTRs) for transactions exceeding $10,000</li>
                <li>Maintain confidentiality of all filed reports</li>
                <li>Cooperate fully with law enforcement investigations</li>
                <li>Preserve all relevant records for a minimum of 5 years</li>
              </ul>
            </section>

            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Ban className="h-5 w-5 text-gold-400" />
                Prohibited Activities
              </h2>
              <p className="text-muted-foreground leading-relaxed mb-4">
                CryptoVault strictly prohibits the use of its services for:
              </p>
              <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                <li>Money laundering or terrorist financing</li>
                <li>Transactions involving sanctioned individuals, entities, or jurisdictions</li>
                <li>Fraud, tax evasion, or other illegal activities</li>
                <li>Transactions with known darknet markets or illicit services</li>
                <li>Circumventing transaction limits or verification requirements</li>
              </ul>
              <div className="mt-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
                <p className="text-sm text-destructive">
                  <strong>Warning:</strong> Accounts found to be engaging in prohibited activities will be immediately suspended, reported to authorities, and subject to asset forfeiture where legally required.
                </p>
              </div>
            </section>

            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4">Compliance Officer</h2>
              <p className="text-muted-foreground leading-relaxed">
                CryptoVault has appointed a dedicated Compliance Officer responsible for implementing and maintaining our AML/CTF program. For compliance-related inquiries, please contact:
              </p>
              <div className="mt-4 text-sm">
                <p><strong>Email:</strong> compliance@cryptovault.financial</p>
                <p><strong>Address:</strong> 1201 Market Street, Suite 101, Wilmington, DE 19801</p>
              </div>
            </section>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default AMLPolicy;
