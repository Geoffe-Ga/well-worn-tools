# Apple → Android Platform Mapping Tables

Canonical mapping rows for the two most common port pairs. Use these as the
spine of the SPEC's "Technology mapping" section. **Adapt rows to the actual
platform pair**; do not invent mappings.

Each cell suggests a **default** choice. The default is a starting point, not a
mandate — flag any deferred choice in the SPEC's §Open Questions.

---

## watchOS → Wear OS

| Concern | watchOS (source) | Wear OS (port) — default |
|---|---|---|
| Language | Swift 5.9+ | **Kotlin** (latest stable) |
| UI framework | SwiftUI (watchOS 10+) | **Jetpack Compose for Wear OS** (`androidx.wear.compose:*`) |
| Min platform | watchOS 10.0 | **Wear OS 4 / API 33** (acceptable `minSdk` 30, target latest) |
| App entry / scene | `@main App` + `WindowGroup` | `ComponentActivity` + `setContent { WearApp() }` |
| Navigation | `TabView(.page)` (swipe tabs) | **`HorizontalPager`** (Wear Compose) or `SwipeDismissableNavHost` + pager |
| Persistence | **SwiftData** (`@Model`, `ModelContext`) | **Room** (`@Entity`, `@Dao`, `RoomDatabase`) |
| Async | `async/await`, `@MainActor` | Kotlin **coroutines** + `Dispatchers.Main`/`viewModelScope`, `Flow` |
| State / VM | `ObservableObject` + `@Published` | `ViewModel` + `StateFlow`/`MutableStateFlow` (Compose `mutableStateOf` for view-local) |
| DI | Protocol-based manual injection | Interfaces + constructor injection; **manual `AppContainer`** (Hilt only if justified) |
| Bundled data | JSON in bundle, decoded via `Codable` | Same JSON in `res/raw/` (or `assets/`), decoded via **kotlinx.serialization** |
| Images | Asset Catalog imagesets (@1x/2x/3x) | **drawable resources** (`drawable-mdpi/-xhdpi/-xxxhdpi`) or `assets/`; name-stable |
| CSPRNG | `SystemRandomNumberGenerator` | `java.security.SecureRandom` (wrapped behind a `RandomGenerator` interface) |
| Haptics | `WKInterfaceDevice.current().play(.click)` | `Vibrator`/`VibratorManager` + `VibrationEffect`, or Wear `HapticFeedback` |
| Storage stats | `FileManager.attributesOfFileSystem` | `StatFs(filesDir.path)` or `StorageManager` |
| Date formatting | `DateFormatter` (medium/short) | `java.time` + `DateTimeFormatter.ofLocalizedDate*` |
| Siri / App Intent | `AppIntent` ("Draw a card") | **Wear OS Tile** + optional complication / quick-launch shortcut (no voice equivalent — document the gap) |
| Build | Xcode project | **Gradle (Kotlin DSL)**, single `:app` (or `:wear`) module |
| Unit tests | XCTest / Swift Testing | **JUnit5** + **MockK** + **Turbine** (Flow) + Robolectric where needed |
| UI tests | XCUITest | **Compose UI test** (`createAndroidComposeRule`) + (optional) UiAutomator |
| Lint/format | SwiftLint + SwiftFormat | **ktlint** + **detekt** + Android Lint |
| Coverage | `xccov` | **Kover** (or JaCoCo) |
| Watch metadata | watchOS-only target | `AndroidManifest.xml`: `<uses-feature android.hardware.type.watch>` + `<meta-data com.google.android.wearable.standalone value="true"/>` |

**Test matrix to demand in the SPEC** (Wear OS): round large, round small (chin),
square, low-end (Galaxy Watch 4/5 class), high-end (Pixel Watch 2 / Galaxy Watch 7).

---

## iOS → Android phone

| Concern | iOS (source) | Android phone (port) — default |
|---|---|---|
| Language | Swift 5.9+ | **Kotlin** (latest stable) |
| UI framework | SwiftUI / UIKit | **Jetpack Compose** (Material 3); legacy Views only if the source is heavily UIKit and a 1:1 widget port is cheaper |
| Min platform | iOS 16 / 17 | **`minSdk` 26 (default)** or 24; target latest stable |
| App entry | `@main App` + `WindowGroup` / `SceneDelegate` | `Application` subclass + `ComponentActivity` + `setContent` |
| Navigation | `NavigationStack`, `NavigationSplitView`, `TabView` | **`NavController`** + Compose Navigation (`NavHost`) |
| Persistence | SwiftData / Core Data | **Room** (or SQLDelight if the source uses raw SQL) |
| Cloud sync | CloudKit / `NSPersistentCloudKitContainer` | **No 1:1 equivalent** — defer to a real backend or document as non-goal |
| Async | `async/await`, structured concurrency, `@MainActor` | Kotlin **coroutines** + `Dispatchers`, `Flow`, structured concurrency via `viewModelScope` |
| State / VM | `ObservableObject` + `@Published`, `Observation` | **`ViewModel`** + `StateFlow`/`SharedFlow`; Compose `mutableStateOf` for local UI state |
| DI | Manual / `Environment` / Resolver | **Hilt** (idiomatic for phone) or manual `AppContainer` |
| Networking | `URLSession`, `async` | **OkHttp + Retrofit** (REST) or **Ktor** (multiplatform) |
| Serialization | `Codable` | **kotlinx.serialization** (default) or Moshi |
| Images | Asset Catalog, `Image(systemName:)` | **drawable / vector** resources; `Image(painterResource(R.drawable.x))`; SF Symbols → Material Symbols |
| Notifications | `UNUserNotificationCenter` | **`NotificationManager`** + channels + `POST_NOTIFICATIONS` runtime permission (API 33+); `WorkManager` for scheduling |
| Background work | `BGProcessingTask`, `URLSessionDownloadTask` | **`WorkManager`** (`OneTimeWorkRequest` / `PeriodicWorkRequest`) |
| Siri / Shortcut Action | `AppIntent` + `AppShortcutsProvider` | **App Actions** (App Actions SDK + `shortcuts.xml`) or deep-link intent + `AssistantAppContent` |
| Today Widget / Lock Screen widget | `WidgetKit` | **App Widget** (`RemoteViews`) or Glance (Compose-style); not a 1:1 map |
| Live Activities | `ActivityKit` | **Foreground Service notification** (closest analogue; no Dynamic Island equivalent) |
| In-app purchase | StoreKit 2 | **Google Play Billing Library 6+** |
| Sign in with Apple | `ASAuthorizationController` | Sign in with Google / Credential Manager — *user-visible product change*, confirm in goals |
| Date formatting | `DateFormatter`, `RelativeDateTimeFormatter` | `java.time` + `DateTimeFormatter` + `DateUtils.getRelativeTimeSpanString` |
| Build | Xcode project | **Gradle (Kotlin DSL)** + version catalog `gradle/libs.versions.toml` |
| Unit tests | XCTest / Swift Testing | **JUnit5** + MockK + Turbine + Robolectric |
| UI tests | XCUITest | **Compose UI test** + Espresso (for legacy Views) |
| Lint/format | SwiftLint + SwiftFormat | **ktlint** + **detekt** + Android Lint |
| Coverage | `xccov` | **Kover** (or JaCoCo) |
| Distribution | TestFlight + App Store | **Internal/closed/open testing** + Play Store |
| Privacy | App Store privacy "nutrition" labels | **Play Data Safety form** (re-declare from scratch; the two systems are not interchangeable) |

**Test matrix to demand in the SPEC** (phone): small phone (Pixel 6a class), large
phone (Pixel 8 Pro / Galaxy S24 Ultra), foldable inner+outer display if relevant,
tablet (if scope), dark + light theme, API minSdk + targetSdk runtime.

---

## Other Apple→Android pairs (brief)

- **macOS → Android tablet / ChromeOS**: SwiftUI → Compose; AppKit → Compose for Desktop is *not* the right move (target is Android). Treat as iOS-tablet port.
- **iPadOS → Android tablet / foldable**: same as iOS row, plus `WindowSizeClass`-aware Compose layouts.
- **tvOS → Android TV**: SwiftUI → **Compose for TV** (`androidx.tv:tv-foundation`/`tv-material`); focus-driven navigation; D-pad input; leanback-style lists.

---

## Cross-cutting non-portable categories (call out as non-goals)

These have no faithful 1:1 Android map. Document explicitly so they don't ambush
implementation:

- Siri voice fidelity → partial via App Actions / Tile, no voice phrase parity.
- iCloud / CloudKit sync → requires a real backend; not a code port.
- Sign in with Apple → user-visible change to Google / Credential Manager.
- HealthKit → Health Connect; field-level mapping is not 1:1.
- HomeKit → Google Home / Matter; not a code port.
- App Clips → Instant Apps (deprecated direction); usually drop.
- Dynamic Island / Live Activities → no equivalent; foreground notification is the closest.
- ARKit → ARCore; the rendering APIs differ enough that this is a rewrite, not a port.
