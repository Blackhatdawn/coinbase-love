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
  // Schema markup for SEO
  const organizationSchema = {
    "@context": "https://schema.org",
    "@type": "FinancialService",
    "name": "CryptoVault Financial",
    "description": "Institutional-grade digital asset custody and management. Multi-jurisdiction cold storage, real-time proof of reserves, and zero security breaches since 2019.",
    "url": "https://cryptovault.financial",
    "logo": "https://cryptovault.financial/logo.svg",
    "image": "https://cryptovault.financial/og-image.jpg",
    "telephone": "+1-302-555-0100",
    "email": "support@cryptovault.financial",
    "address": {
      "@type": "PostalAddress",
      "streetAddress": "1201 Market Street, Suite 101",
      "addressLocality": "Wilmington",
      "addressRegion": "DE",
      "postalCode": "19801",
      "addressCountry": "US"
    },
    "foundingDate": "2019-01-15",
    "numberOfEmployees": {
      "@type": "QuantitativeValue",
      "value": "50"
    },
    "slogan": "The Custody Solution Institutions Trust With $10B+",
    "sameAs": [
      "https://twitter.com/CryptoVaultFin",
      "https://linkedin.com/company/cryptovault-financial",
      "https://discord.gg/cryptovault",
      "https://t.me/cryptovaultfinancial"
    ],
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "4.8",
      "reviewCount": "250",
      "bestRating": "5",
      "worstRating": "1"
    }
  };

  const serviceSchema = {
    "@context": "https://schema.org",
    "@type": "Service",
    "serviceType": "Digital Asset Custody",
    "provider": {
      "@type": "Organization",
      "name": "CryptoVault Financial"
    },
    "areaServed": "Worldwide",
    "hasOfferCatalog": {
      "@type": "OfferCatalog",
      "name": "Custody Services",
      "itemListElement": [
        {
          "@type": "Offer",
          "itemOffered": {
            "@type": "Service",
            "name": "Cold Storage Custody",
            "description": "95% of assets stored offline in multi-jurisdiction vaults"
          }
        },
        {
          "@type": "Offer",
          "itemOffered": {
            "@type": "Service",
            "name": "Multi-Signature Wallets",
            "description": "2-of-3 and 3-of-5 multi-sig configurations"
          }
        },
        {
          "@type": "Offer",
          "itemOffered": {
            "@type": "Service",
            "name": "Real-Time Proof of Reserves",
            "description": "On-chain verification updated daily"
          }
        }
      ]
    }
  };

  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "How is CryptoVault different from Coinbase Custody?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "CryptoVault offers multi-jurisdiction storage across 5 countries, real-time on-chain proof of reserves updated daily, and lower custody fees (0.15% vs industry average 0.25%). We've maintained zero security breaches since 2019."
        }
      },
      {
        "@type": "Question",
        "name": "What is the minimum to open an account?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Individual accounts require $10,000 minimum. Institutional accounts require $500,000 minimum."
        }
      },
      {
        "@type": "Question",
        "name": "How do you store assets securely?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "95% of assets are stored in cold storage using offline Hardware Security Modules (HSMs) in geographically distributed vaults with 24/7 security. Private keys never touch internet-connected devices."
        }
      },
      {
        "@type": "Question",
        "name": "What are your custody fees?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Standard custody fee is 0.15% annually. Enterprise accounts ($10M+) receive custom pricing. Setup fee is $2,500 (waived for first month)."
        }
      }
    ]
  };

  const breadcrumbSchema = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {
        "@type": "ListItem",
        "position": 1,
        "name": "Home",
        "item": "https://cryptovault.financial"
      }
    ]
  };

  return (
    <div className="min-h-screen bg-background">
      <Helmet>
        <title>CryptoVault Financial | Institutional Digital Asset Custody - $10B+ Secured</title>
        <meta name="description" content="Trusted by 250+ institutions. Multi-jurisdiction cold storage, real-time proof of reserves, zero breaches since 2019. SOC 2 certified with $500M Lloyd's insurance." />
        <meta name="keywords" content="crypto custody, digital asset custody, institutional custody, bitcoin custody, ethereum custody, cold storage, multi-sig wallet" />
        
        {/* Open Graph */}
        <meta property="og:title" content="CryptoVault Financial | Institutional Digital Asset Custody" />
        <meta property="og:description" content="The custody solution institutions trust with $10B+. Multi-jurisdiction storage, real-time proof of reserves." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cryptovault.financial" />
        <meta property="og:image" content="https://cryptovault.financial/og-image.jpg" />
        
        {/* Twitter Card */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:site" content="@CryptoVaultFin" />
        <meta name="twitter:title" content="CryptoVault Financial | Institutional Custody" />
        <meta name="twitter:description" content="Trusted by 250+ institutions. Zero breaches since 2019." />
        <meta name="twitter:image" content="https://cryptovault.financial/twitter-image.jpg" />
        
        {/* Canonical */}
        <link rel="canonical" href="https://cryptovault.financial" />
        
        {/* Schema.org markup */}
        <script type="application/ld+json">
          {JSON.stringify(organizationSchema)}
        </script>
        <script type="application/ld+json">
          {JSON.stringify(serviceSchema)}
        </script>
        <script type="application/ld+json">
          {JSON.stringify(faqSchema)}
        </script>
        <script type="application/ld+json">
          {JSON.stringify(breadcrumbSchema)}
        </script>
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
