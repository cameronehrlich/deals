# Spec: Streamline Deals Flow

**Status:** Implemented
**Author:** BlackCastle (Claude Code)
**Date:** 2026-01-04

## Overview

Simplify the property analysis workflow by removing the standalone Analyze page. Users will browse properties on Find Deals, save interesting ones with a single click (which triggers background enrichment), and view full analysis in Saved Properties.

## Goals

1. **Reduce friction** - One-click "Save & Analyze" replaces multi-step navigation
2. **Simplify codebase** - Maintain only one property detail view (Saved Properties)
3. **Better UX** - Show real-time job queue status on the deals page
4. **Preserve URL import** - Add subtle import button to Find Deals for manual URL entry

## Current State

- **Find Deals page** (`/deals`) - Browse listings, "Analyze" button navigates to `/import`
- **Analyze page** (`/import`) - URL import form + full property analysis display
- **Saved Properties** (`/saved`) - List of saved properties with analysis
- **Navigation** - 7 items including separate "Analyze" link

## Proposed Changes

### 1. Find Deals Page (`web/src/app/deals/page.tsx`)

#### A. Replace "Analyze" Button with "Save & Analyze"

**Current:**
```tsx
<button onClick={onAnalyze}>
  <TrendingUp /> Analyze
</button>
```

**Proposed:**
```tsx
// For unsaved properties
<button onClick={onSaveAndAnalyze}>
  <Bookmark /> Save & Analyze
</button>

// For already-saved properties
<button onClick={onViewSaved}>
  <Check /> View Saved
</button>
```

**Behavior:**
- Calls `api.enqueuePropertyJob()` (existing endpoint)
- Shows brief pulse/highlight animation on card
- Updates card state to show "Analyzing..." spinner
- Adds property ID to local `savedPropertyIds` set
- Does NOT navigate away

#### B. Card States

| State | Visual | Button |
|-------|--------|--------|
| Default | Normal card | "Save & Analyze" |
| Saving/Queued | Card pulse animation | Spinner + "Analyzing..." |
| Processing | Small spinner in corner | "Analyzing..." (disabled) |
| Saved | "Saved" badge on card | "View Saved" with checkmark |

#### C. Global Job Queue Indicator (Upper Right)

Add a small indicator near the header showing active jobs:

```
[Processing 2 of 5] or [Queue empty ✓]
```

**Location:** Upper right of the Find Deals page, below the "Live Data" badge

**Implementation:**
- Poll `/api/jobs/stats` or `/api/jobs?status=pending,running` periodically
- Show count of pending + running jobs for current session
- Clicking opens a dropdown/popover listing queued properties

#### D. URL Import Button

Add a subtle import option at the top of the page:

```
[Search controls...]                    [+ Import URL]
```

**Behavior:**
- Click reveals a collapsible text input: "Paste Zillow, Redfin, or Realtor URL"
- Submit enqueues the job (same as Save & Analyze)
- Shows success toast: "Property queued for analysis"
- Property appears in Saved Properties when complete

### 2. Navigation Updates (`web/src/components/Navigation.tsx`)

#### A. Remove "Analyze" Link

**Current:**
```tsx
{ name: "Analyze", href: "/import", icon: BarChart3 },
```

**Proposed:** Remove this item entirely.

#### B. Badge on "Saved" Link

Show count of properties being processed:

```tsx
<Link href="/saved">
  <Bookmark />
  Saved
  {processingCount > 0 && (
    <span className="badge">{processingCount}</span>
  )}
</Link>
```

### 3. Remove Analyze Page

**Delete:** `web/src/app/import/page.tsx`

**Note:** The URL import functionality moves to Find Deals page. Full analysis display moves to Saved Properties detail page.

### 4. Saved Properties Updates

The existing `/saved/[id]` detail page already shows full analysis. No major changes needed, but ensure:

- Location data is displayed
- "What Should I Offer" slider works
- Due Diligence can be triggered from here

## Animation Specification

### Save & Analyze Click Animation

1. Button changes to spinner + "Saving..."
2. Card gets `ring-2 ring-primary-500` highlight
3. After ~300ms, highlight fades with `transition-all duration-500`
4. "Saved" badge appears with `animate-fade-in`
5. Button changes to "View Saved" with checkmark

### CSS Classes Needed

```css
@keyframes pulse-ring {
  0% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(99, 102, 241, 0); }
  100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
}

.animate-pulse-ring {
  animation: pulse-ring 0.6s ease-out;
}
```

## API Endpoints (Existing)

No new endpoints required. Uses existing:

- `POST /api/jobs/enqueue-property` - Create property + enqueue enrichment
- `GET /api/jobs/stats` - Queue statistics
- `GET /api/jobs` - List jobs with filters
- `GET /api/saved/properties` - List saved properties
- `GET /api/saved/properties/{id}` - Get single property with analysis

## Data Flow

```
User clicks "Save & Analyze"
         ↓
Frontend calls api.enqueuePropertyJob()
         ↓
Backend creates SavedProperty (minimal data)
Backend creates Job (enrich_property)
         ↓
Frontend updates local state:
  - Add to savedPropertyIds
  - Show card animation
  - Increment queue counter
         ↓
Background worker processes job:
  - Geocode address
  - Fetch rent estimates
  - Get Walk Score, flood zone, etc.
  - Calculate financials
  - Update SavedProperty with full analysis
         ↓
User navigates to Saved Properties
User clicks property to see full analysis
```

## Edge Cases

1. **Duplicate save attempt** - API returns existing property ID, frontend shows "Already saved" and navigates to detail
2. **Job failure** - Show error state on card, allow retry
3. **Rate limit** - Show appropriate message, suggest trying later
4. **Network error** - Show retry button on card

## Files to Modify

| File | Changes |
|------|---------|
| `web/src/app/deals/page.tsx` | Replace Analyze button, add job indicator, add URL import |
| `web/src/components/Navigation.tsx` | Remove Analyze link, add badge to Saved |
| `web/src/app/import/page.tsx` | DELETE |
| `web/src/lib/api.ts` | No changes needed |
| `web/src/app/globals.css` | Add animation classes |

## Testing Checklist

- [ ] Save & Analyze creates property and enqueues job
- [ ] Card shows animation feedback
- [ ] "View Saved" button appears for saved properties
- [ ] Job queue indicator updates in real-time
- [ ] URL import works from Find Deals page
- [ ] Saved Properties shows enriched data
- [ ] Navigation badge shows processing count
- [ ] Duplicate saves handled gracefully
- [ ] Error states display appropriately

## Open Questions

None - all requirements clarified with user.

## Rollout Plan

1. Implement UI changes on Find Deals page
2. Add job queue indicator
3. Add URL import to Find Deals
4. Update Navigation (remove Analyze, add badge)
5. Delete Analyze page
6. Test full flow end-to-end
