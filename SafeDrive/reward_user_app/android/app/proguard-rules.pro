# Flutter Wrappers
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.**  { *; }
-keep class io.flutter.util.**  { *; }
-keep class io.flutter.view.**  { *; }
-keep class io.flutter.**  { *; }
-keep class io.flutter.plugins.**  { *; }

# Google Play Services
-keep class com.google.android.gms.** { *; }
-dontwarn com.google.android.gms.**
-keep class com.google.firebase.** { *; }
-dontwarn com.google.firebase.**

# Prevent obfuscating generic types
-keepattributes Signature
-keepattributes *Annotation*
-keepattributes EnclosingMethod

# R8/Proguard rules for Flutter plugins
-keep class com.google.crypto.tink.** { *; }
-dontwarn com.google.crypto.tink.**
