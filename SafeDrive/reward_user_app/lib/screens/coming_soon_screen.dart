import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';

class ComingSoonScreen extends StatelessWidget {
  final bool isDarkMode;

  const ComingSoonScreen({super.key, this.isDarkMode = false});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: isDarkMode ? const Color(0xFF0F172A) : const Color(0xFFF5F7FA),
      body: SafeArea(
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // 2️⃣ CENTER ICON
              Icon(
                Icons.construction, // Using material construction icon as requested
                size: 120,
                color: AppColors.constructionIcon,
              ),
              
              const SizedBox(height: 16),
              
              // 3️⃣ TITLE TEXT
              Text(
                "Coming Soon",
                style: GoogleFonts.poppins(
                  fontSize: 20,
                  fontWeight: FontWeight.w500,
                  color: AppColors.textSecondarySolid,
                ),
              ),
              
              // 4️⃣ OPTIONAL SUBTEXT (Included as per spec)
              /* 
              const SizedBox(height: 8),
              Text(
                "This feature is under development",
                style: GoogleFonts.poppins(
                  fontSize: 14,
                  color: AppColors.textTertiary,
                ),
              ),
              */
            ],
          ),
        ),
      ),
    );
  }
}
