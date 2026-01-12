import { useState, useEffect, useRef, useCallback } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, CheckCircle2, XCircle, Mail, RefreshCw, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';

interface OTPVerificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  email: string;
  onVerify: (code: string) => Promise<boolean>;
  onResend: () => Promise<boolean>;
  onSuccess: () => void;
}

const OTP_LENGTH = 6;
const RESEND_COOLDOWN = 30; // 30 seconds
const CODE_EXPIRY = 300; // 5 minutes in seconds

export function OTPVerificationModal({
  isOpen,
  onClose,
  email,
  onVerify,
  onResend,
  onSuccess
}: OTPVerificationModalProps) {
  const [otp, setOtp] = useState<string[]>(Array(OTP_LENGTH).fill(''));
  const [isVerifying, setIsVerifying] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [verificationStatus, setVerificationStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [resendCooldown, setResendCooldown] = useState(0);
  const [codeExpiry, setCodeExpiry] = useState(CODE_EXPIRY);
  
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setOtp(Array(OTP_LENGTH).fill(''));
      setVerificationStatus('idle');
      setErrorMessage('');
      setCodeExpiry(CODE_EXPIRY);
      setTimeout(() => inputRefs.current[0]?.focus(), 100);
    }
  }, [isOpen]);

  // Resend cooldown timer
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setInterval(() => {
        setResendCooldown(prev => prev - 1);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [resendCooldown]);

  // Code expiry timer
  useEffect(() => {
    if (isOpen && codeExpiry > 0) {
      const timer = setInterval(() => {
        setCodeExpiry(prev => prev - 1);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [isOpen, codeExpiry]);

  // Format time as MM:SS
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle verification
  const handleVerify = useCallback(async (code: string) => {
    if (code.length !== OTP_LENGTH || isVerifying) return;
    
    setIsVerifying(true);
    setErrorMessage('');
    
    try {
      const success = await onVerify(code);
      
      if (success) {
        setVerificationStatus('success');
        // Wait for success animation then redirect
        setTimeout(() => {
          onSuccess();
        }, 1500);
      } else {
        setVerificationStatus('error');
        setErrorMessage('Invalid verification code. Please try again.');
        setOtp(Array(OTP_LENGTH).fill(''));
        setTimeout(() => {
          setVerificationStatus('idle');
          inputRefs.current[0]?.focus();
        }, 2000);
      }
    } catch (error: any) {
      setVerificationStatus('error');
      setErrorMessage(error.message || 'Verification failed. Please try again.');
      setOtp(Array(OTP_LENGTH).fill(''));
      setTimeout(() => {
        setVerificationStatus('idle');
        inputRefs.current[0]?.focus();
      }, 2000);
    } finally {
      setIsVerifying(false);
    }
  }, [onVerify, onSuccess, isVerifying]);

  // Handle input change
  const handleChange = (index: number, value: string) => {
    // Only allow digits
    const digit = value.replace(/\D/g, '').slice(-1);
    
    const newOtp = [...otp];
    newOtp[index] = digit;
    setOtp(newOtp);
    
    // Auto-focus next input
    if (digit && index < OTP_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus();
    }
    
    // Auto-verify when complete
    const fullCode = newOtp.join('');
    if (fullCode.length === OTP_LENGTH) {
      handleVerify(fullCode);
    }
  };

  // Handle paste (auto-paste functionality)
  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, OTP_LENGTH);
    
    if (pastedData.length > 0) {
      const newOtp = Array(OTP_LENGTH).fill('');
      pastedData.split('').forEach((digit, index) => {
        if (index < OTP_LENGTH) newOtp[index] = digit;
      });
      setOtp(newOtp);
      
      // Focus last filled input or trigger verify
      if (pastedData.length === OTP_LENGTH) {
        handleVerify(pastedData);
      } else {
        inputRefs.current[pastedData.length]?.focus();
      }
    }
  };

  // Handle keydown for backspace navigation
  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  // Auto-paste when clicking anywhere in modal
  const handleContainerClick = async () => {
    try {
      const clipboardText = await navigator.clipboard.readText();
      const digits = clipboardText.replace(/\D/g, '').slice(0, OTP_LENGTH);
      
      if (digits.length === OTP_LENGTH && otp.every(d => d === '')) {
        const newOtp = digits.split('');
        setOtp(newOtp);
        handleVerify(digits);
      }
    } catch {
      // Clipboard access denied - focus first input instead
      inputRefs.current[0]?.focus();
    }
  };

  // Handle resend
  const handleResend = async () => {
    if (resendCooldown > 0 || isResending) return;
    
    setIsResending(true);
    try {
      const success = await onResend();
      if (success) {
        setResendCooldown(RESEND_COOLDOWN);
        setCodeExpiry(CODE_EXPIRY);
        setOtp(Array(OTP_LENGTH).fill(''));
        setErrorMessage('');
        setVerificationStatus('idle');
        inputRefs.current[0]?.focus();
      }
    } catch (error) {
      setErrorMessage('Failed to resend code. Please try again.');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && verificationStatus !== 'success' && onClose()}>
      <DialogContent 
        className="sm:max-w-md bg-background/95 backdrop-blur-xl border-border/50"
        onClick={handleContainerClick}
        ref={containerRef}
        data-testid="otp-verification-modal"
      >
        {/* Success Overlay */}
        {verificationStatus === 'success' && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/95 backdrop-blur-sm z-50 rounded-lg animate-fade-in">
            <div className="relative">
              <div className="absolute inset-0 bg-success/20 rounded-full blur-xl animate-pulse" />
              <CheckCircle2 className="h-20 w-20 text-success relative animate-bounce" />
            </div>
            <h3 className="text-xl font-bold text-success mt-4">Verified!</h3>
            <p className="text-muted-foreground text-sm mt-2">Redirecting to setup...</p>
          </div>
        )}

        <DialogHeader className="text-center">
          <div className="mx-auto mb-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#C5A049] to-[#8B7355] flex items-center justify-center">
              <Shield className="h-8 w-8 text-background" />
            </div>
          </div>
          <DialogTitle className="text-2xl font-bold">Verify Your Email</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            We've sent a 6-digit code to<br />
            <span className="text-foreground font-medium">{email}</span>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* OTP Input Fields */}
          <div className="flex justify-center gap-2" data-testid="otp-inputs">
            {otp.map((digit, index) => (
              <Input
                key={index}
                ref={(el) => (inputRefs.current[index] = el)}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                onPaste={handlePaste}
                disabled={isVerifying || verificationStatus === 'success'}
                className={cn(
                  "w-12 h-14 text-center text-2xl font-mono font-bold transition-all duration-200",
                  "border-2 rounded-lg focus:ring-2 focus:ring-[#C5A049]/50",
                  digit && "border-[#C5A049] bg-[#C5A049]/10",
                  verificationStatus === 'error' && "border-destructive bg-destructive/10 animate-shake",
                  verificationStatus === 'success' && "border-success bg-success/10"
                )}
                data-testid={`otp-input-${index}`}
              />
            ))}
          </div>

          {/* Expiry Timer */}
          <div className="text-center">
            {codeExpiry > 0 ? (
              <p className={cn(
                "text-sm",
                codeExpiry <= 60 ? "text-destructive" : "text-muted-foreground"
              )}>
                Code expires in <span className="font-mono font-semibold">{formatTime(codeExpiry)}</span>
              </p>
            ) : (
              <p className="text-sm text-destructive">Code expired. Please request a new one.</p>
            )}
          </div>

          {/* Error Message */}
          {errorMessage && verificationStatus === 'error' && (
            <div className="flex items-center justify-center gap-2 text-destructive text-sm animate-fade-in">
              <XCircle className="h-4 w-4" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Verifying Spinner */}
          {isVerifying && (
            <div className="flex items-center justify-center gap-2 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Verifying...</span>
            </div>
          )}

          {/* Resend Button */}
          <div className="flex flex-col items-center gap-2">
            <p className="text-sm text-muted-foreground">Didn't receive the code?</p>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleResend}
              disabled={resendCooldown > 0 || isResending || verificationStatus === 'success'}
              className="text-[#C5A049] hover:text-[#C5A049]/80 hover:bg-[#C5A049]/10"
              data-testid="resend-code-btn"
            >
              {isResending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Sending...
                </>
              ) : resendCooldown > 0 ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Resend in {resendCooldown}s
                </>
              ) : (
                <>
                  <Mail className="h-4 w-4 mr-2" />
                  Resend Code
                </>
              )}
            </Button>
          </div>

          {/* Tip */}
          <p className="text-xs text-muted-foreground/70 text-center">
            Tip: Paste your code anywhere in this window to auto-fill
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default OTPVerificationModal;
