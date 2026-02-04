#!/bin/bash
# Migrate from npm/yarn to pnpm

set -e

echo "📦 Migrating to pnpm..."
echo ""

cd /app/frontend

# Check if pnpm is installed
if ! command -v pnpm &> /dev/null; then
  echo "⚠️ pnpm not found. Installing..."
  npm install -g pnpm@latest
  echo "✅ pnpm installed"
fi

# Backup package.json
echo "💾 Backing up package.json..."
cp package.json package.json.backup

# Remove old lock files
echo "🗑️ Removing old lock files..."
rm -f package-lock.json yarn.lock

# Create .npmrc for pnpm settings
echo "📝 Creating .npmrc..."
cat > .npmrc << 'EOF'
# pnpm configuration
shamefully-hoist=false
strict-peer-dependencies=false
public-hoist-pattern[]=*eslint*
public-hoist-pattern[]=*prettier*
auto-install-peers=true
EOF

# Add packageManager field to package.json
echo "📝 Updating package.json with packageManager field..."
node -e "
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
pkg.packageManager = 'pnpm@9.0.0';
fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2));
"

# Install dependencies with pnpm
echo "📥 Installing dependencies with pnpm..."
pnpm install

echo ""
echo "✅ Migration to pnpm complete!"
echo ""
echo "📊 Summary:"
echo "  - package-lock.json: Removed"
echo "  - yarn.lock: Removed"
echo "  - pnpm-lock.yaml: Created"
echo "  - .npmrc: Created"
echo "  - Dependencies: Installed with pnpm"
echo ""
echo "🧪 Test commands:"
echo "  pnpm dev       # Start development server"
echo "  pnpm build     # Build for production"
echo "  pnpm lint      # Run linter"
echo ""
echo "🔄 Rollback (if needed):"
echo "  mv package.json.backup package.json"
echo "  npm install  # or yarn install"
echo ""
