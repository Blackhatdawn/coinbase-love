import React from 'react';
import { useWeb3, SUPPORTED_NETWORKS } from '@/contexts/Web3Context';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Wallet, LogOut, Network, Copy, ExternalLink, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export const WalletConnect: React.FC = () => {
  const {
    isConnected,
    account,
    balance,
    networkName,
    chainId,
    connectWallet,
    disconnectWallet,
    switchNetwork,
    isConnecting,
    isSwitchingNetwork
  } = useWeb3();

  const copyAddress = () => {
    if (account) {
      navigator.clipboard.writeText(account);
      toast.success('Address copied to clipboard');
    }
  };

  const viewOnExplorer = () => {
    if (!account || !chainId) return;

    const explorers: { [key: string]: string } = {
      '0x1': `https://etherscan.io/address/${account}`,
      '0x89': `https://polygonscan.com/address/${account}`,
      '0xaa36a7': `https://sepolia.etherscan.io/address/${account}`
    };

    const explorerUrl = explorers[chainId];
    if (explorerUrl) {
      window.open(explorerUrl, '_blank');
    }
  };

  if (!isConnected) {
    return (
      <Button
        onClick={connectWallet}
        disabled={isConnecting}
        className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
      >
        {isConnecting ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Connecting...
          </>
        ) : (
          <>
            <Wallet className="mr-2 h-4 w-4" />
            Connect Wallet
          </>
        )}
      </Button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="relative">
          <Wallet className="mr-2 h-4 w-4" />
          <span className="hidden sm:inline">
            {account?.slice(0, 6)}...{account?.slice(-4)}
          </span>
          <span className="sm:hidden">Wallet</span>
          {networkName && (
            <span className="ml-2 text-xs text-muted-foreground hidden md:inline">
              ({networkName})
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel>Wallet Info</DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        <div className="px-2 py-2 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Address</span>
            <div className="flex items-center gap-1">
              <span className="text-sm font-mono">
                {account?.slice(0, 6)}...{account?.slice(-4)}
              </span>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={copyAddress}
              >
                <Copy className="h-3 w-3" />
              </Button>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Balance</span>
            <span className="text-sm font-semibold">
              {balance ? `${parseFloat(balance).toFixed(4)} ${networkName === 'Polygon' ? 'MATIC' : 'ETH'}` : '0.0000'}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Network</span>
            <span className="text-sm font-medium">{networkName}</span>
          </div>
        </div>

        <DropdownMenuSeparator />
        
        <DropdownMenuLabel className="flex items-center gap-2">
          <Network className="h-4 w-4" />
          Switch Network
        </DropdownMenuLabel>
        
        {Object.entries(SUPPORTED_NETWORKS).map(([key, network]) => (
          <DropdownMenuItem
            key={key}
            onClick={() => switchNetwork(network.chainId)}
            disabled={isSwitchingNetwork || chainId === network.chainId}
            className="cursor-pointer"
          >
            <span className={chainId === network.chainId ? 'font-bold' : ''}>
              {network.chainName}
            </span>
            {chainId === network.chainId && (
              <span className="ml-2 text-xs text-green-600">● Active</span>
            )}
          </DropdownMenuItem>
        ))}

        <DropdownMenuSeparator />
        
        <DropdownMenuItem onClick={viewOnExplorer} className="cursor-pointer">
          <ExternalLink className="mr-2 h-4 w-4" />
          View on Explorer
        </DropdownMenuItem>

        <DropdownMenuItem onClick={disconnectWallet} className="cursor-pointer text-red-600">
          <LogOut className="mr-2 h-4 w-4" />
          Disconnect
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
