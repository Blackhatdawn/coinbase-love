import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Shield, Target, Eye, Users, Building2, Award } from "lucide-react";
import { resolveSupportEmail } from "@/lib/runtimeConfig";

const About = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-20 sm:pt-24">
        {/* Hero Section */}
        <section className="section-padding bg-gradient-to-b from-secondary/30 to-background">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-6">
                <Building2 className="h-4 w-4 text-primary" />
                <span className="text-sm text-primary font-medium">Delaware C-Corp</span>
              </div>
              <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold mb-6">
                Building Trust in <span className="text-gradient">Digital Asset Custody</span>
              </h1>
              <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto">
                CryptoVault Financial is an institutional-grade digital asset custody platform,
                providing secure storage and management solutions for individuals and enterprises.
              </p>
            </div>
          </div>
        </section>

        {/* Founder Section */}
        <section className="section-padding">
          <div className="container mx-auto px-4">
            <div className="max-w-6xl mx-auto">
              <div className="grid md:grid-cols-2 gap-8 sm:gap-12 items-center">
                <div>
                  <div className="w-64 h-64 mx-auto md:mx-0 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center mb-6">
                    <Users className="h-32 w-32 text-primary/50" />
                  </div>
                </div>
                <div>
                  <h2 className="font-display text-2xl sm:text-3xl font-bold mb-4">Meet Our Founder</h2>
                  <h3 className="text-xl text-primary font-semibold mb-2">Alex Rivera</h3>
                  <p className="text-muted-foreground mb-4">Founder & CEO, CryptoVault Financial</p>
                  <p className="text-muted-foreground leading-relaxed mb-4">
                    Alex Rivera brings over 15 years of experience in financial technology and cybersecurity.
                    Previously serving as VP of Security at major financial institutions, Alex founded
                    CryptoVault Financial with a mission to bring institutional-grade security to everyone.
                  </p>
                  <p className="text-muted-foreground leading-relaxed">
                    "Our goal is to make digital asset custody as secure and accessible as traditional banking,
                    while maintaining the transparency and innovation that defines the crypto industry."
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Mission & Values */}
        <section className="section-padding bg-secondary/20">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center mb-10 sm:mb-12">
              <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-bold mb-4">
                Our Mission & Values
              </h2>
              <p className="text-muted-foreground">
                Guided by transparency, security, and innovation
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6 sm:gap-8 max-w-5xl mx-auto">
              <div className="glass-card p-6 sm:p-8 text-center" data-testid="mission-security">
                <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6">
                  <Shield className="h-6 w-6 sm:h-8 sm:w-8 text-primary" />
                </div>
                <h3 className="font-display text-xl font-semibold mb-3">Security First</h3>
                <p className="text-muted-foreground text-sm">
                  We prioritize the security of your assets above all else, employing
                  military-grade encryption and cold storage solutions.
                </p>
              </div>

              <div className="glass-card p-6 sm:p-8 text-center" data-testid="mission-transparency">
                <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6">
                  <Eye className="h-6 w-6 sm:h-8 sm:w-8 text-primary" />
                </div>
                <h3 className="font-display text-xl font-semibold mb-3">Transparency</h3>
                <p className="text-muted-foreground text-sm">
                  Full visibility into our operations, proof-of-reserves,
                  and regular third-party audits to build trust.
                </p>
              </div>

              <div className="glass-card p-6 sm:p-8 text-center" data-testid="mission-innovation">
                <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6">
                  <Target className="h-6 w-6 sm:h-8 sm:w-8 text-primary" />
                </div>
                <h3 className="font-display text-xl font-semibold mb-3">Innovation</h3>
                <p className="text-muted-foreground text-sm">
                  Continuously advancing our technology to provide
                  cutting-edge custody solutions for the evolving digital asset landscape.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Company Info */}
        <section className="section-padding">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              <div className="grid md:grid-cols-2 gap-8 sm:gap-12">
                <div className="glass-card p-6 sm:p-8">
                  <Award className="h-10 w-10 text-primary mb-4" />
                  <h3 className="font-display text-xl font-semibold mb-3">Corporate Structure</h3>
                  <ul className="space-y-3 text-muted-foreground text-sm">
                    <li className="flex items-start gap-2">
                      <span className="text-primary">•</span>
                      Delaware C-Corporation
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-primary">•</span>
                      Registered with FinCEN as Money Services Business
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-primary">•</span>
                      State money transmitter licenses (in progress)
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-primary">•</span>
                      SOC 2 Type II certification (in progress)
                    </li>
                  </ul>
                </div>

                <div className="glass-card p-6 sm:p-8">
                  <Building2 className="h-10 w-10 text-primary mb-4" />
                  <h3 className="font-display text-xl font-semibold mb-3">Headquarters</h3>
                  <address className="not-italic text-muted-foreground text-sm space-y-2">
                    <p>CryptoVault Financial, Inc.</p>
                    <p>1201 Market Street, Suite 101</p>
                    <p>Wilmington, DE 19801</p>
                    <p>United States</p>
                    <p className="pt-2">
                      <a href={`mailto:${resolveSupportEmail()}`} className="text-primary hover:underline">
                        {resolveSupportEmail()}
                      </a>
                    </p>
                  </address>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default About;
