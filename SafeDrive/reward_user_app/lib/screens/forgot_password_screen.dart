import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/auth_service.dart';
import '../constants/app_colors.dart';
import 'otp_screen.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _emailController = TextEditingController();

  void _sendResetCode() async {
    if (_emailController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please enter your email")));
      return;
    }

    // Call Backend
    // Call Backend (Using RTO Email OTP for Reset)
    // Passing 'RESET-PWD' as dummy plate to satisfy API
    final response = await AuthService.sendRtoEmailOtp(_emailController.text.trim(), "RESET-PWD");

    if (response.containsKey('msg')) {
        // Success (Backend returns { msg: 'OTP sent...' })
        if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(response['msg'])));
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => OtpScreen(
                  destination: _emailController.text.trim(),
                  onVerified: () {
                    Navigator.popUntil(context, (route) => route.isFirst);
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("OTP Verified. Password Reset Successful.")));
                  },
                ),
              ),
            );
        }
    } else {
        if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(response['message'] ?? "Failed to send OTP")));
        }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new_rounded, color: isDark ? Colors.white : AppColors.primaryDark),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "Forgot Password?",
              style: GoogleFonts.poppins(
                fontSize: 24, 
                fontWeight: FontWeight.bold, 
                color: isDark ? Colors.white : AppColors.primaryDark
              ),
            ),
            const SizedBox(height: 8),
            Text(
              "Don't worry! It happens. Please enter the email address linked with your account.",
              style: GoogleFonts.poppins(color: AppColors.grey),
            ),
            const SizedBox(height: 48),
            
            TextFormField(
              controller: _emailController,
              style: GoogleFonts.poppins(color: isDark ? Colors.white : AppColors.primaryDark),
              decoration: InputDecoration(
                labelText: "Email / Mobile",
                labelStyle: GoogleFonts.poppins(color: AppColors.grey),
                prefixIcon: Icon(Icons.email_outlined, color: isDark ? Colors.white70 : AppColors.grey),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: isDark ? const BorderSide(color: Colors.white10) : const BorderSide(),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: isDark ? const BorderSide(color: Colors.white10) : const BorderSide(color: Colors.grey),
                ),
                filled: true,
                fillColor: Theme.of(context).cardColor,
              ),
            ),
            
            const SizedBox(height: 32),
            
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _sendResetCode,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primaryPurple,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                child: Text("Send Code", style: GoogleFonts.poppins(fontWeight: FontWeight.bold, color: Colors.white)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
