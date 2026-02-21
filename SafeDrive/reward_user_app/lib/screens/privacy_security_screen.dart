import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';

class PrivacySecurityScreen extends StatelessWidget {
  const PrivacySecurityScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text(
          "Privacy & Security", 
          style: GoogleFonts.poppins(
            color: isDark ? Colors.white : AppColors.primaryDark, 
            fontWeight: FontWeight.bold
          )
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new_rounded, color: isDark ? Colors.white : AppColors.primaryDark),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            _buildSection(context, "Terms of Service", "By using SafeDrive, you agree to abide by our driving data collection policies to ensure road safety..."),
            _buildSection(context, "Data Privacy", "We collect location and speed data only during active trips. Your data is encrypted and never shared with third parties without consent."),
            _buildSection(context, "Account Security", "Enable 2FA for enhanced security. You can change your password in the Edit Profile section."),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(BuildContext context, String title, String content) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        boxShadow: isDark ? [] : [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 10,
            offset: const Offset(0, 5),
          ),
        ],
        border: isDark ? Border.all(color: Colors.white10) : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title, 
            style: GoogleFonts.poppins(
              fontSize: 18, 
              fontWeight: FontWeight.bold, 
              color: isDark ? Colors.white : AppColors.primaryDark
            )
          ),
          const SizedBox(height: 8),
          Text(content, style: GoogleFonts.poppins(fontSize: 14, color: AppColors.grey, height: 1.5)),
        ],
      ),
    );
  }
}
