import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { resolveSupportEmail } from "@/lib/runtimeConfig";
import { Cookie, Info, Settings, Shield } from "lucide-react";

const CookiePolicy = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-24 pb-20">
        <div className="container mx-auto px-4 max-w-4xl">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gold-500/10 flex items-center justify-center">
              <Cookie className="h-8 w-8 text-gold-400" />
            </div>
            <h1 className="font-display text-4xl md:text-5xl font-bold mb-4">
              Cookie <span className="bg-gradient-to-r from-gold-400 to-gold-600 bg-clip-text text-transparent">Policy</span>
            </h1>
            <p className="text-muted-foreground">Last updated: June 1, 2025</p>
          </div>

          {/* Content */}
          <div className="prose prose-invert max-w-none space-y-8">
            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Info className="h-5 w-5 text-gold-400" />
                What Are Cookies?
              </h2>
              <p className="text-muted-foreground leading-relaxed">
                Cookies are small text files that are placed on your computer or mobile device when you visit our website. They help us provide you with a better experience by remembering your preferences, analyzing how you use our platform, and enabling certain features.
              </p>
            </section>

            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Settings className="h-5 w-5 text-gold-400" />
                Types of Cookies We Use
              </h2>
              
              <div className="space-y-6">
                <div>
                  <h3 className="font-semibold text-gold-400 mb-2">Essential Cookies</h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    These cookies are necessary for the website to function and cannot be switched off. They are usually set in response to actions made by you, such as setting your privacy preferences, logging in, or filling in forms. These include:
                  </p>
                  <ul className="list-disc list-inside text-sm text-muted-foreground mt-2 space-y-1">
                    <li>Authentication cookies (session management)</li>
                    <li>Security cookies (CSRF protection)</li>
                    <li>Load balancing cookies</li>
                  </ul>
                </div>

                <div>
                  <h3 className="font-semibold text-gold-400 mb-2">Performance Cookies</h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    These cookies allow us to count visits and traffic sources so we can measure and improve the performance of our site. They help us know which pages are the most and least popular. All information collected is aggregated and anonymous.
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold text-gold-400 mb-2">Functional Cookies</h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    These cookies enable enhanced functionality and personalization, such as remembering your language preference, display settings, and trading preferences.
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold text-gold-400 mb-2">Targeting Cookies</h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    These cookies may be set through our site by our advertising partners. They may be used to build a profile of your interests and show you relevant adverts on other sites. They do not store directly personal information but are based on uniquely identifying your browser and internet device.
                  </p>
                </div>
              </div>
            </section>

            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Shield className="h-5 w-5 text-gold-400" />
                Managing Your Cookie Preferences
              </h2>
              <p className="text-muted-foreground leading-relaxed mb-4">
                You can control and manage cookies in various ways. Please note that removing or blocking cookies may impact your user experience and parts of our website may no longer be fully accessible.
              </p>
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Browser Settings</h3>
                  <p className="text-muted-foreground text-sm">
                    Most browsers allow you to refuse to accept cookies and to delete cookies. The methods for doing so vary from browser to browser. You can obtain up-to-date information about blocking and deleting cookies via your browser's support pages.
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Our Cookie Settings</h3>
                  <p className="text-muted-foreground text-sm">
                    You can adjust your cookie preferences at any time using the cookie settings button in the footer of our website or by contacting our support team.
                  </p>
                </div>
              </div>
            </section>

            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4">Cookie Retention</h2>
              <p className="text-muted-foreground leading-relaxed">
                The length of time cookies remain on your device depends on the type of cookie. Session cookies only last for your browsing session and are deleted when you close your browser. Persistent cookies stay on your device until they expire or are deleted manually.
              </p>
              <ul className="list-disc list-inside text-sm text-muted-foreground mt-4 space-y-1">
                <li>Session cookies: Deleted when browser closes</li>
                <li>Authentication cookies: 7-30 days</li>
                <li>Preference cookies: 1 year</li>
                <li>Analytics cookies: Up to 2 years</li>
              </ul>
            </section>

            <section className="glass-card p-6 border border-gold-500/10">
              <h2 className="text-xl font-bold mb-4">Contact Us</h2>
              <p className="text-muted-foreground leading-relaxed">
                If you have any questions about our use of cookies or this Cookie Policy, please contact us at:
              </p>
              <div className="mt-4 text-sm">
                <p><strong>Email:</strong> <a href={`mailto:${resolveSupportEmail()}`} className="text-primary hover:underline">{resolveSupportEmail()}</a></p>
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

export default CookiePolicy;
