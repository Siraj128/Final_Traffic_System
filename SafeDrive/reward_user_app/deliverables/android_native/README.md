# SafeDrive Rewards - Android Native Assets

This folder contains the **Native Android** implementation of the "Coming Soon" screen, as requested.

## 📂 Contents

### 1. Jetpack Compose (Kotlin)
- **File**: `ComingSoonScreen.kt`
- **Description**: Full Jetpack Compose implementation.
- **Components**:
  - `ComingSoonScreen`: The main UI layout.
  - `BottomNavBar`: Custom gradient navigation bar.
  - `ScanFAB`: Floating action button with gradient.
  - `AppTheme`: Color palette and theme constants.

### 2. XML Layout (Legacy/View System)
- **File**: `res/layout/activity_coming_soon.xml`
- **Description**: Standard XML layout version (Optional).
- **Resources**:
  - `res/drawable/ic_construction.xml`: Vector icon.

## 🚀 How to Use

### Jetpack Compose
Copy the code from `ComingSoonScreen.kt` into your Android project's `ui` package. Call `MainScreen()` from your `MainActivity`'s `setContent` block.

```kotlin
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MainScreen()
        }
    }
}
```

### XML Layout
Copy the `res` folders into your `src/main/res` directory. Inflate `activity_coming_soon.xml` in your Activity.
