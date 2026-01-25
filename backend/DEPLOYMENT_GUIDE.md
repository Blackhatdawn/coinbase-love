# Fly.io Deployment Guide for coinbase-love

## Quick Deployment Steps

### Step 1: Set Secrets (run once)
```bash
cd /app/backend
./set-fly-secrets.sh
```

Or manually:
```bash
flyctl secrets set \
  MONGO_URL="mongodb+srv://team_db_user:mWPe3V6ZhoNNEWUk@cryptovaultcluster.vobw2w8.mongodb.net/?appName=CryptoVaultCluster" \
  JWT_SECRET="jmZgXmsOEx10hwWOIE6EvhCft56jew6PVSiSweq-JQI" \
  CSRF_SECRET="9f5cb48d-aa6b-4923-a760-ce8065e4238d" \
  SENDGRID_API_KEY="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" \
  COINCAP_API_KEY="68aa5a01aa84e5704a10f5d6f730dadd9381901161e06d07085fcca8587f41e3" \
  NOWPAYMENTS_API_KEY="ZKDVT1B-4WTMVAZ-KZ7E38G-GPNE8Q7" \
  NOWPAYMENTS_IPN_SECRET="bEEgqlb1q+TF6ygQfNJ+fUJyWvARDJwp" \
  UPSTASH_REDIS_REST_URL="https://emerging-sponge-14455.upstash.io" \
  UPSTASH_REDIS_REST_TOKEN="ATh3AAIncDE5OTMzNjFiM2M4NzA0NmEzOWQwOWE2MjgwODczMDNlM3AxMTQ0NTU" \
  SENTRY_DSN="https://bcb7c3a730f99e6fa758cd3e25edc327@o4510716875505664.ingest.us.sentry.io/4510716879503360" \
  CORS_ORIGINS='["https://www.cryptovault.financial","https://cryptovault.financial","https://coinbase-love.fly.dev"]' \
  --app coinbase-love
```

### Step 2: Deploy
```bash
cd /app/backend
flyctl deploy --app coinbase-love
```

### Step 3: Verify
```bash
# Check status
flyctl status --app coinbase-love

# Check health
curl https://coinbase-love.fly.dev/health

# View logs
flyctl logs --app coinbase-love
```

## Environment Variable Strategy

### Secrets (Fly.io Secrets - encrypted)
| Variable | Description |
|----------|-------------|
| `MONGO_URL` | MongoDB connection string |
| `JWT_SECRET` | JWT signing key |
| `CSRF_SECRET` | CSRF token secret |
| `SENDGRID_API_KEY` | Email service |
| `COINCAP_API_KEY` | Crypto prices API |
| `NOWPAYMENTS_API_KEY` | Payment gateway |
| `NOWPAYMENTS_IPN_SECRET` | Payment IPN verification |
| `UPSTASH_REDIS_REST_URL` | Redis cache URL |
| `UPSTASH_REDIS_REST_TOKEN` | Redis auth token |
| `SENTRY_DSN` | Error tracking |
| `CORS_ORIGINS` | Allowed origins (JSON) |
| `FIREBASE_CREDENTIALS_BASE64` | Firebase service account |

### Non-Secrets (fly.toml [env] - visible)
| Variable | Value |
|----------|-------|
| `ENVIRONMENT` | production |
| `DB_NAME` | cryptovault |
| `PORT` | 8001 |
| `JWT_ALGORITHM` | HS256 |
| `EMAIL_SERVICE` | sendgrid |
| `APP_URL` | https://www.cryptovault.financial |
| `PUBLIC_API_URL` | https://coinbase-love.fly.dev |
| ... | (see fly.toml for full list) |

## URLs After Deployment
- **API**: https://coinbase-love.fly.dev
- **Health**: https://coinbase-love.fly.dev/health
- **Docs**: https://coinbase-love.fly.dev/api/docs
- **Frontend**: https://www.cryptovault.financial (Vercel)
