# NoteKeeper UI/UX Specification

> Comprehensive design specifications for the NoteKeeper secure note-taking application

**Version:** 1.0.0  
**Last Updated:** April 2026  
**Status:** Ready for Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [Design System](#design-system)
3. [User Flows](#user-flows)
4. [Wireframe Specifications](#wireframe-specifications)
5. [Interaction Design](#interaction-design)
6. [Accessibility](#accessibility)
7. [Responsive Design](#responsive-design)
8. [Related Resources](#related-resources)

---

## Overview

This document provides comprehensive UI/UX specifications for NoteKeeper, a secure note-taking REST API application with categories, tags, full-text search, and markdown support.

### Project Identifiers

- **GitHub Repository:** `bhogarinc/notekeeper-api`
- **Confluence Space:** `NK` (NoteKeeper)
- **Primary Tech Stack:** React, TypeScript, Tailwind CSS (frontend)

### UI/UX GitHub Issues Created

| Issue | Title | Story Points | Status |
|-------|-------|--------------|--------|
| #60 | Design System and Component Library Specification | 8 | Open |
| #61 | User Flows and Navigation Design | 8 | Open |
| #63 | Wireframe Specifications for All Screens | 13 | Open |
| #65 | Interaction Design and Micro-interactions | 5 | Open |
| #67 | Accessibility (a11y) Implementation Guide | 5 | Open |

---

## Design System

### Color Palette

#### Primary Colors
```css
--color-primary-50: #EEF2FF   /* Lightest backgrounds */
--color-primary-100: #E0E7FF  /* Hover backgrounds */
--color-primary-500: #6366F1  /* Primary actions */
--color-primary-600: #4F46E5  /* Active states */
--color-primary-700: #4338CA  /* Focus rings */
```

#### Semantic Colors
| Token | Value | Usage | Contrast Ratio |
|-------|-------|-------|----------------|
| Success | #10B981 | Success states | 4.6:1 |
| Warning | #F59E0B | Warnings | 4.5:1 |
| Error | #EF4444 | Errors | 4.5:1 |
| Info | #3B82F6 | Information | 4.5:1 |

#### Neutral Colors (Light Mode)
| Token | Value | Dark Mode |
|-------|-------|-----------|
| Background Primary | #FFFFFF | #0F172A |
| Background Secondary | #F8FAFC | #1E293B |
| Text Primary | #0F172A | #F8FAFC |
| Text Secondary | #475569 | #94A3B8 |
| Border | #E2E8F0 | #334155 |

### Typography System

#### Font Stack
```css
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', Consolas, Monaco, monospace;
```

#### Type Scale
| Style | Size | Weight | Line Height |
|-------|------|--------|-------------|
| H1 | 36px / 2.25rem | 700 | 1.2 |
| H2 | 30px / 1.875rem | 600 | 1.25 |
| H3 | 24px / 1.5rem | 600 | 1.3 |
| H4 | 20px / 1.25rem | 600 | 1.35 |
| Body | 16px / 1rem | 400 | 1.6 |
| Body Small | 14px / 0.875rem | 400 | 1.5 |
| Caption | 12px / 0.75rem | 400 | 1.4 |

### Spacing System

Based on 4px grid foundation:

| Token | Value | Usage |
|-------|-------|-------|
| space-1 | 4px | Tight spacing |
| space-2 | 8px | Internal padding |
| space-4 | 16px | Standard padding |
| space-6 | 24px | Section padding |
| space-8 | 32px | Large gaps |
| space-16 | 64px | Page spacing |

### Component Library

#### Buttons
- **Height:** 40px (standard), 32px (small), 48px (large)
- **Border Radius:** 8px
- **Variants:** Primary, Secondary, Ghost, Danger
- **States:** Default, Hover, Active, Focus, Disabled, Loading

#### Form Inputs
- **Height:** 40px
- **Border Radius:** 8px
- **States:** Default, Hover, Focus, Error, Disabled
- **Features:** Icon support, validation states, helper text

#### Cards (Note Cards)
- **Min Height:** 180px (desktop), 160px (tablet), 140px (mobile)
- **Padding:** 20px
- **Border Radius:** 12px
- **Shadow:** 0 1px 3px rgba(0,0,0,0.1)
- **Hover:** Lift -4px, enhanced shadow

#### Modals
- **Max Width:** 480px (small), 640px (medium), 900px (large)
- **Border Radius:** 16px
- **Animation:** Scale 0.95 → 1, fade in 250ms

---

## User Flows

### 1. Authentication Flows

#### Login Flow
```
Entry → Check Auth → Login Screen → Validate → Submit → Success → Dashboard
                                              ↓
                                          Error Toast
```

**Key Interactions:**
- Real-time validation on blur
- "Remember Me" option (30 days)
- Forgot password link
- Create account link

#### Registration Flow
```
Login → Create Account → Form (Name, Email, Password, Terms) → Validate → Submit → Verification Email → Login
```

**Features:**
- Password strength indicator
- Real-time validation
- Terms acceptance required

### 2. Note Management Flows

#### Create Note
```
New Note Button → Editor Opens → Auto-save (3s) → Manual Save → Success Toast → List Update
```

**Entry Points:**
- "+ New Note" button
- Ctrl/Cmd + N shortcut
- Sidebar link

#### Edit Note
```
Select Note → Editor Opens (pre-populated) → Edit → Track Changes → Save → Optimistic Update
```

**Features:**
- Dirty state tracking
- "Unsaved changes" warning
- Optimistic UI updates

#### Delete Note
```
Delete Action → Confirmation Dialog → Confirm → Move to Trash → Undo Toast (5s)
```

### 3. Navigation Structure

```
NoteKeeper
├── Authentication
│   ├── Login
│   ├── Register
│   ├── Forgot Password
│   └── Reset Password
├── Main Application
│   ├── Dashboard
│   ├── Notes (All, Pinned)
│   ├── Categories
│   ├── Tags
│   ├── Archive
│   ├── Search
│   └── Settings
```

### 4. Keyboard Shortcuts

| Shortcut | Action | Context |
|----------|--------|---------|
| Ctrl/Cmd + N | New Note | Global |
| Ctrl/Cmd + K | Open Search | Global |
| Ctrl/Cmd + S | Save Note | Editor |
| Ctrl/Cmd + P | Toggle Pin | Note selected |
| Ctrl/Cmd + E | Edit Note | Note selected |
| Escape | Close/Cancel | Modal/Editor |
| / | Focus Search | Global |

---

## Wireframe Specifications

### 1. Authentication Screens

#### Login Screen (Desktop)
- Centered card layout, 420px width
- Logo at top
- Email and password fields
- Remember me checkbox
- Sign In button (48px height)
- Forgot password and Create account links

**Responsive:**
- Desktop: Centered card with shadow
- Mobile: Full-width card, 100% - 32px margins

### 2. Dashboard Layout

#### Desktop Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Header: Logo | Search | Settings | Profile                  │
├─────────────┬───────────────────────────────────────────────┤
│             │ Pinned Notes Section                          │
│  Sidebar    ├───────────────────────────────────────────────┤
│  (260px)    │ All Notes Grid                                │
│             │                                               │
│  Navigation │ [Card] [Card] [Card] [Card]                   │
│  Categories │ [Card] [Card] [Card] [Card]                   │
│  Tags       │                                               │
│  Archive    │ Pagination                                    │
└─────────────┴───────────────────────────────────────────────┘
```

#### Note Card Structure
1. Title (H6, max 2 lines)
2. Preview (Body Small, max 3 lines)
3. Category badge
4. Tag chips
5. Timestamp
6. Action buttons (pin, edit, delete) - visible on hover

### 3. Note Editor

#### Desktop (Split View)
- Sidebar + Editor panels
- Title input (H2 size)
- Category selector
- Tag input with chips
- Rich text toolbar
- Content textarea
- Save/Cancel buttons

#### Mobile (Full-screen Modal)
- Header with back and save buttons
- Title input
- Category and tags row
- Toolbar
- Full-height content area

### 4. Responsive Breakpoints

| Breakpoint | Width | Columns | Navigation |
|------------|-------|---------|------------|
| Mobile | < 640px | 1 | Bottom tab bar |
| Tablet | 640-1023px | 2 | Collapsible sidebar |
| Desktop | 1024-1279px | 3 | Persistent sidebar |
| Large Desktop | ≥ 1280px | 4 | Persistent sidebar |

---

## Interaction Design

### Animation Timing

| Type | Duration | Easing |
|------|----------|--------|
| Micro-interaction | 150ms | ease-out |
| UI Response | 200ms | cubic-bezier(0.4, 0, 0.2, 1) |
| Modal | 250ms | cubic-bezier(0, 0, 0.2, 1) |
| Page Transition | 300ms | cubic-bezier(0.4, 0, 0.2, 1) |
| List Item | 350ms | cubic-bezier(0.4, 0, 0.6, 1) |

### Form Validation

- **Inline Validation:** On blur for most fields
- **Real-time:** Password strength indicator
- **Error Animation:** Shake 300ms + message slide-down
- **States:** Default, Focus, Valid (green check), Invalid (red border)

### Loading States

#### Skeleton Screens
- Shimmer animation: 1.5s infinite
- Show 6 skeleton cards initially
- Stagger delay: 100ms per card
- Cross-fade to content: 400ms

#### Loading Indicators
- Inline: 16px spinner
- Page: 32px spinner
- Overlay: 48px spinner
- Progress bar: 4px height for uploads

### Toast Notifications

| Type | Duration | Position |
|------|----------|----------|
| Success | 3000ms | Top-right (desktop), Bottom (mobile) |
| Error | 5000ms | Top-right (desktop), Bottom (mobile) |
| Warning | 4000ms | Top-right (desktop), Bottom (mobile) |
| Info | 3000ms | Top-right (desktop), Bottom (mobile) |

**Animation:** Slide in from right 300ms, slide out 200ms

### Micro-interactions

#### Button States
- **Hover:** Lift -1px, darken background (150ms)
- **Active:** Scale 0.98 (100ms)
- **Focus:** Ring 2px
- **Loading:** Text fades, spinner appears (200ms)

#### Card Hover
- Lift -4px
- Enhanced shadow
- Show action buttons
- Transition: 200ms

#### Pin Animation
- Rotate -45deg when pinned
- Scale 1.1 on hover
- Bounce easing

---

## Accessibility

### WCAG 2.1 AA Compliance

#### Perceivable
- All images have alt text
- Semantic HTML structure
- Color contrast 4.5:1 minimum
- Text resizable to 200%
- Content reflows at 320px

#### Operable
- All functionality via keyboard
- Visible focus indicators (2px ring, 2px offset)
- No keyboard traps
- Logical tab order

#### Understandable
- Clear error messages
- Form labels and instructions
- Error prevention for destructive actions

### Keyboard Navigation

- **Tab/Shift+Tab:** Navigate between elements
- **Enter/Space:** Activate buttons/links
- **Escape:** Close modals/menus
- **Focus Management:** Trap in modals, restore on close

### Screen Reader Support

#### ARIA Landmarks
```html
<header role="banner">
<nav role="navigation">
<main role="main">
<aside role="complementary">
```

#### Live Regions
- `role="status"` for non-critical updates
- `role="alert"` for errors
- `aria-live="polite"` for search results

### Focus Management

```css
:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px white, 0 0 0 4px #4F46E5;
}
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Responsive Design

### Mobile First Approach

1. Base styles for mobile (< 640px)
2. Progressive enhancement for larger screens
3. Touch-friendly targets (min 44px)
4. Optimized typography scaling

### Breakpoint Strategy

```css
/* Mobile first */
/* Base styles here */

/* Tablet */
@media (min-width: 640px) { }

/* Desktop */
@media (min-width: 1024px) { }

/* Large Desktop */
@media (min-width: 1280px) { }
```

### Navigation Patterns

| Device | Pattern |
|--------|---------|
| Mobile | Bottom tab bar (4-5 items) |
| Tablet | Collapsible sidebar |
| Desktop | Persistent sidebar (260px) |

---

## Related Resources

### Confluence Documentation

| Page | ID | Content |
|------|-----|---------|
| Design System | 13435397 | Color, typography, spacing, components |
| User Flows | 13664930 | Authentication, notes, categories, tags |
| Wireframes | 13435504 | Screen layouts, responsive specs |
| Interactions | 13664979 | Animations, micro-interactions |
| Accessibility | 13533574 | WCAG compliance, a11y guidelines |

### Code Files

| File | Path | Description |
|------|------|-------------|
| Design Tokens | `frontend/src/styles/design-tokens.css` | CSS custom properties |
| Animations | `frontend/src/styles/animations.css` | Keyframes and utilities |
| Components | `frontend/src/styles/components.css` | Base component styles |

### GitHub Issues

- [UI/UX-001: Design System (#60)](https://github.com/bhogarinc/notekeeper-api/issues/60)
- [UI/UX-002: User Flows (#61)](https://github.com/bhogarinc/notekeeper-api/issues/61)
- [UI/UX-003: Wireframes (#63)](https://github.com/bhogarinc/notekeeper-api/issues/63)
- [UI/UX-004: Interactions (#65)](https://github.com/bhogarinc/notekeeper-api/issues/65)
- [UI/UX-005: Accessibility (#67)](https://github.com/bhogarinc/notekeeper-api/issues/67)

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Set up CSS custom properties (design-tokens.css)
- [ ] Configure Tailwind with custom theme
- [ ] Set up font loading (Inter, JetBrains Mono)
- [ ] Implement dark mode toggle

### Phase 2: Components
- [ ] Button component (all variants)
- [ ] Form inputs (text, textarea, select)
- [ ] Card component
- [ ] Modal component
- [ ] Toast notification system

### Phase 3: Layouts
- [ ] Authentication layouts
- [ ] Dashboard layout with sidebar
- [ ] Note editor (split view + modal)
- [ ] Settings page
- [ ] Archive/Trash views

### Phase 4: Interactions
- [ ] Page transitions
- [ ] Loading skeletons
- [ ] Form validation animations
- [ ] Toast notifications
- [ ] Hover effects and micro-interactions

### Phase 5: Accessibility
- [ ] Keyboard navigation
- [ ] Focus management
- [ ] Screen reader testing
- [ ] Color contrast verification
- [ ] Reduced motion support

---

*This specification is a living document and will be updated as the project evolves.*
