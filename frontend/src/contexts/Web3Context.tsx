import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { ethers, BrowserProvider, JsonRpcSigner } from 'ethers';
import { toast } from 'sonner';

// Supported networks
export const SUPPORTED_NETWORKS = {
  ETHEREUM_MAINNET: {
    chainId: '0x1',
    chainName: 'Ethereum Mainnet',
    nativeCurrency: { name: 'Ether', symbol: 'ETH', decimals: 18 },
    rpcUrls: ['https://mainnet.infura.io/v3/'],
    blockExplorerUrls: ['https://etherscan.io']
  },
  POLYGON_MAINNET: {
    chainId: '0x89',
    chainName: 'Polygon Mainnet',
    nativeCurrency: { name: 'MATIC', symbol: 'MATIC', decimals: 18 },
    rpcUrls: ['https://polygon-rpc.com'],
    blockExplorerUrls: ['https://polygonscan.com']
  },
  ETHEREUM_SEPOLIA: {
    chainId: '0xaa36a7',
    chainName: 'Ethereum Sepolia',
    nativeCurrency: { name: 'SepoliaETH', symbol: 'ETH', decimals: 18 },
    rpcUrls: ['https://sepolia.infura.io/v3/'],
    blockExplorerUrls: ['https://sepolia.etherscan.io']
  }
};

interface Web3ContextType {
  // Connection state
  isConnected: boolean;
  account: string | null;
  balance: string | null;
  chainId: string | null;
  networkName: string | null;
  
  // Provider and signer
  provider: BrowserProvider | null;
  signer: JsonRpcSigner | null;
  
  // Actions
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
  switchNetwork: (chainId: string) => Promise<void>;
  
  // Transaction methods
  sendTransaction: (to: string, amount: string) => Promise<string>;
  getGasPrice: () => Promise<string>;
  estimateGas: (to: string, amount: string) => Promise<string>;
  
  // Loading states
  isConnecting: boolean;
  isSwitchingNetwork: boolean;
}

const Web3Context = createContext<Web3ContextType | undefined>(undefined);

export const Web3Provider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [account, setAccount] = useState<string | null>(null);
  const [balance, setBalance] = useState<string | null>(null);
  const [chainId, setChainId] = useState<string | null>(null);
  const [networkName, setNetworkName] = useState<string | null>(null);
  const [provider, setProvider] = useState<BrowserProvider | null>(null);
  const [signer, setSigner] = useState<JsonRpcSigner | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isSwitchingNetwork, setIsSwitchingNetwork] = useState(false);

  // Get network name from chainId
  const getNetworkName = (chainId: string): string => {
    const networks: { [key: string]: string } = {
      '0x1': 'Ethereum',
      '0x89': 'Polygon',
      '0xaa36a7': 'Sepolia'
    };
    return networks[chainId] || 'Unknown Network';
  };

  // Update balance
  const updateBalance = useCallback(async (address: string, provider: BrowserProvider) => {
    try {
      const balance = await provider.getBalance(address);
      setBalance(ethers.formatEther(balance));
    } catch (error) {
      console.error('Error fetching balance:', error);
    }
  }, []);

  // Connect wallet
  const connectWallet = async () => {
    if (typeof window.ethereum === 'undefined') {
      toast.error('MetaMask not detected', {
        description: 'Please install MetaMask to use wallet features.'
      });
      return;
    }

    try {
      setIsConnecting(true);

      // Request accounts
      const accounts = await window.ethereum.request({
        method: 'eth_requestAccounts'
      });

      if (accounts.length === 0) {
        throw new Error('No accounts found');
      }

      // Create provider and signer
      const web3Provider = new ethers.BrowserProvider(window.ethereum);
      const web3Signer = await web3Provider.getSigner();
      const network = await web3Provider.getNetwork();

      setProvider(web3Provider);
      setSigner(web3Signer);
      setAccount(accounts[0]);
      setChainId(`0x${network.chainId.toString(16)}`);
      setNetworkName(getNetworkName(`0x${network.chainId.toString(16)}`));
      setIsConnected(true);

      // Update balance
      await updateBalance(accounts[0], web3Provider);

      toast.success('Wallet connected!', {
        description: `Connected to ${accounts[0].slice(0, 6)}...${accounts[0].slice(-4)}`
      });

      // Save connection state
      localStorage.setItem('walletConnected', 'true');
      localStorage.setItem('walletAddress', accounts[0]);
    } catch (error: any) {
      console.error('Error connecting wallet:', error);
      toast.error('Failed to connect wallet', {
        description: error.message || 'Please try again.'
      });
    } finally {
      setIsConnecting(false);
    }
  };

  // Disconnect wallet
  const disconnectWallet = () => {
    setIsConnected(false);
    setAccount(null);
    setBalance(null);
    setChainId(null);
    setNetworkName(null);
    setProvider(null);
    setSigner(null);

    localStorage.removeItem('walletConnected');
    localStorage.removeItem('walletAddress');

    toast.info('Wallet disconnected');
  };

  // Switch network
  const switchNetwork = async (targetChainId: string) => {
    if (!window.ethereum) {
      toast.error('MetaMask not detected');
      return;
    }

    try {
      setIsSwitchingNetwork(true);

      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: targetChainId }]
      });

      toast.success('Network switched successfully');
    } catch (error: any) {
      // If network not added, try to add it
      if (error.code === 4902) {
        try {
          const networkConfig = Object.values(SUPPORTED_NETWORKS).find(
            n => n.chainId === targetChainId
          );

          if (networkConfig) {
            await window.ethereum.request({
              method: 'wallet_addEthereumChain',
              params: [networkConfig]
            });
            toast.success('Network added and switched');
          }
        } catch (addError: any) {
          toast.error('Failed to add network', {
            description: addError.message
          });
        }
      } else {
        toast.error('Failed to switch network', {
          description: error.message
        });
      }
    } finally {
      setIsSwitchingNetwork(false);
    }
  };

  // Send transaction
  const sendTransaction = async (to: string, amount: string): Promise<string> => {
    if (!signer) {
      throw new Error('Wallet not connected');
    }

    try {
      const tx = await signer.sendTransaction({
        to,
        value: ethers.parseEther(amount)
      });

      toast.info('Transaction submitted', {
        description: `Hash: ${tx.hash.slice(0, 10)}...`
      });

      const receipt = await tx.wait();

      if (receipt?.status === 1) {
        toast.success('Transaction confirmed!');
        // Update balance after transaction
        if (account && provider) {
          await updateBalance(account, provider);
        }
      }

      return tx.hash;
    } catch (error: any) {
      toast.error('Transaction failed', {
        description: error.message
      });
      throw error;
    }
  };

  // Get current gas price
  const getGasPrice = async (): Promise<string> => {
    if (!provider) {
      throw new Error('Provider not available');
    }

    try {
      const feeData = await provider.getFeeData();
      if (feeData.gasPrice) {
        return ethers.formatUnits(feeData.gasPrice, 'gwei');
      }
      return '0';
    } catch (error) {
      console.error('Error fetching gas price:', error);
      return '0';
    }
  };

  // Estimate gas for transaction
  const estimateGas = async (to: string, amount: string): Promise<string> => {
    if (!provider || !account) {
      throw new Error('Wallet not connected');
    }

    try {
      const gasEstimate = await provider.estimateGas({
        from: account,
        to,
        value: ethers.parseEther(amount)
      });

      return gasEstimate.toString();
    } catch (error) {
      console.error('Error estimating gas:', error);
      return '21000'; // Default gas limit for ETH transfer
    }
  };

  // Auto-connect on mount if previously connected
  useEffect(() => {
    const wasConnected = localStorage.getItem('walletConnected');
    if (wasConnected === 'true' && window.ethereum) {
      connectWallet();
    }
  }, []);

  // Listen to account changes
  useEffect(() => {
    if (!window.ethereum) return;

    const handleAccountsChanged = (accounts: string[]) => {
      if (accounts.length === 0) {
        disconnectWallet();
      } else if (accounts[0] !== account) {
        setAccount(accounts[0]);
        if (provider) {
          updateBalance(accounts[0], provider);
        }
        toast.info('Account changed', {
          description: `${accounts[0].slice(0, 6)}...${accounts[0].slice(-4)}`
        });
      }
    };

    const handleChainChanged = (chainId: string) => {
      setChainId(chainId);
      setNetworkName(getNetworkName(chainId));
      toast.info('Network changed', {
        description: getNetworkName(chainId)
      });
      // Reload to reset state
      window.location.reload();
    };

    window.ethereum.on('accountsChanged', handleAccountsChanged);
    window.ethereum.on('chainChanged', handleChainChanged);

    return () => {
      window.ethereum?.removeListener('accountsChanged', handleAccountsChanged);
      window.ethereum?.removeListener('chainChanged', handleChainChanged);
    };
  }, [account, provider, updateBalance]);

  const value: Web3ContextType = {
    isConnected,
    account,
    balance,
    chainId,
    networkName,
    provider,
    signer,
    connectWallet,
    disconnectWallet,
    switchNetwork,
    sendTransaction,
    getGasPrice,
    estimateGas,
    isConnecting,
    isSwitchingNetwork
  };

  return <Web3Context.Provider value={value}>{children}</Web3Context.Provider>;
};

export const useWeb3 = () => {
  const context = useContext(Web3Context);
  if (context === undefined) {
    throw new Error('useWeb3 must be used within a Web3Provider');
  }
  return context;
};

// Type declaration for window.ethereum
declare global {
  interface Window {
    ethereum?: any;
  }
}
