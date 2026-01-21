/**
 * Social media links configuration
 * These can be overridden via environment variables or runtime configuration
 */

export interface SocialLinks {
  twitter?: string;
  linkedin?: string;
  discord?: string;
  telegram?: string;
}

const DEFAULT_SOCIAL_LINKS: SocialLinks = {
  twitter: 'https://twitter.com/CryptoVaultFin',
  linkedin: 'https://linkedin.com/company/cryptovault-financial',
  discord: 'https://discord.gg/cryptovault',
  telegram: 'https://t.me/cryptovaultfinancial',
};

/**
 * Get social media links - can be customized via environment variables
 * VITE_SOCIAL_TWITTER_URL
 * VITE_SOCIAL_LINKEDIN_URL
 * VITE_SOCIAL_DISCORD_URL
 * VITE_SOCIAL_TELEGRAM_URL
 */
export function getSocialLinks(): SocialLinks {
  return {
    twitter: import.meta.env.VITE_SOCIAL_TWITTER_URL || DEFAULT_SOCIAL_LINKS.twitter,
    linkedin: import.meta.env.VITE_SOCIAL_LINKEDIN_URL || DEFAULT_SOCIAL_LINKS.linkedin,
    discord: import.meta.env.VITE_SOCIAL_DISCORD_URL || DEFAULT_SOCIAL_LINKS.discord,
    telegram: import.meta.env.VITE_SOCIAL_TELEGRAM_URL || DEFAULT_SOCIAL_LINKS.telegram,
  };
}

export default DEFAULT_SOCIAL_LINKS;
