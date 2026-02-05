# WooCombine UX Audit Report
**Date:** 2026-02-03
**Auditor:** Tosh (Automated)
**URL:** https://tosh-woo-combine.web.app

---

## Critical Issues

### 1. ⏳ CORS Misconfiguration (FIXED - DEPLOYING)
**Location:** Backend API
**Status:** Code fix pushed to GitHub, awaiting Render auto-deploy (~3-5 min)

**Issue:** Backend CORS only allowed `woo-combine.com`, not the new Firebase Hosting domain `tosh-woo-combine.web.app`. All API calls blocked with "Network Error".

**Fix:** Updated `/backend/main.py` CORS regex to include Firebase Hosting domains.

---

### 2. ⚠️ Main CTA Leads to Dead End
**Location:** Landing Page → "Start Setup Now" button
**Status:** Design decision needed

**Issue:** The prominent "🚀 Start Setup Now" button leads directly to an "Invite-Only" page saying signups are closed. This is confusing for new visitors.

**Recommendation:** Either:
- A) Remove/hide the button when signups are closed
- B) Change button text to "Request Access" or "Join Waitlist"
- C) Enable public signups

**Screenshot:** See landing page screenshot

---

### 3. ⚠️ URL Mismatch on Login/Signup
**Location:** Auth pages
**Status:** Minor issue

**Issue:** "Return to Sign In" link on Invite-Only page goes to `/signup` but the page shows "Welcome Back" sign-in form. URL doesn't match content.

**Recommendation:** Fix routing - `/signup` should show signup form, `/login` should show login form.

---

## UI/Design Issues

### 4. 🎨 Footer Links Very Low Contrast
**Location:** All pages (footer)
**Status:** Accessibility concern

**Issue:** Footer links (Terms, Privacy, Contact) are barely visible - very light gray on light background. May not pass WCAG contrast requirements.

**Recommendation:** Darken footer text to at least 4.5:1 contrast ratio.

---

### 5. ✅ Role Selection Page - Good
**Location:** `/select-role`
**Status:** Working well

**Notes:**
- Clear role descriptions
- Visual confirmation when selected (checkmark appears)
- "Continue" button disabled until selection made
- "Can be changed later" reassurance shown

---

## Backend/Infrastructure Issues

### 6. ⏳ Cold Start Delay
**Location:** Login flow
**Status:** Expected (Render free tier)

**Issue:** Backend takes 30+ seconds to respond on first request after inactivity.

**Mitigation (already implemented):**
- UI shows "Server is waking up" message
- Good user feedback during wait

---

## Pending Tests (blocked by CORS fix deploy)

- [ ] Complete role selection flow
- [ ] Event creation flow
- [ ] Player management
- [ ] Live scoring entry
- [ ] Rankings generation
- [ ] Export functionality

---

## Next Steps

1. Wait for Render backend deploy (~2-3 min)
2. Continue UX audit through full user flow
3. Document any additional issues found

