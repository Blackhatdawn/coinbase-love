import Header from "@/components/Header";
import Footer from "@/components/Footer";

const TermsOfService = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-24 pb-20">
        <div className="container mx-auto px-4 max-w-4xl">
          <h1 className="font-display text-4xl md:text-5xl font-bold mb-8">Terms of Service</h1>
          
          <div className="prose prose-invert max-w-none space-y-8 text-muted-foreground">
            <section>
              <h2 className="text-2xl font-bold text-foreground mb-4">1. Acceptance of Terms</h2>
              <p>
                By accessing and using CryptoVault, you accept and agree to be bound by the terms and provision of this agreement.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-foreground mb-4">2. Use License</h2>
              <p>
                Permission is granted to temporarily download one copy of the materials (information or software) from CryptoVault for personal, 
                non-commercial transitory viewing only. This is the grant of a license, not a transfer of title, and under this license you may not:
              </p>
              <ul className="list-disc list-inside space-y-2 mt-4">
                <li>Modify or copy the materials</li>
                <li>Use the materials for any commercial purpose or for any public display</li>
                <li>Attempt to decompile or reverse engineer any software contained on CryptoVault</li>
                <li>Remove any copyright or other proprietary notations from the materials</li>
                <li>Transfer the materials to another person or "mirror" the materials on any other server</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-foreground mb-4">3. Disclaimer</h2>
              <p>
                The materials on CryptoVault are provided on an 'as is' basis. CryptoVault makes no warranties, expressed or implied, 
                and hereby disclaims and negates all other warranties including, without limitation, implied warranties or conditions of merchantability, 
                fitness for a particular purpose, or non-infringement of intellectual property or other violation of rights.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-foreground mb-4">4. Limitations</h2>
              <p>
                In no event shall CryptoVault or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, 
                or due to business interruption) arising out of the use or inability to use the materials on CryptoVault.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-foreground mb-4">5. Accuracy of Materials</h2>
              <p>
                The materials appearing on CryptoVault could include technical, typographical, or photographic errors. CryptoVault does not warrant that 
                any of the materials on its website are accurate, complete, or current.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-foreground mb-4">6. Links</h2>
              <p>
                CryptoVault has not reviewed all of the sites linked to its website and is not responsible for the contents of any such linked site. 
                The inclusion of any link does not imply endorsement by CryptoVault of the site. Use of any such linked website is at the user's own risk.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-foreground mb-4">7. Modifications</h2>
              <p>
                CryptoVault may revise these terms of service for its website at any time without notice. By using this website, you are agreeing to 
                be bound by the then current version of these terms of service.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-foreground mb-4">8. Governing Law</h2>
              <p>
                These terms and conditions are governed by and construed in accordance with the laws of the jurisdiction in which CryptoVault operates, 
                and you irrevocably submit to the exclusive jurisdiction of the courts in that location.
              </p>
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

export default TermsOfService;
