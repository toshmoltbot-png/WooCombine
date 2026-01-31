# Post-Deployment Verification: Combine Lock UI Sync

**Commit:** `cf33dd5`  
**Deployed:** [Date/Time - to be updated after Render deployment completes]

---

## Deployment Status

### Backend (Render)
- [ ] Build triggered: https://dashboard.render.com/
- [ ] Build completed successfully
- [ ] Service restarted
- [ ] Health check passing

### Frontend (Render/Netlify)
- [ ] Build triggered
- [ ] Build completed successfully
- [ ] New build SHA visible (no longer `fb44ad5`)
- [ ] Cache cleared/invalidated

---

## Verification Steps

### 1. Verify Backend Deployment

**Check Render Logs:**
```bash
# Look for deployment confirmation
[STARTUP] messages should show new version
```

**Test Lock Endpoint Directly:**
```bash
# Get auth token from browser console
# localStorage.getItem('firebaseAuthToken')

# Test PATCH endpoint
curl -X PATCH \
  'https://woo-combine-backend.onrender.com/api/leagues/cghm3aU9sTrRSYsM1Zt7/events/NEC2LqYW0MPS6pzHv95n/lock' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"isLocked": true, "reason": "Test"}'
```

**Expected Response:**
```json
{
  "isLocked": true,
  "message": "Combine locked successfully",
  "changed": true,
  "lock_updated_at": "2026-01-11T...",
  "verified": true  // ← NEW FIELD
}
```

**Check Backend Logs for:**
```
[LOCK] Lock toggle request - Event: NEC2LqYW0MPS6pzHv95n, Current: false, Requested: true
[LOCK] Updating league subcollection: /leagues/cghm3aU9sTrRSYsM1Zt7/events/...
[LOCK] Updating global collection: /events/NEC2LqYW0MPS6pzHv95n
[LOCK] Verification successful - Event NEC2LqYW0MPS6pzHv95n isLocked=True
[AUDIT] Combine LOCKED - Event: NEC2LqYW0MPS6pzHv95n
```

---

### 2. Verify Frontend Deployment

**Check Build SHA:**
1. Open DevTools → Console
2. Look for build info or check Network tab headers
3. Confirm build SHA is **NOT** `fb44ad5`

**Check for New Code:**
```javascript
// Open browser console, check if cache invalidation is present
// Should see this log when clicking Lock/Unlock:
"[EVENT-CONTEXT] Invalidated events cache for league cghm3aU9sTrRSYsM1Zt7"
```

---

### 3. End-to-End Lock Test

**Test Lock Flow:**
1. Login as organizer: https://woo-combine.com/
2. Navigate to Admin Tools → Event Setup
3. Scroll to "Combine Lock Control"
4. **Verify initial state:**
   - Shows "🔓 Combine Results Unlocked"
   - Shows "Lock Combine Results" button (red)

5. Click "Lock Combine Results"
6. In confirmation modal, enter reason: "Post-deployment test"
7. Click "Yes, Lock Combine"

**Expected Browser Console Output:**
```
[LOCK] Sending lock toggle request: {eventId: "...", currentState: false, newState: true}
[LOCK] Backend response: {isLocked: true, changed: true, verified: true}
[LOCK] Calling refreshEvents() to sync UI...
[EVENT-CONTEXT] Invalidated events cache for league cghm3aU9sTrRSYsM1Zt7  // ← NEW
[EVENT-CONTEXT] Synced selectedEvent after refresh: NEC2LqYW0MPS6pzHv95n  // ← NEW
[LOCK] refreshEvents() completed
```

**Expected UI Changes (IMMEDIATE - no refresh):**
- ✅ Success toast: "Combine locked successfully..."
- ✅ Header changes to "🔒 Combine Results Locked" (red gradient)
- ✅ Button changes to "Unlock Combine Results" (green)
- ✅ Shows timestamp: "Locked on [date/time]"

**Network Tab Verification:**
```
1. PATCH /api/leagues/.../events/.../lock
   Status: 200 OK
   Response: {"isLocked": true, "verified": true, ...}

2. GET /api/leagues/.../events
   Status: 200 OK
   Response: {"events": [{"id": "...", "isLocked": true, ...}]}
```

---

### 4. Test Unlock Flow

With combine still locked from step 3:

1. Click "Unlock Combine Results" button (green)
2. No confirmation modal - immediate action

**Expected Console Output:**
```
[LOCK] Sending lock toggle request: {currentState: true, newState: false}
[LOCK] Backend response: {isLocked: false, changed: true, verified: true}
[LOCK] Calling refreshEvents() to sync UI...
[EVENT-CONTEXT] Invalidated events cache for league ...
[EVENT-CONTEXT] Synced selectedEvent after refresh: ...
[LOCK] refreshEvents() completed
```

**Expected UI Changes (IMMEDIATE):**
- ✅ Success toast: "Combine unlocked. Coaches can now edit..."
- ✅ Header changes to "🔓 Combine Results Unlocked" (green)
- ✅ Button changes to "Lock Combine Results" (red)

---

### 5. Test State Persistence

1. Lock the combine (using steps from #3)
2. Verify UI shows locked state
3. Refresh browser (F5 or Cmd+R)
4. Navigate back to Admin Tools

**Expected:**
- ✅ Locked state persists after refresh
- ✅ Still shows "🔒 Combine Results Locked"
- ✅ Still shows "Unlock Combine Results" button

---

### 6. Test Coach Read-Only Enforcement

**While Combine is Locked:**

1. Open incognito/private browser
2. Login as coach with event access
3. Navigate to Players page

**Expected:**
- ✅ Coach sees "Combine Locked" indicator
- ✅ Edit buttons disabled
- ✅ Attempting modifications shows error: "This combine has been locked. Results are final..."

**After Unlocking:**
1. As organizer, unlock the combine
2. Coach refreshes their page

**Expected:**
- ✅ Coach regains edit access (based on individual permissions)

---

## Troubleshooting

### Issue: Still seeing old behavior (fb44ad5)

**Diagnosis:**
- Frontend build hasn't deployed yet
- Browser cache serving old version
- CDN hasn't invalidated

**Solutions:**
1. Wait 5-10 minutes for deployment
2. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
3. Clear browser cache completely
4. Try incognito/private window

---

### Issue: Console logs missing

**Diagnosis:**
- Old frontend code still running
- Build didn't include changes

**Check:**
```javascript
// In browser console, type:
EventContext
// Should show the updated component with new logging
```

---

### Issue: Backend shows verified: false

**Diagnosis:**
- Firestore write failed
- Permission issue

**Check Backend Logs:**
```
[LOCK] VERIFICATION FAILED - Event ... shows isLocked=False, expected True
```

**Solutions:**
1. Check Firestore permissions in Firebase Console
2. Verify event exists in both collections
3. Check for Firestore quota limits

---

## Success Criteria

### ✅ All Tests Pass

- [ ] Lock from unlocked → UI updates immediately
- [ ] Unlock from locked → UI updates immediately
- [ ] State persists after browser refresh
- [ ] Coach read-only enforcement works
- [ ] Backend logs show `verified: true`
- [ ] Console logs show cache invalidation
- [ ] Console logs show selectedEvent sync

### ✅ No Errors

- [ ] No 404/500 errors in Network tab
- [ ] No console errors during lock toggle
- [ ] Backend logs show no VERIFICATION FAILED

### ✅ Build Information

- [ ] Frontend build SHA is NOT `fb44ad5`
- [ ] Backend shows commit `cf33dd5`
- [ ] Render deployment status: ✅ Live

---

## Sign-Off

**Tested By:** _________________  
**Date:** _________________  
**Status:** ⬜ PASS | ⬜ FAIL | ⬜ NEEDS REVIEW

**Notes:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

## Rollback (if needed)

```bash
cd /Users/richarcher/Desktop/WooCombine\ App
git revert cf33dd5
git push origin main
# Render will auto-deploy rollback
```

