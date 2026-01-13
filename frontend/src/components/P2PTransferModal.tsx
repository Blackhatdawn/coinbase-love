import { useState, useEffect, useCallback } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Send, Search, Loader2, CheckCircle2, AlertCircle, 
  User, DollarSign, MessageSquare, ArrowRight 
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { api } from '@/lib/apiClient';
import { useToast } from '@/hooks/use-toast';

interface P2PTransferModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentBalance: number;
  onTransferComplete?: () => void;
}

interface UserSearchResult {
  id: string;
  name: string;
  email: string;
}

type TransferStep = 'recipient' | 'amount' | 'confirm' | 'success';

export function P2PTransferModal({
  isOpen,
  onClose,
  currentBalance,
  onTransferComplete
}: P2PTransferModalProps) {
  const [step, setStep] = useState<TransferStep>('recipient');
  const [recipientEmail, setRecipientEmail] = useState('');
  const [selectedRecipient, setSelectedRecipient] = useState<UserSearchResult | null>(null);
  const [searchResults, setSearchResults] = useState<UserSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');
  const [isTransferring, setIsTransferring] = useState(false);
  const [transferResult, setTransferResult] = useState<any>(null);
  const { toast } = useToast();

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setStep('recipient');
      setRecipientEmail('');
      setSelectedRecipient(null);
      setSearchResults([]);
      setAmount('');
      setNote('');
      setTransferResult(null);
    }
  }, [isOpen]);

  // Debounced user search
  const searchUsers = useCallback(async (email: string) => {
    if (email.length < 3) {
      setSearchResults([]);
      return;
    }
    
    setIsSearching(true);
    try {
      const response = await api.users.search(email);
      setSearchResults(response.users || []);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  // Handle email input change with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (recipientEmail) {
        searchUsers(recipientEmail);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [recipientEmail, searchUsers]);

  const handleSelectRecipient = (user: UserSearchResult) => {
    setSelectedRecipient(user);
    setRecipientEmail(user.email);
    setSearchResults([]);
    setStep('amount');
  };

  const handleAmountSubmit = () => {
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      toast({
        title: "Invalid amount",
        description: "Please enter a valid amount greater than 0",
        variant: "destructive"
      });
      return;
    }
    if (numAmount > currentBalance) {
      toast({
        title: "Insufficient balance",
        description: `Your available balance is $${currentBalance.toFixed(2)}`,
        variant: "destructive"
      });
      return;
    }
    setStep('confirm');
  };

  const handleTransfer = async () => {
    if (!selectedRecipient) return;
    
    setIsTransferring(true);
    try {
      const result = await api.transfers.p2p({
        recipient_email: selectedRecipient.email,
        amount: parseFloat(amount),
        currency: 'USD',
        note: note || undefined
      });
      
      setTransferResult(result.transfer);
      setStep('success');
      toast({
        title: "Transfer successful!",
        description: `$${amount} sent to ${selectedRecipient.name}`,
      });
      onTransferComplete?.();
    } catch (error: any) {
      toast({
        title: "Transfer failed",
        description: error.message || "Unable to complete transfer",
        variant: "destructive"
      });
    } finally {
      setIsTransferring(false);
    }
  };

  const renderStep = () => {
    switch (step) {
      case 'recipient':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="recipient">Recipient Email</Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="recipient"
                  type="email"
                  placeholder="Search by email..."
                  value={recipientEmail}
                  onChange={(e) => setRecipientEmail(e.target.value)}
                  className="pl-10"
                  data-testid="recipient-email-input"
                />
                {isSearching && (
                  <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
                )}
              </div>
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="border rounded-lg divide-y divide-border bg-secondary/20">
                {searchResults.map((user) => (
                  <button
                    key={user.id}
                    onClick={() => handleSelectRecipient(user)}
                    className="w-full flex items-center gap-3 p-3 hover:bg-secondary/50 transition-colors text-left"
                    data-testid={`user-result-${user.id}`}
                  >
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                      <User className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-medium text-sm">{user.name}</p>
                      <p className="text-xs text-muted-foreground">{user.email}</p>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {recipientEmail.length >= 3 && searchResults.length === 0 && !isSearching && (
              <p className="text-sm text-muted-foreground text-center py-4">
                No CryptoVault users found with that email
              </p>
            )}
          </div>
        );

      case 'amount':
        return (
          <div className="space-y-4">
            {/* Selected Recipient */}
            {selectedRecipient && (
              <div className="flex items-center gap-3 p-3 rounded-lg bg-secondary/30 border border-border/50">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <User className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-sm">{selectedRecipient.name}</p>
                  <p className="text-xs text-muted-foreground">{selectedRecipient.email}</p>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => setStep('recipient')}
                  className="text-xs"
                >
                  Change
                </Button>
              </div>
            )}

            {/* Amount Input */}
            <div className="space-y-2">
              <Label htmlFor="amount">Amount (USD)</Label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="amount"
                  type="number"
                  placeholder="0.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="pl-10 text-xl font-mono"
                  min="0"
                  step="0.01"
                  data-testid="transfer-amount-input"
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Available balance: <span className="text-foreground font-medium">${currentBalance.toFixed(2)}</span>
              </p>
            </div>

            {/* Quick Amount Buttons */}
            <div className="flex gap-2">
              {[10, 25, 50, 100].map((quickAmount) => (
                <Button
                  key={quickAmount}
                  variant="outline"
                  size="sm"
                  onClick={() => setAmount(quickAmount.toString())}
                  disabled={quickAmount > currentBalance}
                  className="flex-1"
                >
                  ${quickAmount}
                </Button>
              ))}
            </div>

            {/* Note */}
            <div className="space-y-2">
              <Label htmlFor="note">Note (optional)</Label>
              <div className="relative">
                <MessageSquare className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Textarea
                  id="note"
                  placeholder="Add a message..."
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  className="pl-10 min-h-[80px]"
                  maxLength={200}
                  data-testid="transfer-note-input"
                />
              </div>
            </div>

            <Button 
              onClick={handleAmountSubmit} 
              className="w-full"
              disabled={!amount || parseFloat(amount) <= 0}
              data-testid="continue-to-confirm-btn"
            >
              Continue
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        );

      case 'confirm':
        return (
          <div className="space-y-6">
            <div className="text-center py-4">
              <p className="text-4xl font-bold text-[#C5A049]">${parseFloat(amount).toFixed(2)}</p>
              <p className="text-sm text-muted-foreground mt-2">USD</p>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b border-border/50">
                <span className="text-sm text-muted-foreground">To</span>
                <span className="text-sm font-medium">{selectedRecipient?.name}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-border/50">
                <span className="text-sm text-muted-foreground">Email</span>
                <span className="text-sm">{selectedRecipient?.email}</span>
              </div>
              {note && (
                <div className="flex justify-between items-start py-2 border-b border-border/50">
                  <span className="text-sm text-muted-foreground">Note</span>
                  <span className="text-sm text-right max-w-[200px]">{note}</span>
                </div>
              )}
              <div className="flex justify-between items-center py-2">
                <span className="text-sm text-muted-foreground">Fee</span>
                <span className="text-sm text-success">Free</span>
              </div>
            </div>

            <div className="flex gap-3">
              <Button 
                variant="outline" 
                onClick={() => setStep('amount')}
                className="flex-1"
                disabled={isTransferring}
              >
                Back
              </Button>
              <Button 
                onClick={handleTransfer}
                className="flex-1 bg-gradient-to-r from-[#C5A049] to-[#8B7355]"
                disabled={isTransferring}
                data-testid="confirm-transfer-btn"
              >
                {isTransferring ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Send Now
                  </>
                )}
              </Button>
            </div>
          </div>
        );

      case 'success':
        return (
          <div className="text-center py-8 space-y-6">
            <div className="relative mx-auto w-fit">
              <div className="absolute inset-0 bg-success/20 rounded-full blur-xl animate-pulse" />
              <CheckCircle2 className="h-20 w-20 text-success relative" />
            </div>
            
            <div>
              <h3 className="text-xl font-bold text-success">Transfer Complete!</h3>
              <p className="text-muted-foreground mt-2">
                ${parseFloat(amount).toFixed(2)} sent to {selectedRecipient?.name}
              </p>
            </div>

            {transferResult && (
              <div className="text-xs text-muted-foreground">
                Transaction ID: {transferResult.id?.slice(0, 8)}...
              </div>
            )}

            <Button onClick={onClose} className="w-full" data-testid="close-success-btn">
              Done
            </Button>
          </div>
        );
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && step !== 'success' && onClose()}>
      <DialogContent 
        className="sm:max-w-md bg-background/95 backdrop-blur-xl border-border/50"
        data-testid="p2p-transfer-modal"
      >
        {step !== 'success' && (
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Send className="h-5 w-5 text-[#C5A049]" />
              Send Funds
            </DialogTitle>
            <DialogDescription>
              {step === 'recipient' && "Send funds instantly to any CryptoVault user"}
              {step === 'amount' && "Enter the amount you want to send"}
              {step === 'confirm' && "Review and confirm your transfer"}
            </DialogDescription>
          </DialogHeader>
        )}

        <div className="py-4">
          {renderStep()}
        </div>

        {/* Step Indicators */}
        {step !== 'success' && (
          <div className="flex justify-center gap-2 pt-2">
            {['recipient', 'amount', 'confirm'].map((s, i) => (
              <div
                key={s}
                className={cn(
                  "w-2 h-2 rounded-full transition-all",
                  step === s ? "bg-[#C5A049] w-6" : 
                  ['recipient', 'amount', 'confirm'].indexOf(step) > i ? "bg-[#C5A049]" : "bg-border"
                )}
              />
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default P2PTransferModal;
