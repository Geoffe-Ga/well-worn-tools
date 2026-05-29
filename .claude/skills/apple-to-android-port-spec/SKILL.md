---
name: apple-to-android-port-spec
description: >-
  Draft a comprehensive porting SPEC to recreate an existing Apple app
  (iOS / macOS / watchOS / iPadOS / tvOS in Swift, SwiftUI, UIKit, or
  AppKit) as a native Android app (phone, Wear OS, Android TV, or
  Android Auto). Use when the user says "port this to Android", "draft a
  porting SPEC", "Android version of <Apple app>", "Wear OS port of
  <watchOS app>", "Kotlin/Compose port of <SwiftUI app>", or "plan the
  Android port of <app>". Anchors the SPEC in a deep inventory of the
  source app, a canonical technology mapping table, faithful flow and
  algorithm ports, an explicit risk register, and a tracer-code epic
  outline ready for spec-decomposition. Do NOT use for: deciding
  individual technical trade-offs inside the SPEC (use
  architectural-decisions), turning an existing SPEC into GitHub issues
  (use spec-decomposition), designing a fresh net-new Android app where
  no source app exists to mirror, Android-to-Apple ports, or web /
  desktop ports.
metadata:
  author: Geoff
  version: 1.0.0
---

# Apple → Android Port SPEC

Turn an existing Apple app into a single authoritative SPEC that an agent (or the Ralph loop, via `spec-decomposition`) can decompose and implement on Android without ambiguity. The SPEC's job is to make every behavior, algorithm, asset, and constraint of the original app **provable and traceable** in the Android port — not to redesign the product.

This skill assumes a real source app exists at a knowable path. It produces one file: `plans/SPEC.md` in the target repository.

## Instructions

### Step 1: Confirm scope and the platform pair

Before reading any code, confirm three things — interactively if not already obvious from the request. Use `AskUserQuestion` for anything genuinely ambiguous; do not guess.

1. **Platform pair.** Which Apple platform is the source (iOS / macOS / watchOS / iPadOS / tvOS) and which Android target (phone / Wear OS / Android TV / Auto)? The tech mapping changes for each pair (e.g., watchOS → Wear OS uses Compose for Wear OS, not Compose Material 3).
2. **Parity vs scope change.** Is this a **strict parity port** (everything that works in the original works identically), a **reduced port** (drop X, Y, Z), or an **expanded port** (parity plus new features)? Default assumption is strict parity — confirm explicitly if otherwise.
3. **Hidden / feature-flagged code.** Does the source contain feature-flagged code paths (IAP, A/B, work-in-progress UI)? Decide whether the port preserves the flag (recommended for traceability) or strips the dead code.

Capture the answers in the SPEC's "Goals / Non-goals" section verbatim.

### Step 2: Deep-inventory the source app *before* writing

Do not draft a single SPEC sentence until you have a complete inventory of the source. The most common failure mode is writing the SPEC from the request rather than from the code, then discovering missed screens / utilities / constants halfway through implementation.

Read every source file. For each: file path + tight description + any non-obvious behavior. Specifically collect:

- App entry, scene/window setup, persistence container wiring, navigation root, tab/page structure.
- Every screen / View / ViewController — what it shows, what it accepts as input, every user interaction, every state it holds, every navigation it triggers, every animation/haptic/sound it fires.
- Every ViewModel / Presenter / Controller — `@Published` / `@State` / observable properties, public methods, dependencies (protocols), error paths.
- Every model and persistence class (SwiftData `@Model`, Core Data entities, `Codable` structs) — every field + type + constraints + computed properties + fallbacks.
- Every repository / data source — load paths, validation rules, error types, fallbacks.
- Every utility (RNG, storage, sanitizer, formatters, extensions) — quote the actual logic.
- Every configuration constant (thresholds, timeouts, limits, feature flags) — exact values.
- Every component (buttons, cells, custom shapes) — what they render and accept.
- Every bundled resource — JSON schemas, image asset naming conventions (and counts), audio, fonts, plist data.
- Every test target and test file category — what's covered, what isn't.
- CI, pre-commit, build scripts, project conventions in `CLAUDE.md` / `AGENTS.md` / `README.md`.
- Any App Intents / Siri Shortcuts / Widgets / Complications — these are the trickiest to port cleanly.

For large source apps delegate this step to an `Explore` sub-agent with an exhaustive prompt; do not skim. See `references/inventory-checklist.md` for the full checklist.

### Step 3: Extract product invariants

From the inventory, identify what **must not change** in the port. These are usually unwritten — the engineer who wrote the original encoded them in code, not docs. Common categories:

- **Offline / network posture** (e.g., "no network calls, ever").
- **Cryptographic guarantees** (CSPRNG vs PRNG, signing, hashing).
- **Algorithmic invariants** (no-repeat, idempotency, sort stability).
- **UX timing** (minimum animation durations for anticipation; "instant" thresholds).
- **Capacity / storage policies** (warning thresholds, prune sizes).
- **Privacy posture** (what does the app NOT collect / track).
- **Watch-only / phone-only architecture** (a "watch-only" Apple app usually wants to stay watch-only on Wear OS — adding a phone module is scope creep).
- **Feature-flagged UI that must remain hidden.**

Each invariant becomes a non-negotiable line item in the SPEC.

### Step 4: Draft Goals and Non-goals explicitly

Non-goals are often more valuable than goals, because they prevent scope drift mid-implementation. Common Apple→Android non-goals:

- Phone companion module (when the source is watch-only).
- Siri / Shortcuts voice fidelity (no exact Android equivalent; partial via Tile/complication).
- iCloud sync, App Clips, Live Activities, Lock Screen widgets without Android equivalents.
- Net-new features not in the original.

Write the goals/non-goals before drafting any technical mapping. They constrain everything below.

### Step 5: Build the technology mapping table (the spine)

The single most useful section of the SPEC. One row per concern, three columns: **Concern | Source (Apple) | Port (Android)**. Include language, UI framework, min platform, navigation, persistence, async/state, DI, bundled data, image assets, RNG, haptics, storage stats, dates, App Intent equivalent, build system, unit tests, UI tests, lint/format, coverage.

For each row, cite a **default choice** (e.g., "kotlinx.serialization, manual constructor DI, StateFlow, drawable resources, SecureRandom"). If the user has a strong opinion or there's a real tradeoff, flag it as a deferred decision in §Open questions.

Full mapping tables for `iOS → Android phone` and `watchOS → Wear OS` (the two most common pairs) live in `references/platform-mapping.md`. Adapt the rows to the specific pair; do not invent mappings.

### Step 6: Mirror the project structure 1:1

Propose a Kotlin/Gradle project layout whose package tree mirrors the source package tree. Same names where they make sense (`CardDrawViewModel` → `CardDrawViewModel.kt`). This preserves traceability — every Swift file has a known Kotlin counterpart, and reviewers can A/B with the original.

### Step 7: Specify every screen and every ViewModel

For each screen: **what it displays**, **user interactions** (taps, swipes, long-presses, digital crown / rotary input on Wear), **navigation transitions**, **animations**, **state held**, **dependencies injected**. Describe the user flow start-to-finish for the core loop in numbered steps.

For each ViewModel: **state shape** (list every `@Published`/`StateFlow` property), **public methods** (signature + behavior + cancellation/error handling), **private dependencies** (interfaces — never concrete types).

### Step 8: Specify the data layer + asset pipeline

- **Domain models**: each field, type, computed properties, fallback objects (emergency single-item decks, default config).
- **Persistence**: entity columns 1:1 with the source SwiftData/Core Data model, DAO queries (with limits and sort orders), database init resilience (recreate-on-failure, in-memory fallback if the on-disk DB is corrupt).
- **Repositories**: load paths, validation rules quoted from source, exact error types.
- **JSON / bundled data**: schema, reuse verbatim if possible. State explicitly that the file is copied unchanged.
- **Image / audio assets**: naming convention (e.g., `major_00` … `major_21`), source location (`@1x/@2x/@3x` in Asset Catalog), target location (`drawable-mdpi/-xhdpi/-xxxhdpi` or `assets/`). Include a build-time integrity test ("every referenced name resolves to a real resource").

### Step 9: Quote core algorithms verbatim

The most ported-wrong category. For each non-obvious algorithm (RNG selection, no-repeat sets, sanitization rules, threshold math, debouncing, prune logic): quote the source code (Swift), then sketch the Kotlin port. Preserve cancellation semantics, error paths, edge cases. Don't paraphrase; **quote**.

### Step 10: Specify Android-platform concerns

The single largest source of "we forgot about this" issues mid-implementation. Cover:

- **Manifest**: `<uses-feature>`, `<uses-permission>`, `<meta-data android:name="com.google.android.wearable.standalone">`, target/min SDK.
- **Wear OS specifics** (if applicable): `TimeText`, `Vignette`, `ScalingLazyColumn`, swipe-to-dismiss + pager gesture conflict, round vs square vs small-screen layouts, complications/tiles.
- **Phone specifics** (if applicable): edge-to-edge, predictive back, dark theme support.
- **Play Store**: data safety form contents, privacy policy URL (if any), target SDK timeline.
- **Device matrix to test**: list specific devices/form factors (e.g., Galaxy Watch 7 44mm, Pixel Watch 2, Wear OS emulator round 320×320).

### Step 11: Specify testing, CI, accessibility, performance — as checklists

Not prose. Discrete bullets so reviewers can audit each.

- **Test parity matrix**: one row per source test category (unit / UI / asset integrity / statistical / property-based), mapped to the Android equivalent (JUnit5 / Compose UI test / instrumented / Kover / Turbine).
- **Coverage gates**: overall + per-layer (models 95–100%, ViewModels 95–100%, utilities 95–100%, repos 90+%, components 60+%, screens via UI tests).
- **Accessibility checklist**: every interactive surface has a content description / semantics label; TalkBack-tested; minimum touch targets; dynamic font scaling; high-contrast.
- **Performance budgets**: per-surface targets (e.g., "card draw < 100ms cold", "view transition < 50ms", "image render < 16ms from drawable").
- **Localization**: scope explicit ("English only in v1" is a valid answer — just write it down).

### Step 12: Risk register

A short table of known risks for this specific port, each with a mitigation. Examples:

- Memory pressure from 78 high-res PNGs on a watch → load on demand, size to displayed bounds, test on a low-end device.
- Pager vs swipe-to-dismiss gesture conflict on Wear → prototype in Epic 1.
- Storage API differences (StatFs returns 0 in some emulator configs) → wrap and unit-test boundaries.
- App Intent → Tile is a partial map (no voice) → document the gap, do not pretend it's 1:1.

### Step 13: Outline decomposition epics (tracer-code ordered)

5–9 epics. The **first epic must be the project skeleton + CI green on an empty module** so every later epic preserves a demoable system. Subsequent epics follow tracer-code: data layer → core loop → secondary screens → polish → flag-gated future work.

This outline is what `spec-decomposition` consumes next. Each epic gets a 1-line description and a 1-line "Done-Done shape." Do not write the per-issue prompts here — that's spec-decomposition's job.

### Step 14: Close with the contract artifacts

- **Definition of done** — checklist that proves parity ("all source screens exist and match behavior; 78 cards load offline; CSPRNG no-repeat invariant verified by tests; CI green; coverage ≥ floor").
- **Source-of-truth file map** — a 2-column table mapping every source file to its target Kotlin counterpart. Reviewers use this to A/B.
- **Open questions to resolve during decomposition** — explicit list of decisions deferred (asset density bucket strategy, DI framework choice, Wear navigation primitive). Each is a 1-line bullet.

### Step 15: Final review against the SPEC quality bar

Before handing off, audit the draft:

- [ ] Every source file appears either in the source-of-truth file map or in a documented non-goal.
- [ ] Every product invariant from Step 3 has a "must not violate" line in the SPEC.
- [ ] Every algorithm with non-trivial logic is quoted from source (not paraphrased).
- [ ] The technology mapping table has a row for every concern listed in `references/platform-mapping.md`.
- [ ] Goals and non-goals are explicit and surveyed by the user (Step 1 answers).
- [ ] Tests-and-CI section is checklist-shaped, not prose.
- [ ] Epic outline starts with a skeleton epic that builds + CI-greens on its own.
- [ ] Open questions are real questions, not placeholders for missing work.

Use the full skeleton in `references/spec-template.md` as the section scaffold. Fill it; do not invent new top-level sections without reason.

## Examples

### Example 1: watchOS → Wear OS port (the canonical case)

User says: "Port this watchOS tarot app to Wear OS." The source is a SwiftUI + SwiftData app with bundled JSON, 78 card images, MVVM, an App Intent, and Siri Shortcuts.

1. **Step 1**: Confirm parity port; confirm Wear OS standalone (no phone module); confirm hidden multi-deck feature flag stays hidden.
2. **Step 2**: Delegate inventory to an `Explore` agent with a thorough prompt. Get back a complete file list + per-file description.
3. **Steps 3–4**: Invariants — offline, CSPRNG, no-repeat-until-exhausted, 80% storage threshold, 500ms suspense, multi-deck hidden. Non-goals — phone module, Siri voice fidelity, App Clips.
4. **Step 5**: Use `references/platform-mapping.md` "watchOS → Wear OS" table. SwiftUI→Compose for Wear OS, SwiftData→Room, `SystemRandomNumberGenerator`→`SecureRandom`, `WKInterfaceDevice.play(.click)`→`VibrationEffect`, AppIntent → Wear OS Tile (document the voice gap).
5. **Steps 7–9**: Per-screen flow + each ViewModel's state shape + verbatim quote of `selectRandomCard` and `NoteInputSanitizer.sanitize`.
6. **Step 10**: Manifest declares `uses-feature watch` + `standalone=true`; VIBRATE permission; round/square/small-screen test matrix.
7. **Step 13**: 9 epics — skeleton & CI, data layer, draw experience, history, notes, reference browser, theming/a11y, Tile + quick-launch, flag-gated multi-deck.
8. **Step 14**: Source-of-truth map: `Views/DrawCardView.swift` → `ui/draw/DrawCardScreen.kt`, etc.

### Example 2: iOS phone → Android phone (productivity app)

Source is a UIKit + Core Data productivity app with cloud sync via CloudKit, Push notifications, a Today Widget, and a Shortcut Action.

1. **Step 1**: Confirm parity *minus* CloudKit (no Android equivalent without a real backend); user agrees to "no cross-device sync in v1, file as future work."
2. **Step 4**: Non-goals get "Today Widget → Android App Widget is a partial map; defer to v1.1." CloudKit deferred.
3. **Step 5**: Mapping table uses `references/platform-mapping.md` "iOS → Android phone" rows: UIKit→Jetpack Compose (or Views if more pragmatic), Core Data→Room, NSPersistentCloudKitContainer→(out of scope, see non-goals), `UNUserNotificationCenter`→`NotificationManager` + WorkManager, Shortcut Action → App Action (App Actions SDK or deep-link intent).
4. **Step 10**: `POST_NOTIFICATIONS` runtime permission (API 33+), notification channels, edge-to-edge, predictive back.
5. **Step 13**: Skeleton + CI; data layer + Room + migration from Core Data export (if needed); core task list; notifications; settings; widgets (flagged for v1.1).

### Example 3: When the source app isn't fully analyzable yet

User says "Port this iOS app to Android" but the source repo has no `CLAUDE.md`, no README, and 300 Swift files. The risk of writing a SPEC from incomplete understanding is high.

Stop. Run the inventory anyway, but produce a **two-document deliverable**:

1. `plans/INVENTORY.md` — the raw inventory (every file, every screen, every ViewModel), explicitly marked as "machine-generated, please verify."
2. `plans/SPEC.md` — the SPEC, but with **explicit "assumes the inventory is correct" notes** in any section that depended on inferences. Open questions includes "review INVENTORY.md and flag misreads."

This makes the gap visible instead of hiding it inside prose.

## Troubleshooting

### Error: The SPEC describes behavior the source app doesn't actually have

Usually caused by writing the SPEC from the user's request rather than from the code. Fix: re-do Step 2 (deep inventory) against the actual source and reconcile. Any behavior in the SPEC must be traceable to a file/line in the source. If a behavior is *desired* but not in the source, it's a goal-change — surface it explicitly in Goals.

### Error: The tech mapping table has gaps ("we'll figure it out later")

Gaps in the mapping table become decomposition-time crises. Fix: for every gap, either (a) pick a default and add a deferred-decision note in §Open questions, or (b) escalate to `architectural-decisions` skill for one row. Do not ship a SPEC with a blank row.

### Error: The user keeps asking "but what about X?" after handoff

Means non-goals were too thin. Fix: regenerate the non-goals section explicitly listing every feature in the source that won't port and why, plus every adjacent feature the user *might* expect but isn't in scope. Non-goals should answer the awkward questions before they're asked.

### Error: The epic outline isn't tracer-code (later epics break the skeleton)

A common smell is "Epic 1: data layer, Epic 2: UI" — Epic 1 doesn't render anything, so the system isn't demoable. Fix: make Epic 1 the skeleton that builds + launches + CI-greens + shows stub UI for every top-level destination. Subsequent epics replace stubs with real implementations one vertical at a time. See the `tracer-code` skill for the canonical pattern.

### Error: SPEC is over-prescriptive, fights the Android-idiom

If every row of the mapping table says "do it exactly like Apple did it," the port will be un-idiomatic and unmaintainable. Fix: distinguish **product invariants** (must not change — list explicitly in §Invariants) from **implementation choices** (the Android-idiom can and should override). The SPEC fixes the *what*; the implementer chooses the *how* unless an invariant says otherwise.
