import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { BookOpen, Video, Users, Award } from "lucide-react";

const courses = [
  {
    icon: BookOpen,
    title: "Crypto Basics",
    description: "Learn the fundamentals of blockchain and cryptocurrencies",
    level: "Beginner",
    duration: "2 hours",
    lessons: 12,
  },
  {
    icon: Video,
    title: "Trading Strategies",
    description: "Master technical analysis and develop winning trading strategies",
    level: "Intermediate",
    duration: "4 hours",
    lessons: 18,
  },
  {
    icon: Users,
    title: "Portfolio Management",
    description: "Diversify and manage your crypto portfolio effectively",
    level: "Advanced",
    duration: "3 hours",
    lessons: 15,
  },
  {
    icon: Award,
    title: "Smart Contract Development",
    description: "Build decentralized applications on the blockchain",
    level: "Advanced",
    duration: "6 hours",
    lessons: 24,
  },
];

const resources = [
  { title: "Whitepaper Library", icon: "📄", description: "Access original Bitcoin and Ethereum whitepapers" },
  { title: "Market Analysis", icon: "📊", description: "Daily market insights and trend analysis" },
  { title: "Community Forum", icon: "💬", description: "Connect with other crypto enthusiasts" },
  { title: "Developer Docs", icon: "⚙️", description: "Technical documentation for builders" },
];

const Learn = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-24 pb-20">
        <div className="container mx-auto px-4">
          {/* Header */}
          <div className="mb-16 animate-fade-in">
            <h1 className="font-display text-4xl md:text-5xl font-bold mb-3">
              Learn & <span className="text-gradient">Educate</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl">
              Start your crypto journey with comprehensive courses, tutorials, and resources from industry experts.
            </p>
          </div>

          {/* Courses */}
          <h2 className="font-display text-3xl font-bold mb-8">Featured Courses</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
            {courses.map((course) => {
              const IconComponent = course.icon;
              return (
                <Card
                  key={course.title}
                  className="p-8 border-border/50 bg-secondary/20 backdrop-blur hover:border-primary/50 transition-colors group cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-6">
                    <div className="h-12 w-12 rounded-lg bg-primary/20 flex items-center justify-center group-hover:bg-primary/30 transition-colors flex-shrink-0">
                      <IconComponent className="h-6 w-6 text-primary" />
                    </div>
                    <span className="inline-flex px-3 py-1 rounded-full bg-primary/20 text-primary text-xs font-medium">
                      {course.level}
                    </span>
                  </div>

                  <h3 className="font-display text-xl font-bold mb-2">{course.title}</h3>
                  <p className="text-muted-foreground mb-6">{course.description}</p>

                  {/* Course Meta */}
                  <div className="flex items-center gap-6 mb-8 text-sm text-muted-foreground">
                    <span>{course.duration}</span>
                    <span className="h-1 w-1 rounded-full bg-border" />
                    <span>{course.lessons} lessons</span>
                  </div>

                  <Button variant="hero" className="w-full">
                    Start Learning
                  </Button>
                </Card>
              );
            })}
          </div>

          {/* Resources */}
          <h2 className="font-display text-3xl font-bold mb-8">Learning Resources</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-16">
            {resources.map((resource) => (
              <Card
                key={resource.title}
                className="p-6 border-border/50 bg-secondary/20 backdrop-blur hover:border-primary/50 transition-colors group cursor-pointer"
              >
                <div className="text-3xl mb-4">{resource.icon}</div>
                <h3 className="font-medium mb-2">{resource.title}</h3>
                <p className="text-sm text-muted-foreground">{resource.description}</p>
              </Card>
            ))}
          </div>

          {/* CTA */}
          <Card className="p-12 border-border/50 bg-gradient-to-r from-primary/10 to-accent/10 backdrop-blur text-center">
            <h2 className="font-display text-3xl font-bold mb-3">Ready to Master Crypto?</h2>
            <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
              Join thousands of learners who have expanded their crypto knowledge with our courses.
            </p>
            <Button variant="hero" size="lg">
              Explore All Courses
            </Button>
          </Card>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Learn;
