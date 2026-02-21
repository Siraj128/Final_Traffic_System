import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lottie/lottie.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../constants/app_colors.dart';
import '../constants/app_strings.dart';
import 'login_screen.dart';
import 'register_screen.dart';
import 'main_screen.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import 'google_registration_screen.dart';

class AuthHomeScreen extends StatefulWidget {
  const AuthHomeScreen({super.key});

  @override
  State<AuthHomeScreen> createState() => _AuthHomeScreenState();
}

class _AuthHomeScreenState extends State<AuthHomeScreen> {
  bool _isGoogleLoading = false;

  Future<void> _handleGoogleOAuth() async {
    setState(() => _isGoogleLoading = true);
    
    try {
      final response = await AuthService.signInWithGoogle();
      
      if (!mounted) return;

      if (response['success'] == true) {
        // Check for New User Registration
        if (response['isNewUser'] == true) {
           Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => GoogleRegistrationScreen(googleData: response['googleData']),
            ),
          );
          return;
        }

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(AppStrings.googleLoginSuccess),
            backgroundColor: AppColors.rewardGreen,
            behavior: SnackBarBehavior.floating,
          ),
        );

        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => MainScreen(userData: response['data']),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(response['message'] ?? AppStrings.googleLoginFailed),
            backgroundColor: AppColors.violationRed,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(AppStrings.networkError),
          backgroundColor: AppColors.violationRed,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isGoogleLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final screenHeight = size.height;
    final screenWidth = size.width;

    return Scaffold(
      body: Stack(
        children: [
          // Background Image - Futuristic Highway Perspective
          Positioned.fill(
            child: Image.network(
              'https://images.unsplash.com/photo-1534067783941-51c9c23ea3cf?auto=format&fit=crop&q=80&w=1080',
              fit: BoxFit.cover,
              loadingBuilder: (context, child, loadingProgress) {
                if (loadingProgress == null) return child;
                return Container(
                  decoration: const BoxDecoration(
                    gradient: AppColors.primaryGradient,
                  ),
                );
              },
              errorBuilder: (context, error, stackTrace) => Container(
                decoration: const BoxDecoration(
                  gradient: AppColors.primaryGradient,
                ),
              ),
            ),
          ),
          
          // Dark Gradient Overlay for optimal readability
          Positioned.fill(
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.black.withOpacity(0.3),
                    Colors.black.withOpacity(0.5),
                    Colors.black.withOpacity(0.8),
                  ],
                ),
              ),
            ),
          ),
          
          SafeArea(
            child: SingleChildScrollView(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    SizedBox(height: screenHeight * 0.08),

                    // Logo with glow effect - Size increased
                    Container(
                      width: 250,
                      height: 250,
                      padding: const EdgeInsets.all(5),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: AppColors.accentBlue.withValues(alpha: 0.2),
                            blurRadius: 40,
                            spreadRadius: 2,
                          ),
                        ],
                      ),
                      child: Image.asset(
                        'assets/images/startup.png',
                        fit: BoxFit.contain,
                      ),
                    ),
                    
                    SizedBox(height: screenHeight * 0.02),
                    
                    // Tagline - Redundant Title Removed
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      decoration: BoxDecoration(
                        color: AppColors.accentBlue.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.white.withValues(alpha: 0.1)),
                      ),
                      child: Text(
                        AppStrings.appTagline,
                        textAlign: TextAlign.center,
                        style: GoogleFonts.poppins(
                          fontSize: screenWidth * 0.04,
                          color: AppColors.white.withValues(alpha: 0.9),
                          fontWeight: FontWeight.w500,
                          letterSpacing: 1.2,
                        ),
                      ),
                    ),
                    
                    SizedBox(height: screenHeight * 0.08),
                    
                    // OLD USER (Login)
                    SizedBox(
                      width: double.infinity,
                      height: 58,
                      child: Container(
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(18),
                          gradient: LinearGradient(
                            colors: [
                              AppColors.accentBlue,
                              AppColors.primaryPurple.withValues(alpha: 0.8),
                            ],
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: AppColors.accentBlue.withValues(alpha: 0.4),
                              blurRadius: 10,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: ElevatedButton(
                          onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const LoginScreen())),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.transparent,
                            foregroundColor: AppColors.white,
                            shadowColor: Colors.transparent,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                          ),
                          child: Text(
                            "EXISTING USER (LOGIN)",
                            style: GoogleFonts.poppins(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1,
                            ),
                          ),
                        ),
                      ),
                    ),
                    
                    SizedBox(height: screenHeight * 0.02),
                    
                    // NEW USER (Register)
                    SizedBox(
                      width: double.infinity,
                      height: 58,
                      child: OutlinedButton(
                        onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const RegisterScreen())),
                        style: OutlinedButton.styleFrom(
                          side: BorderSide(color: AppColors.white.withValues(alpha: 0.6), width: 1.5),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                          foregroundColor: AppColors.white,
                        ),
                        child: Text(
                          "NEW USER (SIGN UP)",
                          style: GoogleFonts.poppins(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1,
                          ),
                        ),
                      ),
                    ),
                    
                    SizedBox(height: screenHeight * 0.05),
                    
                    // OR Divider
                    Row(
                      children: [
                        Expanded(child: Divider(color: AppColors.white.withValues(alpha: 0.2))),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          child: Text(
                            "OR",
                            style: GoogleFonts.poppins(
                              color: AppColors.white.withValues(alpha: 0.4),
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                        Expanded(child: Divider(color: AppColors.white.withValues(alpha: 0.2))),
                      ],
                    ),
                    
                    SizedBox(height: screenHeight * 0.05),
                    
                    // Google Login Button (Glassmorphism)
                    SizedBox(
                      width: double.infinity,
                      height: 58,
                      child: ElevatedButton(
                        onPressed: _isGoogleLoading ? null : _handleGoogleOAuth,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.white.withOpacity(0.95),
                          foregroundColor: Colors.black87,
                          elevation: 0,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                        ),
                        child: _isGoogleLoading
                            ? SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(
                                  color: Theme.of(context).primaryColor,
                                  strokeWidth: 2,
                                ),
                              )
                            : Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Image.network(
                                    'https://www.gstatic.com/images/branding/googleg/1x/googleg_standard_color_64dp.png',
                                    height: 24,
                                    errorBuilder: (c, e, s) => Icon(
                                      Icons.g_mobiledata_rounded,
                                      color: Theme.of(context).primaryColor,
                                      size: 30,
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Text(
                                    "Continue with Google",
                                    style: GoogleFonts.poppins(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w600,
                                      color: Colors.black87,
                                    ),
                                  ),
                                ],
                              ),
                      ),
                    ),
                    
                    SizedBox(height: screenHeight * 0.04),

                    // Judge Mode / Demo Mode (Subtle)
                    TextButton(
                      onPressed: () async {
                        setState(() => _isGoogleLoading = true);
                        try {
                          final response = await AuthService.loginAsJudge();
                          if (mounted && response['success'] == true) {
                            Navigator.pushReplacement(
                              context,
                              MaterialPageRoute(builder: (context) => MainScreen(userData: response['user'])),
                            );
                          }
                        } finally {
                          if (mounted) setState(() => _isGoogleLoading = false);
                        }
                      },
                      child: Text(
                        "Demo Mode (Judge Access)",
                        style: GoogleFonts.poppins(color: Colors.white.withOpacity(0.3), fontSize: 12),
                      ),
                    ),

                    SizedBox(height: screenHeight * 0.08),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
