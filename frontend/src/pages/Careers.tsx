import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { MapPin, Briefcase, Clock, ArrowRight, Users, Rocket, Heart, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";

const Careers = () => {
  const openings = [
    {
      id: 1,
      title: "Senior Backend Engineer",
      department: "Engineering",
      location: "Remote (US/EU)",
      type: "Full-time",
      description: "Build scalable trading infrastructure handling millions of transactions."
    },
    {
      id: 2,
      title: "Security Engineer",
      department: "Security",
      location: "New York, NY",
      type: "Full-time",
      description: "Protect our customers' assets with cutting-edge security solutions."
    },
    {
      id: 3,
      title: "Product Designer",
      department: "Design",
      location: "Remote",
      type: "Full-time",
      description: "Create intuitive experiences for millions of crypto traders worldwide."
    },
    {
      id: 4,
      title: "Compliance Officer",
      department: "Legal & Compliance",
      location: "Wilmington, DE",
      type: "Full-time",
      description: "Ensure regulatory compliance across multiple jurisdictions."
    },
    {
      id: 5,
      title: "Customer Success Manager",
      department: "Support",
      location: "Remote",
      type: "Full-time",
      description: "Help our users navigate the world of digital assets successfully."
    },
    {
      id: 6,
      title: "Blockchain Developer",
      department: "Engineering",
      location: "Remote",
      type: "Full-time",
      description: "Integrate new blockchain protocols and develop smart contract solutions."
    }
  ];

  const benefits = [
    {
      icon: Heart,
      title: "Comprehensive Healthcare",
      description: "Medical, dental, and vision coverage for you and your family"
    },
    {
      icon: Rocket,
      title: "Equity Package",
      description: "Competitive stock options to share in our success"
    },
    {
      icon: Globe,
      title: "Remote-First Culture",
      description: "Work from anywhere with flexible hours"
    },
    {
      icon: Users,
      title: "Learning Budget",
      description: "$5,000 annual budget for courses, conferences, and books"
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-20 sm:pt-24 pb-16 sm:pb-20">
        <div className="container mx-auto px-4">
          {/* Hero */}
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h1 className="font-display text-4xl md:text-5xl font-bold mb-6">
              Build the Future of <span className="bg-gradient-to-r from-gold-400 to-gold-600 bg-clip-text text-transparent">Finance</span>
            </h1>
            <p className="text-lg text-muted-foreground mb-8">
              Join our team of passionate individuals working to make cryptocurrency accessible, secure, and trusted by everyone.
            </p>
            <div className="flex items-center justify-center gap-8 text-sm text-muted-foreground">
              <span className="flex items-center gap-2"><Users className="h-4 w-4 text-gold-400" /> 200+ Team Members</span>
              <span className="flex items-center gap-2"><Globe className="h-4 w-4 text-gold-400" /> 30+ Countries</span>
              <span className="flex items-center gap-2"><Rocket className="h-4 w-4 text-gold-400" /> Series B Funded</span>
            </div>
          </div>

          {/* Benefits */}
          <section className="mb-20">
            <h2 className="text-2xl font-bold mb-8 text-center">Why Work at CryptoVault?</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {benefits.map((benefit) => (
                <div key={benefit.title} className="glass-card p-6 border border-gold-500/10 text-center">
                  <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-gold-500/10 flex items-center justify-center">
                    <benefit.icon className="h-6 w-6 text-gold-400" />
                  </div>
                  <h3 className="font-semibold mb-2">{benefit.title}</h3>
                  <p className="text-sm text-muted-foreground">{benefit.description}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Open Positions */}
          <section>
            <h2 className="text-2xl font-bold mb-8 flex items-center gap-2">
              <span className="h-8 w-1 bg-gradient-to-b from-gold-400 to-gold-600 rounded-full"></span>
              Open Positions
            </h2>
            <div className="space-y-4">
              {openings.map((job) => (
                <div key={job.id} className="glass-card p-6 border border-gold-500/10 hover:border-gold-500/30 transition-all group">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-semibold group-hover:text-gold-400 transition-colors">{job.title}</h3>
                      <p className="text-sm text-muted-foreground mb-2">{job.description}</p>
                      <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1"><Briefcase className="h-3 w-3" /> {job.department}</span>
                        <span className="flex items-center gap-1"><MapPin className="h-3 w-3" /> {job.location}</span>
                        <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {job.type}</span>
                      </div>
                    </div>
                    <Button variant="outline" className="border-gold-500/30 hover:border-gold-400 hover:text-gold-400 shrink-0">
                      Apply Now <ArrowRight className="h-4 w-4 ml-2" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* CTA */}
          <section className="mt-20 text-center">
            <div className="glass-card p-8 border border-gold-500/20 bg-gradient-to-br from-gold-500/5 to-transparent">
              <h3 className="text-2xl font-bold mb-4">Don't See Your Role?</h3>
              <p className="text-muted-foreground mb-6 max-w-xl mx-auto">
                We're always looking for talented individuals. Send us your resume and let us know how you can contribute to our mission.
              </p>
              <Button className="bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black">
                Send Open Application
              </Button>
            </div>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Careers;
