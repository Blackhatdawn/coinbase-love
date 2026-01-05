import Header from "@/components/Header";
import PriceTicker from "@/components/PriceTicker";
import HeroSection from "@/components/HeroSection";
import MarketSection from "@/components/MarketSection";
import PortfolioSection from "@/components/PortfolioSection";
import FeaturesSection from "@/components/FeaturesSection";
import CTASection from "@/components/CTASection";
import Footer from "@/components/Footer";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <PriceTicker />
      <main>
        <HeroSection />
        <MarketSection />
        <PortfolioSection />
        <FeaturesSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
