import Header from "@/components/Header";
import LivePriceTicker from "@/components/LivePriceTicker";
import HeroSection from "@/components/HeroSection";
import SocialProofSection from "@/components/SocialProofSection";
import FeaturesSection from "@/components/FeaturesSection";
import CTASection from "@/components/CTASection";
import FAQSection from "@/components/FAQSection";
import Footer from "@/components/Footer";
import { Helmet } from 'react-helmet-async';

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Helmet>
        <title>CryptoVault - Secure Digital Asset Custody</title>
        <meta name="description" content="CryptoVault provides institutional-grade custody solutions with cold storage, multi-signature wallets, and comprehensive compliance for your digital assets." />
        <meta property="og:title" content="CryptoVault - Secure Digital Asset Custody" />
        <meta property="og:description" content="Bank-grade security for your cryptocurrency. Trade with confidence." />
        <meta property="og:type" content="website" />
      </Helmet>
      <Header />
      <LivePriceTicker />
      <main>
        <HeroSection />
        <SocialProofSection />
        <FeaturesSection />
        <CTASection />
        <FAQSection />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
