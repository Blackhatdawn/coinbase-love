# 📦 Package Manager Guidelines

## ⚠️ IMPORTANT: Use Yarn Only

This project **exclusively uses Yarn** as the package manager. **Do NOT use npm**.

### Why Yarn Only?

Mixing package managers (npm and yarn) causes:
- ❌ Unsynchronized lock files (package-lock.json vs yarn.lock)
- ❌ Dependency resolution conflicts
- ❌ Inconsistent dependency versions
- ❌ Build issues
- ❌ CI/CD pipeline failures

### Commands Reference

#### ✅ Correct Commands (Yarn)
```bash
# Install dependencies
cd /app/frontend
yarn install

# Add a new package
yarn add <package-name>

# Add a dev dependency
yarn add -D <package-name>

# Remove a package
yarn remove <package-name>

# Update dependencies
yarn upgrade
```

#### ❌ Incorrect Commands (npm - DO NOT USE)
```bash
npm install     # ❌ DON'T USE
npm i           # ❌ DON'T USE
npm add         # ❌ DON'T USE
```

### Lock File

- **Use:** `yarn.lock` ✅
- **Ignore:** `package-lock.json` ❌ (removed from project)

### Verification

To verify you're using yarn correctly:

```bash
# Check if yarn.lock exists
ls -la /app/frontend/yarn.lock

# Verify no package-lock.json exists
ls -la /app/frontend/package-lock.json  # Should show "No such file"

# Check yarn version
yarn --version  # Should show 1.22.22
```

### In CI/CD

Always use:
```yaml
- run: yarn install --frozen-lockfile
```

Never use:
```yaml
- run: npm install  # ❌ Wrong!
```

---

**Remember:** Consistency is key. Always use **yarn** for this project.
