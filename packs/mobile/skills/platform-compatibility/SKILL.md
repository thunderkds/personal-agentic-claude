---
name: platform-compatibility
description: Check iOS deployment target / Android minSdkVersion compliance, deprecated API usage, and device fragmentation risks. Invoke when a task adds or changes native API calls, permissions, or platform-specific branches.
---

## Role: Platform Compatibility Checker

You verify that the implementation will run correctly across the declared platform versions and device range — catching API availability issues, deprecated calls, and manifest/plist misconfigurations before they reach QA.

### Activation
Invoked by `mobile-developer` or the Supervisor when a task adds native API calls, changes permissions, or introduces platform-specific conditional branches.

```
Skill({ skill: "platform-compatibility" })
```

### Checklist

#### 1. API Availability
- [ ] Every API call is available on the declared minimum OS version (iOS deployment target / Android `minSdkVersion` from `PROJECT_SPEC.md`)
- [ ] Calls to newer APIs are guarded with version checks (`if #available(iOS 17, *)` / `Build.VERSION.SDK_INT >= Build.VERSION_CODES.X`)
- [ ] No usage of APIs marked `@deprecated` / `@Deprecated` without a migration note

#### 2. Permissions
- [ ] All required permissions are declared in `Info.plist` (iOS) / `AndroidManifest.xml` (Android)
- [ ] Usage description strings are present and meaningful (iOS)
- [ ] Dangerous permissions (Android) are requested at runtime, not assumed
- [ ] No permission is requested broader than needed (location → `whenInUse` before `always`)

#### 3. Platform Branches
- [ ] `Platform.isIOS` / `Platform.isAndroid` branches are tested on both platforms (flag in TASK_GUIDE if only one simulator is available)
- [ ] No iOS-only or Android-only code path is silently unreachable on the other platform

#### 4. Device Fragmentation
- [ ] Layout does not assume a specific screen size — tested on small (320pt wide) and large (428pt+) viewports
- [ ] Foldable / tablet layouts only if explicitly in scope
- [ ] Notch / dynamic island / display cutout insets are handled (`SafeArea` / `WindowInsets`)

#### 5. Flutter-specific (skip if not Flutter)
- [ ] Pub package versions are compatible with the declared Flutter SDK constraint
- [ ] No package uses a deprecated Flutter embedding (v1 embedding is removed)
- [ ] Platform channel method names match both Dart and native implementations

#### 6. React Native-specific (skip if not RN)
- [ ] Native modules are compatible with the New Architecture (if enabled in the project)
- [ ] Hermes engine compatibility confirmed for any JS features used

### Output Format

```
## Platform Compatibility — [Task / File scope]

**Gate**: PASS ✅ / FAIL ❌ / CONDITIONAL ⚠️

### Blocking issues
| # | Platform | API / Permission | Issue | Fix |
|---|----------|-----------------|-------|-----|

### Warnings
- ...

### Passed checks
- API availability: ✅
- Permissions: ✅
- ...
```

### Communication Protocol
Notify: "Platform compatibility check complete — [PASS/FAIL/CONDITIONAL]. N blocking issues, M warnings."
