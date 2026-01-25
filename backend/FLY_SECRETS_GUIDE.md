# Fly.io Secrets Setup Guide for CryptoVault

## Quick Setup

Run this single command to set all required secrets:

```bash
flyctl secrets set \
  MONGO_URL="mongodb+srv://team_db_user:YOUR_PASSWORD@cryptovaultcluster.vobw2w8.mongodb.net/?appName=CryptoVaultCluster" \
  JWT_SECRET="YOUR_JWT_SECRET_64_CHARS_MIN" \
  CSRF_SECRET="YOUR_CSRF_SECRET_64_CHARS_MIN" \
  SENDGRID_API_KEY="SG.YOUR_SENDGRID_KEY" \
  UPSTASH_REDIS_REST_URL="https://YOUR_REDIS.upstash.io" \
  UPSTASH_REDIS_REST_TOKEN="YOUR_UPSTASH_TOKEN" \
  COINCAP_API_KEY="YOUR_COINCAP_KEY" \
  NOWPAYMENTS_API_KEY="YOUR_NOWPAYMENTS_KEY" \
  NOWPAYMENTS_IPN_SECRET="YOUR_IPN_SECRET" \
  SENTRY_DSN="https://YOUR_SENTRY_DSN@sentry.io/PROJECT_ID"
```

## Individual Secret Commands

### Database
```bash
flyctl secrets set MONGO_URL="mongodb+srv://..."
```

### Authentication
```bash
# Generate strong secrets:
# python3 -c "import secrets; print(secrets.token_urlsafe(64))"
flyctl secrets set JWT_SECRET="your-64-char-secret"
flyctl secrets set CSRF_SECRET="your-64-char-secret"
```

### Email (SendGrid)
```bash
flyctl secrets set SENDGRID_API_KEY="SG.xxxx"
```

### Cache (Upstash Redis)
```bash
flyctl secrets set UPSTASH_REDIS_REST_URL="https://xxx.upstash.io"
flyctl secrets set UPSTASH_REDIS_REST_TOKEN="xxxx"
```

### External APIs
```bash
flyctl secrets set COINCAP_API_KEY="xxxx"
flyctl secrets set NOWPAYMENTS_API_KEY="xxxx"
flyctl secrets set NOWPAYMENTS_IPN_SECRET="xxxx"
```

### Monitoring
```bash
flyctl secrets set SENTRY_DSN="https://xxx@sentry.io/xxx"
```

## Verify Secrets

```bash
# List all secrets (values hidden)
flyctl secrets list

# Check specific secret exists
flyctl secrets list | grep JWT_SECRET
```

## Update a Secret

```bash
# Secrets are updated with the same set command
flyctl secrets set JWT_SECRET="new-secret-value"
```

## Remove a Secret

```bash
flyctl secrets unset SECRET_NAME
```

## Security Best Practices

1. **Never commit secrets to git**
2. **Use strong, random values** for JWT_SECRET and CSRF_SECRET
3. **Rotate secrets periodically** (especially JWT_SECRET)
4. **Use separate secrets for staging vs production**
5. **Monitor for exposed secrets** using tools like GitGuardian

## Generate Strong Secrets

Python one-liner:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

OpenSSL:
```bash
openssl rand -base64 48
```

## Troubleshooting

### Secret not taking effect
```bash
# Restart the app after setting secrets
flyctl apps restart cryptovault-api
```

### Check if secret is set correctly
```bash
# SSH into the container and check env
flyctl ssh console -a cryptovault-api
env | grep YOUR_SECRET_NAME
```

### View deployment logs
```bash
flyctl logs -a cryptovault-api
```
