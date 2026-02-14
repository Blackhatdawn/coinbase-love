import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Mail, Phone, MapPin, MessageSquare } from "lucide-react";
import { useState } from "react";
import { resolveSupportEmail } from "@/lib/runtimeConfig";
import { api } from "@/lib/apiClient";
import { toast } from "sonner";

const Contact = () => {
  const supportEmail = resolveSupportEmail();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    company: "",
    phone: "",
    subject: "",
    message: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.contact.submit({
        name: formData.name,
        email: formData.email,
        company: formData.company || undefined,
        phone: formData.phone || undefined,
        subject: formData.subject,
        message: formData.message,
      });
      toast.success("Message sent! Our team will contact you soon.");
      setFormData({
        name: "",
        email: "",
        company: "",
        phone: "",
        subject: "",
        message: "",
      });
    } catch (error: any) {
      toast.error(error?.message || "Failed to submit message. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-20 sm:pt-24 pb-16 sm:pb-20">
        <div className="container mx-auto px-4">
          {/* Header */}
          <div className="mb-10 sm:mb-16 animate-fade-in">
            <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold mb-3">
              Get in <span className="text-gradient">Touch</span>
            </h1>
            <p className="text-base sm:text-lg text-muted-foreground max-w-2xl">
              Have questions about CryptoVault? Our sales team is here to help you find the perfect solution for your needs.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 sm:gap-8 mb-12 sm:mb-16">
            {/* Contact Info */}
            <div className="space-y-6">
              {/* Email */}
              <Card className="p-4 sm:p-6 border-border/50 bg-secondary/20 backdrop-blur">
                <div className="flex items-start gap-4">
                  <div className="h-10 w-10 sm:h-12 sm:w-12 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                    <Mail className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-medium mb-1">Email</h3>
                    <p className="text-sm text-muted-foreground mb-3">{supportEmail}</p>
                    <Button variant="outline" size="sm" asChild>
                      <a href={`mailto:${supportEmail}`}>Send Email</a>
                    </Button>
                  </div>
                </div>
              </Card>

              {/* Live Chat - Intercom ready */}
              <Card className="p-4 sm:p-6 border-border/50 bg-secondary/20 backdrop-blur">
                <div className="flex items-start gap-4">
                  <div className="h-10 w-10 sm:h-12 sm:w-12 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                    <MessageSquare className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-medium mb-1">Live Chat</h3>
                    <p className="text-sm text-muted-foreground mb-3">24/7 Support Available</p>
                    <Button variant="outline" size="sm" asChild>
                      <a href={`mailto:${supportEmail}?subject=Live%20Support%20Request`}>Start Support Chat</a>
                    </Button>
                  </div>
                </div>
              </Card>

              {/* Address */}
              <Card className="p-4 sm:p-6 border-border/50 bg-secondary/20 backdrop-blur">
                <div className="flex items-start gap-4">
                  <div className="h-10 w-10 sm:h-12 sm:w-12 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
                    <MapPin className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-medium mb-1">Office</h3>
                    <p className="text-sm text-muted-foreground">
                      CryptoVault Financial, Inc.<br />
                      1201 Market Street, Suite 101<br />
                      Wilmington, DE 19801
                    </p>
                  </div>
                </div>
              </Card>
            </div>

            {/* Contact Form */}
            <div className="lg:col-span-2">
              <Card className="p-5 sm:p-8 border-border/50 bg-secondary/20 backdrop-blur">
                <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
                  {/* Name */}
                  <div>
                    <label className="block text-sm font-medium mb-2">Name</label>
                    <Input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      placeholder="Your name"
                      required
                    />
                  </div>

                  {/* Email */}
                  <div>
                    <label className="block text-sm font-medium mb-2">Email</label>
                    <Input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="your@email.com"
                      required
                    />
                  </div>

                  {/* Company */}
                  <div>
                    <label className="block text-sm font-medium mb-2">Company (Optional)</label>
                    <Input
                      type="text"
                      name="company"
                      value={formData.company}
                      onChange={handleChange}
                      placeholder="Your company name"
                    />
                  </div>

                  {/* Phone */}
                  <div>
                    <label className="block text-sm font-medium mb-2">Phone (Optional)</label>
                    <Input
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      placeholder="+1 (555) 000-0000"
                    />
                  </div>

                  {/* Subject */}
                  <div>
                    <label className="block text-sm font-medium mb-2">Subject</label>
                    <Input
                      type="text"
                      name="subject"
                      value={formData.subject}
                      onChange={handleChange}
                      placeholder="How can we help?"
                      required
                    />
                  </div>

                  {/* Message */}
                  <div>
                    <label className="block text-sm font-medium mb-2">Message</label>
                    <textarea
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      placeholder="Tell us about your inquiry..."
                      rows={5}
                      className="w-full px-4 py-3 rounded-lg border border-border/50 bg-background/50 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent"
                      required
                    />
                  </div>

                  <Button variant="hero" size="lg" className="w-full">
                    Send Message
                  </Button>
                </form>
              </Card>
            </div>
          </div>

          {/* FAQ Section */}
          <Card className="p-8 border-border/50 bg-secondary/20 backdrop-blur">
            <div className="flex items-start gap-4 mb-8">
              <MessageSquare className="h-6 w-6 text-primary flex-shrink-0 mt-1" />
              <div>
                <h2 className="font-display text-2xl font-bold mb-2">Frequently Asked Questions</h2>
                <p className="text-muted-foreground">Can't find what you're looking for? Check out our FAQ section.</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {[
                {
                  q: "What are your typical response times?",
                  a: "We aim to respond to all inquiries within 24 business hours.",
                },
                {
                  q: "Do you offer enterprise solutions?",
                  a: "Yes, we offer customized enterprise packages. Contact our sales team for details.",
                },
                {
                  q: "What support channels are available?",
                  a: "We support email, phone, live chat, and in-person meetings for larger clients.",
                },
                {
                  q: "Can I schedule a demo?",
                  a: "Absolutely! Fill out the form above and mention your preferred demo time.",
                },
              ].map((faq, index) => (
                <div key={index}>
                  <h3 className="font-medium mb-2">{faq.q}</h3>
                  <p className="text-sm text-muted-foreground">{faq.a}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Contact;
