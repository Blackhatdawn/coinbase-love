/**
 * Runtime configuration loader.
 * Fetches public config from backend /api/config.
 */

export interface RuntimeConfig {
  appUrl: string;
  apiBaseUrl: string;
  wsBaseUrl: string;
  socketIoPath: string;
  environment: string;
  version: string;
  preferRelativeApi?: boolean;
  sentry?: {
    dsn?: string;
    enabled?: boolean;
    environment?: string;
  };
  branding?: {
    siteName?: string;
    logoUrl?: string;
    supportEmail?: string;
  };
}

const DEFAULT_SOCKET_PATH = '/socket.io/';
const CONFIG_ENDPOINT = '/api/config';

let runtimeConfig: RuntimeConfig | null = null;

const sanitizeBaseUrl = (value: string): string => {
  if (!value) {
    return '';
  }

  const [first] = value.split(',');
  return first.trim().replace(/%20/g, '');
};

const normalizeBaseUrl = (value: string): string => {
  const sanitized = sanitizeBaseUrl(value);
  return sanitized.replace(/\/+$/, '');
};

const deriveWsBaseUrl = (baseUrl: string): string => {
  if (!baseUrl) {
    return '';
  }
  if (baseUrl.startsWith('https://')) {
    return `wss://${baseUrl.slice('https://'.length)}`;
  }
  if (baseUrl.startsWith('http://')) {
    return `ws://${baseUrl.slice('http://'.length)}`;
  }
  return baseUrl;
};

const getFallbackAppUrl = (): string => {
  if (typeof window !== 'undefined') {
    return normalizeBaseUrl(window.location.origin);
  }
  return '';
};

const getFallbackApiBaseUrl = (): string => normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL || '');

const getFallbackConfig = (): RuntimeConfig => ({
  appUrl: getFallbackAppUrl(),
  apiBaseUrl: getFallbackApiBaseUrl(),
  wsBaseUrl: '',
  socketIoPath: DEFAULT_SOCKET_PATH,
  environment: import.meta.env.MODE || 'development',
  version: import.meta.env.VITE_APP_VERSION || '1.0.0',
  preferRelativeApi: false,
  sentry: {
    dsn: import.meta.env.VITE_SENTRY_DSN || '',
    enabled: import.meta.env.VITE_ENABLE_SENTRY === 'true',
    environment: import.meta.env.MODE,
  },
});

const mergeConfig = (base: RuntimeConfig, incoming: Partial<RuntimeConfig>): RuntimeConfig => {
  const preferRelativeApi = incoming.preferRelativeApi ?? base.preferRelativeApi ?? false;
  const merged: RuntimeConfig = {
    ...base,
    ...incoming,
    preferRelativeApi,
    sentry: { ...base.sentry, ...incoming.sentry },
    branding: { ...base.branding, ...incoming.branding },
  };

  merged.appUrl = normalizeBaseUrl(merged.appUrl || base.appUrl);
  merged.apiBaseUrl = preferRelativeApi
    ? ''
    : normalizeBaseUrl(merged.apiBaseUrl || base.apiBaseUrl);
  merged.socketIoPath = merged.socketIoPath || DEFAULT_SOCKET_PATH;
  merged.wsBaseUrl = normalizeBaseUrl(
    merged.wsBaseUrl || deriveWsBaseUrl(merged.apiBaseUrl || base.apiBaseUrl || merged.appUrl)
  );

  return merged;
};

const buildConfigUrl = (): string => {
  const baseUrl = getFallbackApiBaseUrl();
  return `${baseUrl}${CONFIG_ENDPOINT}`;
};

export async function loadRuntimeConfig(): Promise<RuntimeConfig> {
  if (runtimeConfig) {
    return runtimeConfig;
  }

  const fallback = getFallbackConfig();

  try {
    const response = await fetch(buildConfigUrl(), {
      method: 'GET',
      headers: { Accept: 'application/json' },
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`Config request failed (${response.status})`);
    }

    const data = (await response.json()) as Partial<RuntimeConfig>;
    runtimeConfig = mergeConfig(fallback, data);
    return runtimeConfig;
  } catch (error) {
    runtimeConfig = mergeConfig(fallback, {});
    return runtimeConfig;
  }
}

export function getRuntimeConfig(): RuntimeConfig | null {
  return runtimeConfig;
}

export function resolveApiBaseUrl(): string {
  if (runtimeConfig?.preferRelativeApi) {
    return '';
  }
  if (runtimeConfig?.apiBaseUrl) {
    return runtimeConfig.apiBaseUrl;
  }
  return getFallbackApiBaseUrl();
}

export function resolveAppUrl(): string {
  if (runtimeConfig?.appUrl) {
    return runtimeConfig.appUrl;
  }
  return getFallbackAppUrl();
}

export function resolveWsBaseUrl(): string {
  if (runtimeConfig?.wsBaseUrl) {
    return runtimeConfig.wsBaseUrl;
  }

  const apiBase = resolveApiBaseUrl();
  if (apiBase) {
    return deriveWsBaseUrl(apiBase);
  }

  return deriveWsBaseUrl(getFallbackAppUrl());
}

export function resolveSocketIoPath(): string {
  return runtimeConfig?.socketIoPath || DEFAULT_SOCKET_PATH;
}

export function resolveSentryConfig(): RuntimeConfig['sentry'] {
  return runtimeConfig?.sentry || getFallbackConfig().sentry;
}

export function resolveSupportEmail(): string {
  return runtimeConfig?.branding?.supportEmail || 'support@example.com';
}
