import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Mail, Lock, User, ArrowLeft, Eye, EyeOff, Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/apiClient";
import { signUpSchema, signInSchema, validateFormData } from "@/lib/validation";
import OTPVerificationModal from "@/components/OTPVerificationModal";
import RecommendedSetup from "@/components/RecommendedSetup";

interface ValidationError {
  field: string;
  message: string;
}

const Auth = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [emailVerificationStep, setEmailVerificationStep] = useState(false);
  const [verificationCode, setVerificationCode] = useState("");
  const [pendingEmail, setPendingEmail] = useState("");
  const [pendingUserName, setPendingUserName] = useState("");
  const [showOTPModal, setShowOTPModal] = useState(false);
  const [showRecommendedSetup, setShowRecommendedSetup] = useState(false);

  const { signIn, signUp } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  /**
   * Validate form using Zod schema based on current mode (login/signup)
   */
  const validateForm = (): boolean => {
    const schema = isLogin ? signInSchema : signUpSchema;
    const formData = isLogin
      ? { email, password }
      : { email, password, name };

    const fieldErrors = validateFormData(schema, formData);
    const newErrors: ValidationError[] = Object.entries(fieldErrors).map(([field, message]) => ({
      field,
      message,
    }));

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  /**
   * Get error message for a specific field
   */
  const getFieldError = (field: string): string | null => {
    const error = errors.find(e => e.field === field);
    return error ? error.message : null;
  };

  const handleVerifyEmail = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!verificationCode.trim()) {
      toast({
        title: "Verification code required",
        description: "Please enter the verification code or paste the token",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      await api.auth.verifyEmail(verificationCode, pendingEmail);

      toast({
        title: "Email verified!",
        description: "Your email has been verified. You can now sign in.",
      });

      // Reset form and show login
      setEmailVerificationStep(false);
      setVerificationCode("");
      setPendingEmail("");
      setIsLogin(true);
      setEmail("");
      setPassword("");
      setName("");
    } catch (error: any) {
      toast({
        title: "Verification failed",
        description: error.message || "Invalid or expired verification token",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate form before submitting
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      if (isLogin) {
        const result = await signIn(email, password);

        if (result.error) {
          // Check if error is due to unverified email
          if (result.error.includes("Email not verified")) {
            toast({
              title: "Email not verified",
              description: "Please verify your email address first. Check your inbox for a verification link.",
              variant: "destructive",
            });
          } else {
            toast({
              title: "Sign in failed",
              description: result.error,
              variant: "destructive",
            });
          }
        } else {
          toast({
            title: "Welcome back!",
            description: "You have successfully signed in",
          });
          navigate("/");
        }
      } else {
        const result = await signUp(email, password, name);

        if (result.error) {
          toast({
            title: "Sign up failed",
            description: result.error,
            variant: "destructive",
          });
        } else {
          toast({
            title: "Account created!",
            description: "Please check your email for a verification code.",
          });

          // Store user info and show OTP modal
          setPendingEmail(email);
          setPendingUserName(name);
          setShowOTPModal(true);
        }
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-background to-accent/20" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,hsl(var(--primary)/0.3),transparent_50%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,hsl(var(--accent)/0.3),transparent_50%)]" />
        
        <div className="relative z-10 flex flex-col justify-center px-12 xl:px-20">
          <div className="flex items-center gap-3 mb-8">
            <img 
              src="/cryptovault-logo.png" 
              alt="CryptoVault" 
              className="h-12 w-12 object-contain"
            />
            <span className="font-display text-3xl font-bold">CryptoVault</span>
          </div>
          
          <h1 className="text-4xl xl:text-5xl font-display font-bold mb-6 leading-tight">
            Your Gateway to<br />
            <span className="text-gradient">Digital Assets</span>
          </h1>
          
          <p className="text-lg text-muted-foreground max-w-md mb-12">
            Join millions of users trading cryptocurrencies securely. Start your journey with CryptoVault today.
          </p>
          
          <div className="grid grid-cols-3 gap-6">
            <div className="glass-card p-4 rounded-xl">
              <div className="text-2xl font-bold text-primary">$2.8T+</div>
              <div className="text-sm text-muted-foreground">Trading Volume</div>
            </div>
            <div className="glass-card p-4 rounded-xl">
              <div className="text-2xl font-bold text-primary">100M+</div>
              <div className="text-sm text-muted-foreground">Users</div>
            </div>
            <div className="glass-card p-4 rounded-xl">
              <div className="text-2xl font-bold text-primary">150+</div>
              <div className="text-sm text-muted-foreground">Countries</div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Right Panel - Auth Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <button 
              onClick={() => navigate("/")}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div className="flex items-center gap-2">
              <img 
                src="/cryptovault-logo.png" 
                alt="CryptoVault" 
                className="h-9 w-9 object-contain"
              />
              <span className="font-display text-xl font-bold">CryptoVault</span>
            </div>
          </div>
          
          <div className="hidden lg:block mb-8">
            <button 
              onClick={() => navigate("/")}
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to home
            </button>
          </div>
          
          {emailVerificationStep ? (
            <>
              <h2 className="text-2xl sm:text-3xl font-display font-bold mb-2">
                Verify Your Email
              </h2>
              <p className="text-muted-foreground mb-8">
                We've sent a verification link to {pendingEmail}. Enter the verification code below.
              </p>
            </>
          ) : (
            <>
              <h2 className="text-2xl sm:text-3xl font-display font-bold mb-2">
                {isLogin ? "Welcome back" : "Create account"}
              </h2>
              <p className="text-muted-foreground mb-8">
                {isLogin
                  ? "Enter your credentials to access your account"
                  : "Start your crypto journey today"}
              </p>
            </>
          )}

          <form onSubmit={emailVerificationStep ? handleVerifyEmail : handleSubmit} className="space-y-5">
            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="name"
                    type="text"
                    placeholder="John Doe"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className={`pl-10 h-12 bg-muted/50 border-border/50 focus:border-primary ${
                      getFieldError("name") ? "border-destructive" : ""
                    }`}
                  />
                </div>
                {getFieldError("name") && (
                  <p className="text-xs text-destructive">{getFieldError("name")}</p>
                )}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={`pl-10 h-12 bg-muted/50 border-border/50 focus:border-primary ${
                    getFieldError("email") ? "border-destructive" : ""
                  }`}
                />
              </div>
              {getFieldError("email") && (
                <p className="text-xs text-destructive">{getFieldError("email")}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`pl-10 pr-10 h-12 bg-muted/50 border-border/50 focus:border-primary ${
                    getFieldError("password") ? "border-destructive" : ""
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {getFieldError("password") && (
                <p className="text-xs text-destructive">{getFieldError("password")}</p>
              )}
              {!isLogin && !getFieldError("password") && password && (
                <p className="text-xs text-muted-foreground">
                  ✓ Password meets security requirements
                </p>
              )}
            </div>
            
            {isLogin && (
              <div className="flex justify-end">
                <button type="button" className="text-sm text-primary hover:underline">
                  Forgot password?
                </button>
              </div>
            )}
            
            <Button 
              type="submit" 
              variant="gradient" 
              size="lg" 
              className="w-full h-12"
              disabled={isLoading}
            >
              {isLoading ? "Please wait..." : isLogin ? "Sign In" : "Create Account"}
            </Button>
          </form>
          
          <div className="mt-8 text-center">
            <p className="text-muted-foreground">
              {isLogin ? "Don't have an account?" : "Already have an account?"}
              {" "}
              <button
                type="button"
                onClick={() => setIsLogin(!isLogin)}
                className="text-primary hover:underline font-medium"
              >
                {isLogin ? "Sign up" : "Sign in"}
              </button>
            </p>
          </div>
          
          <p className="mt-8 text-xs text-center text-muted-foreground">
            By continuing, you agree to our{" "}
            <a href="/terms" className="underline hover:text-foreground">Terms of Service</a>
            {" "}and{" "}
            <a href="/privacy" className="underline hover:text-foreground">Privacy Policy</a>
          </p>
        </div>
      </div>

      {/* OTP Verification Modal */}
      <OTPVerificationModal
        isOpen={showOTPModal}
        onClose={() => setShowOTPModal(false)}
        email={pendingEmail}
        onVerify={async (code: string) => {
          try {
            await api.auth.verifyEmail(code, pendingEmail);
            return true;
          } catch (error) {
            return false;
          }
        }}
        onResend={async () => {
          try {
            await api.auth.resendVerification(pendingEmail);
            toast({
              title: "Code resent",
              description: "A new verification code has been sent to your email.",
            });
            return true;
          } catch (error) {
            return false;
          }
        }}
        onSuccess={() => {
          setShowOTPModal(false);
          setShowRecommendedSetup(true);
        }}
      />

      {/* Recommended Setup Modal */}
      <RecommendedSetup
        isOpen={showRecommendedSetup}
        onClose={() => setShowRecommendedSetup(false)}
        userName={pendingUserName || name}
      />
    </div>
  );
};

export default Auth;
