# SPEC.md Template (Apple → Android port)

Copy this skeleton into `plans/SPEC.md` in the target repo and fill each
section. Section order and headings are deliberate — they mirror the order an
implementer needs the answers in.

Inline guidance is in `<!-- comments -->`. Delete the comments after filling.

---

```markdown
# <Project Name> for <Android Target> — Port Specification (SPEC)

> **Status:** Draft v1.0 — authoritative source for decomposition.
> **Purpose:** Recreate <Apple app name> *exactly as it is today* as a native
> <Android target: phone / Wear OS / TV / Auto> app. This document is the single
> source of truth an agent (or the Ralph loop, via `spec-decomposition`) uses to
> plan and build the port. The per-issue breakdown is produced afterward by
> `spec-decomposition`.

---

## 0. How to use this document

1. Read this SPEC end-to-end before writing any code.
2. Run `spec-decomposition` against it to file epics + child issues.
3. The Ralph loop then works issues one at a time.
4. The **source of truth for behavior** is the Apple app at `<path>` (the
   "source repo"). When this SPEC and the source disagree, **the source wins** —
   file a SPEC fix issue.

<!-- Reuse bundled data verbatim where possible; mention which files. -->

---

## 1. Product overview

<!-- 1 paragraph: what the app does. Followed by the non-negotiable invariants. -->

**Product invariants (non-negotiable, carried from the source):**
- <e.g., "100% offline — no network calls">
- <e.g., "Cryptographically fair randomness">
- <e.g., "<feature flag X> remains hidden">

---

## 2. Goals / Non-goals

### Goals
- <Faithful feature parity with the source — list the parity scope>
- <Idiomatic <Android target> implementation>
- <Reuse of <bundled assets / data> unchanged>
- <Quality bar matching the source's CI gates>

### Non-goals (v1.0)
- <e.g., "Phone companion module (source is watch-only)">
- <e.g., "CloudKit sync — no Android equivalent without a backend">
- <e.g., "Siri voice fidelity — no Android equivalent">
- <Every feature the user might expect but isn't in scope>

---

## 3. Technology mapping (Apple → Android)

<!-- Adapt the mapping rows from references/platform-mapping.md for your platform pair. -->

| Concern | Source (Apple) | Port (Android) |
|---|---|---|
| Language | Swift | Kotlin |
| UI framework | <SwiftUI / UIKit / AppKit> | <Compose / Compose for Wear OS / Compose for TV> |
| ... | ... | ... |

**Decision defaults** (override only with a logged `architectural-decisions` note): <list>.

---

## 4. Target project structure

<!-- Propose a Kotlin/Gradle layout whose package tree mirrors the source 1:1. -->

```
<project>/
├── settings.gradle.kts
├── build.gradle.kts
├── gradle/libs.versions.toml
├── app/
│   ├── build.gradle.kts
│   └── src/
│       ├── main/
│       │   ├── AndroidManifest.xml
│       │   ├── kotlin/<package>/
│       │   │   ├── <AppName>App.kt
│       │   │   ├── MainActivity.kt
│       │   │   ├── ui/
│       │   │   ├── viewmodel/
│       │   │   ├── data/
│       │   │   ├── util/
│       │   │   └── config/
│       │   └── res/ (or assets/)
│       ├── test/
│       └── androidTest/
└── plans/
    └── SPEC.md (this file)
```

---

## 5. Architecture (MVVM + interface DI)

<!-- Preserve the source's layering. State the layering rule, dependencies, coverage targets. -->

| Layer | Target coverage |
|---|---|
| Models | 95–100% |
| ViewModels | 95–100% |
| Utilities | 95–100% |
| Repositories | 90–100% |
| Components | 60%+ |
| Screens | functional via UI tests |
| **Overall** | **≥ <floor>%** |

---

## 6. Screens & navigation (feature parity)

<!-- One subsection per screen. For each: what it shows, interactions, state, navigation, animations. -->

### 6.1 <Screen A>
- **What it shows:** ...
- **Interactions:** ...
- **State:** ...
- **Navigation:** ...
- **Animations / haptics / sounds:** ...

### 6.2 <Screen B>
...

---

## 7. Data layer

### 7.1 Domain models
<!-- Each model: fields, types, computed properties, fallbacks. -->

### 7.2 Bundled data (`<DataFile.json>`) — schema (reuse verbatim)
<!-- Quote the schema. State the file is copied unchanged. -->

### 7.3 Image / audio / font assets — pipeline
<!-- Naming convention, source location, target location, build-time integrity test. -->

### 7.4 Persistence (`<Model>` → Room)
<!-- Entity columns 1:1 with the source model. DAO queries with limits and sort orders. Resilient init. -->

### 7.5 Repositories
<!-- Each repo: load paths, validation rules quoted from source, error types, fallbacks. -->

---

## 8. Core algorithms (port verbatim)

<!-- Quote each non-trivial algorithm from the source. Sketch the Kotlin port. Preserve cancellation, error paths, edge cases. -->

### 8.1 <Algorithm name>
```swift
// Source (Swift):
<paste verbatim>
```
```kotlin
// Port (Kotlin):
<sketch>
```

---

## 9. <Input sanitization / validation rules> (port exactly)

<!-- Any user-input handling. Quote the rules verbatim and port them. -->

---

## 10. ViewModels (state + behavior)

<!-- One subsection per ViewModel: state shape (StateFlow properties), public methods, dependencies. -->

### 10.1 `<NameViewModel>`
- **State:** ...
- **Behavior:** ...
- **Dependencies (interfaces):** ...

---

## 11. Theming, layout & accessibility

- **Theme:** colors, typography, spacing — port the palette exactly.
- **Layout:** responsive sizing across device matrix.
- **Accessibility checklist** (per surface):
  - [ ] Every interactive element has a content description / semantics label.
  - [ ] TalkBack-tested.
  - [ ] Touch targets ≥ 48dp.
  - [ ] Dynamic font scaling honored.
  - [ ] Color contrast ≥ AA.

---

## 12. Configuration constants (`AppConstants` / `FeatureFlags`)

| Constant | Value | Notes |
|---|---|---|
| ... | ... | ... |

---

## 13. Testing strategy

### Test parity matrix
| Source test category | Android equivalent |
|---|---|
| XCTest unit | JUnit5 + MockK + Turbine |
| XCUITest UI | Compose UI test (`createAndroidComposeRule`) |
| Asset integrity | Build-time test asserting every referenced resource resolves |
| Statistical / property-based | <kotest-property / jqwik> |

### Coverage gates
- Overall ≥ <floor>%; per-layer per §5.

### Performance budgets (per surface)
| Surface | Budget |
|---|---|
| <e.g., card draw> | < 100ms cold |
| <e.g., view transition> | < 50ms |
| <e.g., image render> | < 16ms |

---

## 14. Build, CI & quality gates

- **Gradle (Kotlin DSL)**, version catalog at `gradle/libs.versions.toml`.
- **Quality scripts** (`scripts/*.sh`).
- **CI (`.github/workflows/ci.yml`)**: pre-commit + JDK + Gradle cache + ktlint + detekt + tests + Kover; assemble debug APK; emulator instrumented tests.
- **Pre-commit**: generic hooks + ktlint + detect-secrets + shellcheck.

---

## 15. Android-platform specifics

- **Manifest**: <required permissions, uses-feature, standalone for Wear, target/min SDK>.
- **<Form factor>-specific**: <gesture conflicts, TimeText/Vignette for Wear, predictive back for phone, edge-to-edge, dark theme, foldable layouts>.
- **Play Store**: target SDK timeline, Data Safety declaration, privacy URL.
- **Device matrix to test**: <specific devices/form factors>.

---

## 16. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| <e.g., memory pressure on watch from many high-res images> | M | H | Load on demand; size to displayed bounds; test on low-end device |
| <e.g., swipe-dismiss + pager gesture conflict> | M | M | Prototype in Epic 1; prefer Wear `HorizontalPager` |
| <e.g., StatFs returns 0 in some emulators> | L | M | Wrap + unit-test boundary conditions; never throw |

---

## 17. Decomposition guidance (epics — to be expanded by `spec-decomposition`)

Tracer-code ordering (skeleton first; every later epic preserves a demoable system):

1. **Epic: Project skeleton & CI** — Gradle module, minimal navigation host, CI green. *Bootstrap note: like the source's manual Xcode skeleton, this epic may be landed by hand before starting the Ralph loop.*
2. **Epic: Data layer** — domain models, serialization, repositories, persistence (Room), asset integrity test.
3. **Epic: <Core feature loop>** — <RNG, primary VM, primary screen + flow>.
4. **Epic: <Secondary surface>** — ...
5. **Epic: <Tertiary surface>** — ...
6. **Epic: Theming, accessibility & responsive layout** — ...
7. **Epic: <Platform-specific surface — Tile / App Widget / App Action>** — ...
8. **Epic (deferred / flag-gated): <Future feature>** — ...

Each issue must carry tracer-code sequencing, a 6-component prompt body,
stay-green Done-Done gates, and the max-quality anti-bypass clause.

---

## 18. Definition of done (the port is "done" when…)

- [ ] All §6 screens exist and match the source's behavior and flows.
- [ ] All §8/§9 algorithms reproduce the source's outputs (verified by tests).
- [ ] <Bundled assets> load offline from bundled resources; zero network calls.
- [ ] <Persistence behavior, e.g., history persists across launches; storage warnings work>.
- [ ] CSPRNG / <core invariant> verified by tests.
- [ ] CI green; coverage ≥ floor; ktlint/detekt clean.
- [ ] <Platform-specific surfaces> work end-to-end.
- [ ] <Flag-gated features> remain hidden but code-complete behind the flag.

---

## Appendix A — Source-of-truth file map (source → port)

<!-- A 2-column table mapping every source file to its target counterpart. Reviewers use this to A/B. -->

| Source (Swift) | Port (Kotlin) |
|---|---|
| `<path>/<File>.swift` | `<path>/<File>.kt` |
| ... | ... |

## Appendix B — Open questions to resolve during decomposition

<!-- Real questions, not placeholders. Each is a 1-line bullet. -->

- <Asset density bucket strategy: per-density vs single `drawable-nodpi`>
- <DI framework: manual `AppContainer` vs Hilt>
- <Navigation primitive: `HorizontalPager` vs `SwipeDismissableNavHost` + pager>
- ...
```
