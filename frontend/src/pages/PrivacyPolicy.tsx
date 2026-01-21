import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { resolveSupportEmail, resolveAppUrl } from "@/lib/runtimeConfig";

const PrivacyPolicy = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-24 pb-20">
        <div className="container mx-auto px-4 max-w-4xl">
          <h1 className="font-display text-4xl md:text-5xl font-bold mb-8">Privacy Policy</h1>
          
          <div className="prose prose-invert max-w-none space-y-8 text-muted-foreground">
            <section>
              <h2 className="text-2xl font-bold text-foreground mb-4">Introduction</h2>
              <p>
                CryptoVault ("we" or "us" or "our") operates the website. This page informs you of our policies regarding the collection, 
                use, and disclosure of personal data when you use our service and the choices you have associated with that data.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-foreground mb-4">Information Collection and Use</h2>
              <p>
                We collect several different types of information for various purposes to provide and improve our service to you.
              </p>
              <h3 className="text-lg font-semibold text-foreground mt-4 mb-2">Types of Data Collected:</h3>
              <ul className="list-disc list-inside space-y-2">
                <li><strong>Personal Data:</strong> Email address, first name and last name, phone number, address, city, state, postal code, country</li>
                <li><strong>Usage Data:</strong> Browser type, IP address, pages visited, time and date of visit, time spent on pages</li>
                <li><strong>Financial Data:</strong> Information about cryptocurrency transactions and account balances</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-foreground mb-4">Use of Data</h2>
              <p>
                CryptoVault uses the collected data for various purposes:
              </p>
              <ul className="list-disc list-inside space-y-2 mt-4">
                <li>To provide and maintain our service</li>
                <li>To notify you about changes to our service</li>
                <li>To allow you to participate in interactive features when you choose to do so</li>
                <li>To provide customer support</li>
                <li>To gather analysis or valuable information so that we can improve our service</li>
                <li>To monitor the usage of our service</li>
                <li>To detect, prevent and address technical issues and fraud</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-foreground mb-4">Security of Data</h2>
              <p>
                The security of your data is important to us, but remember that no method of transmission over the Internet or method of electronic storage 
                is 100% secure. While we strive to use commercially acceptable means to protect your personal data, we cannot guarantee its absolute security.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-foreground mb-4">Changes to This Privacy Policy</h2>
              <p>
                We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and 
                updating the "effective date" at the bottom of this Privacy Policy.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-foreground mb-4">Contact Us</h2>
              <p>
                If you have any questions about this Privacy Policy, please contact us at:
              </p>
              <ul className="list-disc list-inside space-y-2 mt-4">
                <li>By email: <a href={`mailto:${resolveSupportEmail()}`} className="text-primary hover:underline">{resolveSupportEmail()}</a></li>
                <li>By visiting this page on our website: <a href={`${resolveAppUrl()}/contact`} className="text-primary hover:underline">{resolveAppUrl()}/contact</a></li>
              </ul>
            </section>

            <p className="text-sm pt-8 border-t border-border/50">
              Last updated: January 2024
            </p>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default PrivacyPolicy;
