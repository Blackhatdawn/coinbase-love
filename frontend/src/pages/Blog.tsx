import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Calendar, Clock, ArrowRight, User } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

const Blog = () => {
  const posts = [
    {
      id: 1,
      title: "Understanding Bitcoin Halving: What It Means for Investors",
      excerpt: "The Bitcoin halving is one of the most anticipated events in the cryptocurrency world. Learn what it means and how it could impact your portfolio.",
      author: "Sarah Chen",
      date: "June 15, 2025",
      readTime: "8 min read",
      category: "Education",
      image: "https://images.unsplash.com/photo-1518546305927-5a555bb7020d?w=800"
    },
    {
      id: 2,
      title: "CryptoVault Security: How We Protect Your Assets",
      excerpt: "Dive deep into our multi-layered security infrastructure, from cold storage to insurance coverage.",
      author: "Michael Torres",
      date: "June 10, 2025",
      readTime: "6 min read",
      category: "Security",
      image: "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800"
    },
    {
      id: 3,
      title: "DeFi vs CeFi: Making the Right Choice for Your Portfolio",
      excerpt: "Explore the differences between decentralized and centralized finance, and how CryptoVault bridges both worlds.",
      author: "James Liu",
      date: "June 5, 2025",
      readTime: "10 min read",
      category: "Analysis",
      image: "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800"
    },
    {
      id: 4,
      title: "Institutional Adoption: The Future of Cryptocurrency",
      excerpt: "How major financial institutions are embracing digital assets and what it means for retail investors.",
      author: "Emma Rodriguez",
      date: "May 28, 2025",
      readTime: "7 min read",
      category: "Market Insights",
      image: "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800"
    },
    {
      id: 5,
      title: "Staking Explained: Earn Passive Income with Your Crypto",
      excerpt: "A comprehensive guide to cryptocurrency staking and how to maximize your returns on CryptoVault.",
      author: "David Park",
      date: "May 20, 2025",
      readTime: "9 min read",
      category: "Education",
      image: "https://images.unsplash.com/photo-1642790106117-e829e14a795f?w=800"
    },
    {
      id: 6,
      title: "Regulatory Landscape: Navigating Crypto Compliance in 2025",
      excerpt: "Stay informed about the latest regulatory developments and how CryptoVault ensures full compliance.",
      author: "Lisa Wang",
      date: "May 15, 2025",
      readTime: "11 min read",
      category: "Regulation",
      image: "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800"
    }
  ];

  const categories = ["All", "Education", "Security", "Analysis", "Market Insights", "Regulation"];

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-20 pb-16 sm:pt-24 sm:pb-20">
        <div className="container mx-auto px-4">
          {/* Hero */}
          <div className="text-center max-w-3xl mx-auto mb-8 sm:mb-10">
            <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold mb-5">
              CryptoVault <span className="bg-gradient-to-r from-gold-400 to-gold-600 bg-clip-text text-transparent">Blog</span>
            </h1>
            <p className="text-base sm:text-lg text-muted-foreground">
              Stay informed with the latest cryptocurrency news, market analysis, educational content, and platform updates.
            </p>
          </div>

          {/* Categories */}
          <div className="flex flex-wrap justify-center gap-2 mb-8 sm:mb-10">
            {categories.map((category) => (
              <button
                key={category}
                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${category === "All" ? "bg-gold-500 text-black" : "bg-gold-500/10 text-muted-foreground hover:text-gold-400 hover:bg-gold-500/20"}`}
              >
                {category}
              </button>
            ))}
          </div>

          {/* Featured Post */}
          <div className="mb-8 sm:mb-10">
            <div className="glass-card border border-gold-500/10 overflow-hidden group">
              <div className="grid md:grid-cols-2 gap-0">
                <div className="aspect-video md:aspect-auto relative overflow-hidden">
                  <img
                    src={posts[0].image}
                    alt={posts[0].title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute top-4 left-4">
                    <span className="px-3 py-1 bg-gold-500 text-black text-xs font-semibold rounded-full">Featured</span>
                  </div>
                </div>
                <div className="p-6 sm:p-8 flex flex-col justify-center">
                  <span className="text-gold-400 text-sm font-medium mb-2">{posts[0].category}</span>
                  <h2 className="text-xl sm:text-2xl font-bold mb-4 group-hover:text-gold-400 transition-colors">{posts[0].title}</h2>
                  <p className="text-muted-foreground mb-6">{posts[0].excerpt}</p>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground mb-6">
                    <span className="flex items-center gap-1"><User className="h-4 w-4" /> {posts[0].author}</span>
                    <span className="flex items-center gap-1"><Calendar className="h-4 w-4" /> {posts[0].date}</span>
                    <span className="flex items-center gap-1"><Clock className="h-4 w-4" /> {posts[0].readTime}</span>
                  </div>
                  <Button variant="outline" className="w-fit border-gold-500/30 hover:border-gold-400 hover:text-gold-400">
                    Read Article <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Posts Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {posts.slice(1).map((post) => (
              <article key={post.id} className="glass-card border border-gold-500/10 overflow-hidden group">
                <div className="aspect-video relative overflow-hidden">
                  <img
                    src={post.image}
                    alt={post.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute top-4 left-4">
                    <span className="px-3 py-1 bg-background/80 backdrop-blur-sm text-gold-400 text-xs font-medium rounded-full">{post.category}</span>
                  </div>
                </div>
                <div className="p-5 sm:p-6">
                  <h3 className="font-semibold text-lg mb-2 group-hover:text-gold-400 transition-colors line-clamp-2">{post.title}</h3>
                  <p className="text-sm text-muted-foreground mb-4 line-clamp-2">{post.excerpt}</p>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{post.author}</span>
                    <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {post.readTime}</span>
                  </div>
                </div>
              </article>
            ))}
          </div>

          {/* Load More */}
          <div className="text-center mt-12">
            <Button variant="outline" className="border-gold-500/30 hover:border-gold-400 hover:text-gold-400">
              Load More Articles
            </Button>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Blog;
