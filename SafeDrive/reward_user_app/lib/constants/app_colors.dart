import 'package:flutter/material.dart';

class AppColors {
  // Modern Fintech Palette
  static const Color fintechBlue = Color(0xFF6A7BFF); // Primary Blue
  static const Color fintechCyan = Color(0xFF30B7FF); // Cyan Accent
  static const Color fintechCoral = Color(0xFFF07067); // Coral Accent
  static const Color fintechNavy = Color(0xFF13141F); // Deep Navy Base
  
  // Logical Mapping
  static const Color primaryBase = fintechBlue;
  static const Color secondaryBase = fintechCyan;
  static const Color accentBase = fintechCoral;
  static const Color darkBase = fintechNavy;

  static const Color background = Color(0xFFF8F9FE); // Very light blue-grey for contrast
  static const Color surface = Colors.white;
  
  static const Color textPrimary = fintechNavy; 
  static const Color textSecondary = Color(0xFF8A8D9F); // Cool Gray
  static const Color iconColor = fintechNavy;

  // Gradients
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [fintechBlue, fintechCyan],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  
  static const LinearGradient cardGradient = LinearGradient(
    colors: [fintechBlue, fintechNavy],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient darkGradient = LinearGradient(
    colors: [fintechNavy, Color(0xFF2B2D42)],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );

  // Rank Gradients
  static const LinearGradient platinumGradient = LinearGradient(
    colors: [Color(0xFFE5E4E2), Color(0xFFB0B0B0)], // Platinum/Metallic Silver
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  
  static const LinearGradient goldGradient = LinearGradient(
    colors: [Color(0xFFFFD700), Color(0xFFFFA500)], // Gold/Orange
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  
  static const LinearGradient silverGradient = LinearGradient(
    colors: [Color(0xFFC0C0C0), Color(0xFF808080)], // Silver/Grey
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  
  static const LinearGradient bronzeGradient = LinearGradient(
    colors: [Color(0xFFCD7F32), Color(0xFFA0522D)], // Bronze/Brown
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // Legacy/Compatibility
  static const Color white = Colors.white;
  static const Color black = Colors.black;
  static const Color grey = textSecondary;
  static const Color lightGrey = Color(0xFFE0E5EC);
  static const Color darkGrey = textPrimary;
  
  // Theme Colors
  static const Color primaryPurple = fintechBlue;
  static const Color primaryDark = fintechNavy; 
  static const Color accentBlue = fintechCyan;
  static const Color accentOutline = fintechCyan;
  
  // Dark Theme Specifics
  static const Color darkBackground = Color(0xFF0F172A);
  static const Color darkSurface = Color(0xFF1E293B);
  static const Color darkSurfaceLight = Color(0xFF334155);

  // Semantic Colors
  static const Color rewardGreen = Color(0xFF00D1FF); 
  static const Color violationRed = fintechCoral; 
  static const Color notificationBlue = fintechBlue; 
  static const Color warningYellow = Color(0xFFFFC107);
  static const Color primaryGold = Color(0xFFFFD700);
}
