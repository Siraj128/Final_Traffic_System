import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';
import '../constants/app_strings.dart';
import '../utils/validators.dart';
import '../services/auth_service.dart';
import '../services/wallet_service.dart';
import 'main_screen.dart';
import 'forgot_password_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _plateController = TextEditingController();
  final _passwordController = TextEditingController();
  
  bool _obscurePassword = true;
  bool _isLoading = false;

  @override
  void dispose() {
    _plateController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);
      
      try {
        String input = _plateController.text.trim();
        if (!input.contains('@')) {
          input = input.toUpperCase();
        }

        final response = await AuthService.login(
          input,
          _passwordController.text,
        );
        
        if (!mounted) return;

        if (response['success'] == true) {
          final userData = response['user'];

          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text(AppStrings.loginSuccess),
              backgroundColor: AppColors.rewardGreen,
              behavior: SnackBarBehavior.floating,
            ),
          );

          Navigator.pushAndRemoveUntil(
            context,
            MaterialPageRoute(
              builder: (context) => MainScreen(userData: userData),
            ),
            (route) => false,
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(response['message'] ?? AppStrings.loginFailed),
              backgroundColor: AppColors.violationRed,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Login Error: ${e.toString()}"),
            backgroundColor: AppColors.violationRed,
            behavior: SnackBarBehavior.floating,
          ),
        );
      } finally {
        if (mounted) {
          setState(() => _isLoading = false);
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        height: MediaQuery.of(context).size.height,
        width: double.infinity,
        color: Theme.of(context).scaffoldBackgroundColor,
        child: SingleChildScrollView(
          child: Column(
            children: [
              // Gradient Header
              Container(
                height: MediaQuery.of(context).size.height * 0.35,
                width: double.infinity,
                decoration: const BoxDecoration(
                  gradient: AppColors.primaryGradient,
                  borderRadius: BorderRadius.only(
                    bottomLeft: Radius.circular(40),
                    bottomRight: Radius.circular(40),
                  ),
                ),
                child: SafeArea(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(
                        Icons.shield_rounded,
                        size: 70,
                        color: Colors.white,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        AppStrings.appName,
                        style: GoogleFonts.poppins(
                          fontSize: 26,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      Text(
                        "Sign in to your account",
                        style: GoogleFonts.poppins(
                          fontSize: 14,
                          color: Colors.white.withValues(alpha: 0.8),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              
              // Login Card
              Transform.translate(
                offset: const Offset(0, -40),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  child: Container(
                    padding: const EdgeInsets.all(28),
                    decoration: BoxDecoration(
                      color: Theme.of(context).cardColor,
                      borderRadius: BorderRadius.circular(24),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.08),
                          blurRadius: 20,
                          offset: const Offset(0, 10),
                        ),
                      ],
                    ),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            AppStrings.loginTitle,
                            style: GoogleFonts.poppins(
                              fontSize: 18,
                              fontWeight: FontWeight.w600,
                              color: Theme.of(context).textTheme.titleLarge?.color,
                            ),
                          ),
                          const SizedBox(height: 24),
                          
                          // Vehicle Plate or Email Field
                          Text(
                            "Vehicle Number or Email",
                            style: GoogleFonts.poppins(
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                              color: AppColors.grey,
                            ),
                          ),
                          const SizedBox(height: 8),
                          TextFormField(
                            controller: _plateController,
                            decoration: InputDecoration(
                              hintText: "Enter Plate Number or Email",
                              prefixIcon: const Icon(Icons.person_rounded, size: 20, color: AppColors.primaryPurple),
                              fillColor: Theme.of(context).brightness == Brightness.dark 
                                  ? Colors.white.withValues(alpha: 0.1) 
                                  : Colors.grey.withValues(alpha: 0.05),
                            ),
                            // textCapitalization: TextCapitalization.characters, // Remove forced caps for email
                            validator: (val) {
                              if (val == null || val.isEmpty) return "Required";
                              // Simple check: if it has @, validate as email, else plate
                              if (val.contains('@')) {
                                return Validators.validateEmail(val);
                              }
                              return Validators.validatePlateNumber(val);
                            },
                          ),
                          const SizedBox(height: 20),
                          
                          // Password Field
                          Text(
                            AppStrings.passwordLabel,
                            style: GoogleFonts.poppins(
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                              color: AppColors.grey,
                            ),
                          ),
                          const SizedBox(height: 8),
                          TextFormField(
                            controller: _passwordController,
                            obscureText: _obscurePassword,
                            decoration: InputDecoration(
                              hintText: AppStrings.passwordHint,
                              prefixIcon: const Icon(Icons.lock_rounded, size: 20, color: AppColors.primaryPurple),
                              fillColor: Theme.of(context).brightness == Brightness.dark 
                                  ? Colors.white.withValues(alpha: 0.1) 
                                  : Colors.grey.withValues(alpha: 0.05),
                              suffixIcon: IconButton(
                                icon: Icon(
                                  _obscurePassword ? Icons.visibility_off_rounded : Icons.visibility_rounded,
                                  size: 20,
                                ),
                                onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                              ),
                            ),
                            validator: (val) => Validators.validateRequired(val, "Password"),
                          ),
                          
                          // Forgot Password
                          Align(
                            alignment: Alignment.centerRight,
                            child: TextButton(
                              onPressed: () {
                                Navigator.push(context, MaterialPageRoute(builder: (_) => const ForgotPasswordScreen()));
                              },
                              child: Text(
                                AppStrings.forgotPassword,
                                style: GoogleFonts.poppins(
                                  color: AppColors.primaryPurple,
                                  fontSize: 13,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 12),
                          
                          // Login Button
                          SizedBox(
                            width: double.infinity,
                            child: ElevatedButton(
                              onPressed: _isLoading ? null : _handleLogin,
                              child: _isLoading
                                  ? const SizedBox(
                                      height: 20,
                                      width: 20,
                                      child: CircularProgressIndicator(color: AppColors.white, strokeWidth: 2),
                                    )
                                  : const Text(AppStrings.loginSubmitButton),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              
              // Back Button
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text(
                  "Return to Home",
                  style: GoogleFonts.poppins(
                    color: AppColors.grey,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}
