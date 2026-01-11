# 🚨 CRITICAL BUGS FOUND - Deep Code Review

## Summary
Found **5 critical/high severity bugs** that will cause runtime failures and memory leaks in production. All require immediate fixes.

---

## 🔴 BUG #1: ReferenceError in API Error Handling [CRITICAL]

**File**: `frontend/src/lib/api.ts` — Line 157  
**Severity**: CRITICAL - App crashes on network errors  
**Status**: UNRESOLVED

### The Problem
```typescript
const isNetworkError = error instanceof TypeError || error instanceof NetworkError;
```

`NetworkError` is **undefined**. When any network error occurs, this line throws a `ReferenceError`, which:
- Masks the original network error
- Breaks the entire retry logic
- Prevents user-friendly error messages
- Causes unhandled promise rejections in browser

### Impact
- All API failures silently fail or crash
- Retry mechanism doesn't work
- Users see blank pages instead of error messages
- Backend spin-down recovery doesn't work

### The Fix
```typescript
// OLD (BROKEN):
const isNetworkError = error instanceof TypeError || error instanceof NetworkError;

// NEW (FIXED):
const isNetworkError = error instanceof TypeError;
```

### Why This Happens
`NetworkError` is an older API that may not be available. `TypeError` is sufficient to catch network errors in modern browsers (TypeError is thrown for "Failed to fetch" errors).

---

## 🔴 BUG #2: useToast Memory Leak [CRITICAL]

**File**: `frontend/src/hooks/use-toast.ts` — Lines 166-177  
**Severity**: CRITICAL - Memory leak, duplicate listeners, excessive re-renders  
**Status**: UNRESOLVED

### The Problem
```typescript
React.useEffect(() => {
  listeners.push(setState);
  return () => {
    const index = listeners.indexOf(setState);
    if (index > -1) {
      listeners.splice(index, 1);
    }
  };
}, [state]);  // ❌ WRONG: depends on [state]
```

**The Issue**: The effect depends on `[state]`, meaning:
1. Every time state changes, the effect re-runs
2. A NEW listener is pushed (duplicate!)
3. The cleanup runs but leaves stale listeners
4. Results in 100+ listeners after a few toasts
5. Every toast update triggers all listeners → cascading renders

### Impact
- Memory leak: listeners never fully cleaned up
- Performance degradation: more toasts = more listeners = slower app
- Possible stack overflow if app runs long enough

### The Fix
```typescript
React.useEffect(() => {
  listeners.push(setState);
  return () => {
    const index = listeners.indexOf(setState);
    if (index > -1) {
      listeners.splice(index, 1);
    }
  };
}, []);  // ✅ CORRECT: empty dependency array
```

**Why**: The listener should be registered once on mount and removed on unmount, not on every state change.

---

## 🔴 BUG #3: Unreasonable Toast Removal Timeout [HIGH]

**File**: `frontend/src/hooks/use-toast.ts` — Line 6  
**Severity**: HIGH - Toasts never disappear, accumulate in memory  
**Status**: UNRESOLVED

### The Problem
```typescript
const TOAST_REMOVE_DELAY = 1000000;
```

This is **1 million milliseconds = 16.67 MINUTES**!

### Impact
- Toasts stay in memory for 16+ minutes
- If user sees 100 toasts, they don't clear for 16+ minutes
- Memory fills up on long-running app sessions
- Users manually can't close toasts that auto-dismiss

### The Fix
```typescript
// Change from:
const TOAST_REMOVE_DELAY = 1000000;

// Change to:
const TOAST_REMOVE_DELAY = 5000;  // 5 seconds (reasonable default)

// Or better yet, make it per-toast:
// const TOAST_REMOVE_DELAY = 5000;  // default
// toast({ description: "...", duration: 3000 })  // override per toast
```

**Standard**: Most toast libraries use 3-5 second default auto-dismiss times.

---

## 🟡 BUG #4: Non-Pure Reducer with Side Effects [HIGH]

**File**: `frontend/src/hooks/use-toast.ts` — Lines 85-93  
**Severity**: HIGH - Race conditions, unpredictable state  
**Status**: UNRESOLVED

### The Problem
```typescript
case "DISMISS_TOAST": {
  const { toastId } = action;

  // ❌ SIDE EFFECTS IN REDUCER!
  if (toastId) {
    addToRemoveQueue(toastId);  // Calls setTimeout + dispatch!
  } else {
    state.toasts.forEach((toast) => {
      addToRemoveQueue(toast.id);  // Multiple side effects!
    });
  }

  return {
    ...state,
    toasts: state.toasts.map((t) =>
      t.id === toastId || toastId === undefined
        ? { ...t, open: false }
        : t,
    ),
  };
}
```

### Why This Is Bad
1. Reducers must be PURE (same input = same output)
2. `addToRemoveQueue` has side effects (setTimeout + dispatch)
3. If the reducer is called twice with same action, it triggers side effects twice
4. Can cause race conditions where toast removal gets scheduled multiple times
5. Hard to debug and reason about timing

### Impact
- Toasts might be removed multiple times
- Race conditions in dismissal logic
- Unpredictable behavior with rapid toast dismissals
- Harder to test and maintain

### The Fix
Refactor the side effect out of the reducer:

```typescript
// In reducer - PURE only:
case "DISMISS_TOAST": {
  const { toastId } = action;
  return {
    ...state,
    toasts: state.toasts.map((t) =>
      t.id === toastId || toastId === undefined
        ? { ...t, open: false }
        : t,
    ),
  };
}

// Outside reducer - side effect handler:
function dismissToast(toastId?: string) {
  dispatch({ type: "DISMISS_TOAST", toastId });
  
  // Schedule removal separately
  if (toastId) {
    addToRemoveQueue(toastId);
  } else {
    memoryState.toasts.forEach((t) => {
      addToRemoveQueue(t.id);
    });
  }
}
```

---

## 🟡 BUG #5: ErrorBoundary Leaks Error Messages to Users [MEDIUM]

**File**: `frontend/src/components/ErrorBoundary.tsx` — Lines 54-58  
**Severity**: MEDIUM - Information disclosure, poor UX  
**Status**: UNRESOLVED

### The Problem
```typescript
{this.state.error && (
  <div className="p-3 bg-secondary/30 rounded-lg">
    <p className="text-xs font-mono text-muted-foreground break-all">
      {this.state.error.message}  {/* ❌ Raw error message */}
    </p>
  </div>
)}
```

### Why This Is Bad
1. **Information Disclosure**: Error messages might contain:
   - Stack traces from backend
   - File paths (reveals app structure)
   - API endpoints
   - Database query details
   - Environment variables names

2. **Poor UX**: Users don't understand cryptic error messages

3. **Security**: In production, exposing technical details is a vulnerability

### Impact
- Could leak sensitive information to users
- Bad user experience
- Fails security audits

### The Fix
```typescript
{this.state.error && (
  <div className="p-3 bg-secondary/30 rounded-lg">
    <p className="text-xs text-muted-foreground mb-2">
      Error details (for debugging):
    </p>
    <p className="text-xs font-mono text-muted-foreground break-all">
      {process.env.NODE_ENV === 'development' 
        ? this.state.error.message 
        : 'An unexpected error occurred. Please try again.'}
    </p>
  </div>
)}
```

Or even better, always show a generic message:
```typescript
<p className="text-xs font-mono text-muted-foreground break-all">
  Error ID: {this.state.error.name}
</p>
```

---

## 📋 Implementation Checklist

- [ ] **Fix #1**: Remove `NetworkError` from api.ts line 157
- [ ] **Fix #2**: Change useEffect dependency to `[]` in use-toast.ts
- [ ] **Fix #3**: Change `TOAST_REMOVE_DELAY` from 1000000 to 5000
- [ ] **Fix #4**: Refactor DISMISS_TOAST logic out of reducer (advanced)
- [ ] **Fix #5**: Hide raw errors in ErrorBoundary for production

---

## Testing After Fixes

### Test #1: Network Error Retry
1. Open DevTools Network tab
2. Throttle network to "Offline"
3. Try to trigger API call (e.g., sign in)
4. Should see "Backend is waking up..." message
5. Should retry 3 times
6. Should show error message, not crash

### Test #2: Toast Behavior
1. Trigger multiple toasts (validation errors, etc)
2. Each toast should disappear after 5 seconds
3. Memory usage should be stable
4. No duplicate toasts

### Test #3: Error Boundary
1. Cause an error in Trade page
2. Should show error boundary UI
3. Message should NOT be raw JavaScript error
4. Should have "Reload Page" button

---

## 🚨 Why These Weren't Caught

1. **NetworkError Bug**: Only manifests on network failures (testing edge case)
2. **Memory Leak**: Only noticeable after heavy use or on low-memory devices
3. **Toast Timeout**: Hidden constant, not obvious at first glance
4. **Reducer Side Effects**: Works but is fragile, harder to catch in testing
5. **Error Messages**: Security issues not caught by linters

---

## Severity Scale

- 🔴 **CRITICAL**: App crashes or fails core functionality
- 🔴 **CRITICAL**: Security vulnerability
- 🟡 **HIGH**: Major performance issue or unpredictable behavior
- 🟠 **MEDIUM**: Affects UX or information disclosure
- 🟢 **LOW**: Code quality or minor optimization

---

## Next Steps

1. Apply all 5 fixes immediately
2. Run manual testing for each bug scenario
3. Consider adding integration tests for:
   - Network error handling
   - Toast lifecycle
   - Error boundary behavior
4. Set up monitoring to catch runtime errors in production
