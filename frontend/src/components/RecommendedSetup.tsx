import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Check, ChevronRight, Shield, Bell, Smartphone, Key, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useNavigate } from 'react-router-dom';

interface RecommendedSetupProps {
  isOpen: boolean;
  onClose: () => void;
  userName: string;
}

const setupSteps = [
  {
    id: 'security',
    icon: Shield,
    title: 'Enable Two-Factor Authentication',
    description: 'Add an extra layer of security to your account',
    action: '/dashboard/settings/security',
    recommended: true
  },
  {
    id: 'notifications',
    icon: Bell,
    title: 'Set Up Notifications',
    description: 'Stay informed about your account activity',
    action: '/dashboard/settings/notifications',
    recommended: true
  },
  {
    id: 'mobile',
    icon: Smartphone,
    title: 'Connect Mobile App',
    description: 'Access CryptoVault on the go',
    action: null, // Coming soon
    recommended: false
  },
  {
    id: 'api',
    icon: Key,
    title: 'Generate API Keys',
    description: 'For developers and automated trading',
    action: '/dashboard/settings/api',
    recommended: false
  }
];

export function RecommendedSetup({ isOpen, onClose, userName }: RecommendedSetupProps) {
  const navigate = useNavigate();
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [isExiting, setIsExiting] = useState(false);

  const handleStepClick = (step: typeof setupSteps[0]) => {
    if (step.action) {
      setCompletedSteps(prev => [...prev, step.id]);
      navigate(step.action);
      onClose();
    }
  };

  const handleSkip = () => {
    setIsExiting(true);
    setTimeout(() => {
      navigate('/dashboard');
      onClose();
    }, 300);
  };

  const handleGoToDashboard = () => {
    setIsExiting(true);
    setTimeout(() => {
      navigate('/dashboard');
      onClose();
    }, 300);
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleSkip()}>
      <DialogContent 
        className={cn(
          "sm:max-w-lg bg-background/95 backdrop-blur-xl border-border/50 transition-all duration-300",
          isExiting && "opacity-0 scale-95"
        )}
        data-testid="recommended-setup-modal"
      >
        <DialogHeader className="text-center pb-2">
          <div className="mx-auto mb-4">
            <div className="relative">
              <div className="absolute inset-0 bg-success/20 rounded-full blur-xl animate-pulse" />
              <div className="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center relative">
                <Check className="h-8 w-8 text-success" />
              </div>
            </div>
          </div>
          <DialogTitle className="text-2xl font-bold">
            Welcome, {userName}! 🎉
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Your account is ready. Complete these recommended steps to secure your vault.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-4">
          {setupSteps.map((step) => {
            const isCompleted = completedSteps.includes(step.id);
            const Icon = step.icon;
            
            return (
              <button
                key={step.id}
                onClick={() => handleStepClick(step)}
                disabled={!step.action || isCompleted}
                className={cn(
                  "w-full flex items-center gap-4 p-4 rounded-xl border transition-all duration-200",
                  "hover:bg-secondary/50 hover:border-primary/30",
                  isCompleted && "bg-success/10 border-success/30",
                  !step.action && "opacity-50 cursor-not-allowed",
                  step.recommended && !isCompleted && "border-[#C5A049]/30 bg-[#C5A049]/5"
                )}
                data-testid={`setup-step-${step.id}`}
              >
                <div className={cn(
                  "w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0",
                  isCompleted ? "bg-success/20" : "bg-primary/10"
                )}>
                  {isCompleted ? (
                    <Check className="h-5 w-5 text-success" />
                  ) : (
                    <Icon className="h-5 w-5 text-primary" />
                  )}
                </div>
                
                <div className="flex-1 text-left">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-sm">{step.title}</h4>
                    {step.recommended && !isCompleted && (
                      <span className="px-2 py-0.5 text-xs rounded-full bg-[#C5A049]/20 text-[#C5A049] font-medium">
                        Recommended
                      </span>
                    )}
                    {!step.action && (
                      <span className="px-2 py-0.5 text-xs rounded-full bg-muted text-muted-foreground font-medium">
                        Coming Soon
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">{step.description}</p>
                </div>
                
                {step.action && !isCompleted && (
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                )}
              </button>
            );
          })}
        </div>

        <div className="flex gap-3 pt-2">
          <Button
            variant="ghost"
            onClick={handleSkip}
            className="flex-1"
            data-testid="skip-setup-btn"
          >
            Skip for now
          </Button>
          <Button
            variant="gradient"
            onClick={handleGoToDashboard}
            className="flex-1 bg-gradient-to-r from-[#C5A049] to-[#8B7355]"
            data-testid="go-to-dashboard-btn"
          >
            Go to Dashboard
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default RecommendedSetup;
