import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import { Copy, Download, Check } from "lucide-react";

interface TwoFactorSetupProps {
  onComplete: () => void;
}

const TwoFactorSetup = ({ onComplete }: TwoFactorSetupProps) => {
  const { toast } = useToast();
  const [step, setStep] = useState<"request" | "verify" | "backup" | "complete">("request");
  const [qrCode, setQrCode] = useState<string>("");
  const [secret, setSecret] = useState<string>("");
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [verificationCode, setVerificationCode] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Step 1: Request 2FA setup
  const handleRequestSetup = async () => {
    setIsLoading(true);
    try {
      const response = await api.auth.setup2FA();
      setQrCode(response.qrCode);
      setSecret(response.secret);
      setBackupCodes(response.backupCodes);
      setStep("verify");
      toast({
        title: "QR Code Ready",
        description: "Scan the QR code with your authenticator app",
      });
    } catch (error: any) {
      toast({
        title: "Setup Failed",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Step 2: Verify TOTP code
  const handleVerifyCode = async () => {
    if (!verificationCode || verificationCode.length !== 6) {
      toast({
        title: "Invalid Code",
        description: "Please enter a 6-digit code",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await api.auth.verify2FA(verificationCode);
      setBackupCodes(response.backupCodes);
      setStep("backup");
      toast({
        title: "Code Verified!",
        description: "2FA setup is almost complete",
      });
    } catch (error: any) {
      toast({
        title: "Verification Failed",
        description: error.message || "Invalid code. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Copy secret to clipboard
  const copySecret = () => {
    navigator.clipboard.writeText(secret);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Download backup codes
  const downloadBackupCodes = () => {
    const content = backupCodes.join("\n");
    const element = document.createElement("a");
    element.setAttribute("href", `data:text/plain;charset=utf-8,${encodeURIComponent(content)}`);
    element.setAttribute("download", "backup-codes.txt");
    element.style.display = "none";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    toast({
      title: "Downloaded",
      description: "Backup codes saved",
    });
  };

  if (step === "request") {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-2">Enable Two-Factor Authentication</h3>
          <p className="text-muted-foreground">
            Add an extra layer of security to your account with two-factor authentication.
          </p>
        </div>
        <Button onClick={handleRequestSetup} disabled={isLoading} className="w-full">
          {isLoading ? "Setting up..." : "Start Setup"}
        </Button>
      </div>
    );
  }

  if (step === "verify") {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-4">Scan QR Code</h3>

          {qrCode && (
            <div className="flex justify-center mb-6">
              <img src={qrCode} alt="2FA QR Code" className="w-64 h-64 border rounded" />
            </div>
          )}

          <div className="bg-muted p-4 rounded mb-4">
            <p className="text-sm text-muted-foreground mb-2">
              Can't scan? Enter this code manually:
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 text-sm font-mono p-2 bg-background rounded">
                {secret}
              </code>
              <Button
                size="sm"
                variant="outline"
                onClick={copySecret}
              >
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="verify-code">Enter 6-digit code from authenticator</Label>
          <Input
            id="verify-code"
            type="text"
            placeholder="000000"
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value.slice(0, 6))}
            className="text-center text-2xl tracking-widest"
            maxLength={6}
          />
        </div>

        <Button onClick={handleVerifyCode} disabled={isLoading} className="w-full">
          {isLoading ? "Verifying..." : "Verify Code"}
        </Button>
      </div>
    );
  }

  if (step === "backup") {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-2">Save Backup Codes</h3>
          <p className="text-muted-foreground mb-4">
            Save these codes in a safe place. You can use them to recover your account if you lose your authenticator.
          </p>

          <div className="bg-muted p-4 rounded space-y-2 font-mono text-sm mb-4">
            {backupCodes.map((code) => (
              <div key={code} className="text-muted-foreground">
                {code}
              </div>
            ))}
          </div>

          <Button onClick={downloadBackupCodes} variant="outline" className="w-full mb-4">
            <Download className="h-4 w-4 mr-2" />
            Download Codes
          </Button>
        </div>

        <Button onClick={() => setStep("complete")} className="w-full">
          Done
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center mx-auto">
          <Check className="h-6 w-6 text-green-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">2FA Enabled!</h3>
          <p className="text-muted-foreground text-sm">
            Your account is now protected with two-factor authentication.
          </p>
        </div>
      </div>

      <Button onClick={onComplete} className="w-full">
        Continue
      </Button>
    </div>
  );
};

export default TwoFactorSetup;
