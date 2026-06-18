# PACK.md — Mobile
**Pack**: `mobile`
**Domain**: Mobile app development (Flutter, React Native, Swift/SwiftUI, Kotlin/Jetpack Compose)
**Core framework version tested**: 1.14+

---

## When to use this pack

Select when the project delivers a native or cross-platform mobile application. The core `frontend-developer` agent understands web UI; this pack adds the mobile-specific mindset: platform lifecycle, app-store constraints, device fragmentation, and offline-first patterns.

**Select this pack when your project involves:**
- Flutter or React Native cross-platform apps
- Native iOS (Swift/SwiftUI) or Android (Kotlin/Jetpack Compose) development
- Mobile SDKs, plugins, or packages published to pub.dev / npm / Maven
- Projects with push notifications, background tasks, deep links, or biometric auth

**Do NOT select if:** the project is a web app that happens to be mobile-responsive — the core `frontend-developer` is sufficient.

---

## What this pack adds

| Resource | Type | Purpose |
|----------|------|---------|
| `mobile-developer` | Agent | Mobile-first implementer: platform lifecycle, widget trees, app-store awareness |
| `ui-accessibility` | Skill | WCAG mobile + screen reader + touch target audit |
| `platform-compatibility` | Skill | iOS/Android API level checks, deprecation, device fragmentation |

**Boundary from core agents:**
- Core `frontend-developer` handles: web components, browser DOM, CSS, web accessibility
- This pack's `mobile-developer` handles: platform widgets, navigation stacks, hot-reload workflow, native API bridging, app lifecycle (foreground/background/terminated), app-store submission constraints

---

## Install

Selected automatically during interactive `setup.sh`. To add to an existing install:

```sh
sh ~/.supervisor/setup.sh --pack mobile
```

---

## Agents installed

### `mobile-developer`
**File**: `packs/mobile/agents/mobile-developer.md`
Implements mobile UI slices test-first with platform-aware patterns: widget/component trees, navigation stacks, state management, native API bridging, and offline-first data sync. Flags app-store policy risks (permissions, background limits, API usage) before implementation begins.

---

## Skills installed

### `ui-accessibility`
**File**: `packs/mobile/skills/ui-accessibility/SKILL.md`
Audits mobile UI for WCAG 2.2 AA compliance, screen reader compatibility (VoiceOver / TalkBack), touch target sizing (≥44pt), and color contrast. Invoke before any Stage 4 review of a UI task.

### `platform-compatibility`
**File**: `packs/mobile/skills/platform-compatibility/SKILL.md`
Checks iOS deployment target / Android `minSdkVersion` compliance, deprecated API usage, and device fragmentation risks. Invoke when a task adds or changes native API calls, permissions, or platform-specific branches.
