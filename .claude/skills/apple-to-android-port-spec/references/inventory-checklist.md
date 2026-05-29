# Deep-inventory checklist (run BEFORE writing the SPEC)

The single most common SPEC failure is writing from the user's request rather
than from the actual source code. This checklist guards against that. Complete
every box before drafting any SPEC section.

For source apps larger than ~30 files, **delegate this checklist to an
`Explore` sub-agent** with a prompt that names every category below. Skimming
is the failure mode.

---

## Read first

- [ ] `README.md`, `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md` — house rules and conventions.
- [ ] `.swiftlint.yml`, `.swiftformat`, `.pre-commit-config.yaml` — quality bar.
- [ ] `.github/workflows/*.yml` — CI shape (build/test/coverage).
- [ ] Build files (`*.xcodeproj`/`*.xcworkspace`/`Package.swift`) — targets, deps, platforms.
- [ ] `scripts/` — any custom test/asset/build scripts.

## App entry & navigation

- [ ] `@main App` (or `AppDelegate`/`SceneDelegate` for UIKit) — scene setup, persistence container wiring, launch arguments (e.g., `--uitesting`).
- [ ] Root view / window / scene — initial route, navigation primitives.
- [ ] Tab / page structure — every top-level destination and its default index.
- [ ] Persistence container init — SwiftData `Schema`, Core Data model, fallback/recovery behavior on corrupt DB.

## Every screen / View / ViewController

For each, capture:
- [ ] File path.
- [ ] What it displays (text, images, controls, lists).
- [ ] Every user interaction (tap, swipe, long-press, digital crown / rotary, drag, pinch).
- [ ] Every navigation transition triggered (sheet / fullScreenCover / push / dismiss / programmatic deep link).
- [ ] Every animation (durations, easings, transitions).
- [ ] Every haptic / sound / vibration.
- [ ] Every state held (`@State`, `@StateObject`, `@Binding`, `@Environment`).
- [ ] Every dependency injected (which protocol-typed properties).
- [ ] Empty state, loading state, error state.
- [ ] Accessibility labels and hints.

## Every ViewModel / Presenter / Controller

For each:
- [ ] File path + `@MainActor` / `final class` / actor isolation.
- [ ] Every `@Published` / `@Observable` property and its type.
- [ ] Every public method (signature + behavior + cancellation + error paths).
- [ ] Every private dependency (which protocols — never concrete types).
- [ ] Any session-scoped state (in-memory sets, caches, debounce timers).
- [ ] Any cross-cutting side effects (haptics, analytics, system APIs).

## Every model + persistence type

- [ ] SwiftData `@Model` / Core Data `NSManagedObject` / `Codable` struct.
- [ ] Every field, type, `@Attribute` modifiers (`.unique`, `.externalStorage`), default values.
- [ ] Every relationship (cascade / nullify, inverse).
- [ ] Every computed property + any derived display logic.
- [ ] Fallback/emergency instances (single-item decks, default config) used on load failure.

## Repositories / data sources

- [ ] Load path (which bundle resource, which URL, which file system path).
- [ ] Decoding (`Codable`, JSON schema).
- [ ] **Validation rules** — quote them verbatim (count checks, non-empty fields, ID format).
- [ ] Every error type and what fires it.
- [ ] Every fallback (e.g., fallback deck when JSON is malformed).
- [ ] Query limits, sort orders, predicates.

## Utilities

- [ ] RNG wrappers — exact algorithm (CSPRNG vs PRNG), seeding behavior.
- [ ] Sanitizers — exact rules (regex / character filters / length caps / collapse rules).
- [ ] Storage / capacity monitors — threshold values, source of "free space" (`FileManager` keys), error behavior.
- [ ] Date / number formatters — locale handling, style.
- [ ] Extensions on `Date`, `Image`, `String`, etc. — what they add.

## Configuration constants

- [ ] Thresholds (storage, history caps, retry counts).
- [ ] Timeouts (minimum animation durations, debounce intervals).
- [ ] Limits (note length, list display caps).
- [ ] Default IDs / names (default deck, default theme).
- [ ] **Feature flags** — every flag, its current value, what it gates.

## Components (reusable UI)

- [ ] Custom buttons, cards, rows, layouts.
- [ ] What they render and what they accept.
- [ ] Any state or animation they hold.
- [ ] Accessibility behavior.

## Bundled resources

- [ ] JSON files — schema (every key, type, nesting) + record count + size.
- [ ] Image asset catalogs — naming convention + count + scales (`@1x/@2x/@3x`) + idioms.
- [ ] Audio / fonts / Lottie / video.
- [ ] App icon, complication assets, widget previews.
- [ ] `Info.plist` keys — privacy strings, capabilities, URL schemes, background modes.

## App Intents / Shortcuts / Widgets / Complications

The hardest category to port faithfully. For each:
- [ ] Intent name and parameters.
- [ ] What it does in-app vs in-background.
- [ ] Voice phrases (`AppShortcutsProvider`).
- [ ] Widget kind, sizes supported, refresh policy.
- [ ] Complication families, refresh policy.

These rarely map 1:1 on Android — note the gap clearly so the SPEC can flag it.

## Tests + coverage

- [ ] Test target structure (unit / UI / integration).
- [ ] Coverage gates in CI.
- [ ] Mock patterns (protocol fakes vs Mockingbird vs hand-rolled).
- [ ] Statistical / property-based tests (Hypothesis-style).
- [ ] UI test conventions (page-object style? accessibility-id reliance?).
- [ ] What's intentionally **not** tested (per `COVERAGE_GAPS.md` or similar).

## CI + automation

- [ ] What CI runs (build, test, lint/format, coverage).
- [ ] On which simulator/device matrix.
- [ ] Any custom GitHub Actions or scripts (e.g., `run-tests.sh`).
- [ ] Any agent loops (Ralph, claude-code-review, iteration-trigger).

## Repo conventions worth preserving

- [ ] Commit message style.
- [ ] Branch naming.
- [ ] PR template.
- [ ] Anti-bypass / max-quality rules already documented.

---

## Output of this checklist

A document (in your scratch space — *not* the SPEC yet) that lists, per
category above, every file with a tight description. This becomes the input to
the SPEC's Source-of-truth file map (Appendix A of the SPEC template), and it's
what you cross-reference in Step 15's final review ("every source file appears
either in the source-of-truth file map or in a documented non-goal").
