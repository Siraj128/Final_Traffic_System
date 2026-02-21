import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';

class HelpSupportScreen extends StatelessWidget {
  const HelpSupportScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text(
          "Help & Support", 
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
            _buildSupportOption(context, Icons.question_answer_outlined, "FAQs", "Common questions about rewards & safety"),
            _buildSupportOption(context, Icons.email_outlined, "Contact Us", "support@safedrive.com"),
            _buildSupportOption(context, Icons.phone_outlined, "Helpline", "+1 800 123 4567"),
          ],
        ),
      ),
    );
  }

  Widget _buildSupportOption(BuildContext context, IconData icon, String title, String subtitle) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
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
      child: ListTile(
        leading: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: AppColors.primaryPurple.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: AppColors.primaryPurple),
        ),
        title: Text(
          title, 
          style: GoogleFonts.poppins(
            fontWeight: FontWeight.bold, 
            fontSize: 16,
            color: isDark ? Colors.white : AppColors.primaryDark
          )
        ),
        subtitle: Text(subtitle, style: GoogleFonts.poppins(color: AppColors.grey, fontSize: 13)),
        trailing: const Icon(Icons.arrow_forward_ios_rounded, size: 16, color: AppColors.grey),
        onTap: () {
          // Mock action
        },
      ),
    );
  }
}
