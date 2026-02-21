import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';
import '../constants/app_strings.dart';
import '../utils/validators.dart';
import '../services/api_service.dart';
import '../services/session_manager.dart';
import '../services/auth_service.dart'; // [NEW] Import added
import 'main_screen.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _plateController = TextEditingController();
  final _nameController = TextEditingController();
  final _mobileController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  
  String? _selectedVehicleType;
  bool _isLoading = false;
  bool _obscurePassword = true;
  
  // [NEW] RTO Verification State
  bool _isVerified = false;


  @override
  void dispose() {
    _plateController.dispose();
    _nameController.dispose();
    _mobileController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  // [NEW] RTO Verification Logic (Email)
  Future<void> _verifyVehicle() async {
    final plate = _plateController.text.trim().toUpperCase();
    if (plate.length < 5) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Enter a valid Vehicle Number first")));
      return;
    }

    setState(() => _isLoading = true);

    // 1. Lookup RTO Email
    final rtoRes = await AuthService.lookupRtoEmail(plate);
    setState(() => _isLoading = false);

    if (rtoRes['found'] != true) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(rtoRes['message'] ?? "Vehicle not found in RTO Registry"), backgroundColor: AppColors.violationRed)
        );
      }
      return;
    }

    final maskedEmail = rtoRes['masked_email'];
    final rawEmail = rtoRes['email']; // Keep for sending OTP
    // _rtoPhone no longer used, we use email
    
    // 2. Confirm Dialog
    if (!mounted) return;
    final confirm = await showDialog<bool>(
      context: context, 
      builder: (ctx) => AlertDialog(
        title: const Text("Verify Ownership"),
        content: Text("This vehicle is registered to $maskedEmail.\n\nWe will send a verification code to this email to verify you are the owner."),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Cancel")),
          ElevatedButton(onPressed: () => Navigator.pop(ctx, true), child: const Text("Send Code")),
        ],
      )
    );

    if (confirm != true) return;

    // 3. Trigger Email OTP
    _sendOtp(rawEmail, plate);
  }

  Future<void> _sendOtp(String email, String plate) async {
    setState(() => _isLoading = true);
    
    final res = await AuthService.sendRtoEmailOtp(email, plate);
    setState(() => _isLoading = false);

    if (res['success'] == true) {
      // [DEV] If OTP is returned in response (Simulated Mode), show it
      if (res.containsKey('dev_otp')) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Dev Mode: Your OTP is ${res['dev_otp']}"),
            backgroundColor: Colors.blue,
            duration: const Duration(seconds: 10),
            behavior: SnackBarBehavior.floating,
          )
        );
      }
      _showOtpDialog(email);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Failed to send OTP: ${res['message']}"), backgroundColor: Colors.red));
    }
  }

  void _showOtpDialog(String email) {
    final otpController = TextEditingController();
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: const Text("Enter Verification Code"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text("Code sent to $email"),
            const SizedBox(height: 10),
            TextField(
              controller: otpController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: "6-digit Code", border: OutlineInputBorder()),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          ElevatedButton(
            onPressed: () async {
              final code = otpController.text.trim();
              if (code.length < 6) return;
              Navigator.pop(ctx);
              _verifyOtpCode(email, code);
            },
            child: const Text("Verify"),
          ),
        ],
      ),
    );
  }

  Future<void> _verifyOtpCode(String email, String code) async {
    setState(() => _isLoading = true);

    final res = await AuthService.verifyRtoEmailOtp(email, code);
    setState(() => _isLoading = false);

    if (res['success'] == true) {
      _onVerificationSuccess(email);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Invalid Verification Code"), backgroundColor: Colors.red));
    }
  }

  void _onVerificationSuccess(String email) {
    setState(() {
      _isLoading = false;
      _isVerified = true;
      _emailController.text = email; // Auto-fill Verified Email
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("✅ Verification Successful! Email linked."), backgroundColor: Colors.green)
    );
  }

  Future<void> _handleRegister() async {
    if (_formKey.currentState!.validate()) {
      // [NEW] Security Check
      if (!_isVerified) {
        ScaffoldMessenger.of(context).showSnackBar(
           const SnackBar(
             content: Text("🚨 You must verify the Vehicle Owner OTP first!"),
             backgroundColor: AppColors.violationRed,
           )
        );
        return;
      }

      setState(() => _isLoading = true);
      
      try {
        final response = await ApiService.register(
          ownerName: _nameController.text.trim(),
          email: _emailController.text.trim(),
          password: _passwordController.text,
          plateNumber: _plateController.text.trim().toUpperCase(),
          mobileNumber: _mobileController.text.trim(),
          vehicleType: _selectedVehicleType ?? 'Car',
        );
        
        if (!mounted) return;

        if (response['success'] == true) {
          final data = response['data'];
          final token = response['token'];

          // Save Session for Persistent Login
          if (token != null) {
            await SessionManager.saveLogin(
              email: data['email'] ?? '',
              token: token,
              name: data['owner_name'] ?? data['name'],
              plate: data['plate_number'] ?? data['vehicle_number'],
              userId: (data['driver_id'] ?? data['_id']).toString(),
              userData: data, // Save full object
            );
          }

          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text(AppStrings.registrationSuccess),
              backgroundColor: AppColors.rewardGreen,
              behavior: SnackBarBehavior.floating,
            ),
          );

          Navigator.pushAndRemoveUntil(
            context,
            MaterialPageRoute(
              builder: (context) => MainScreen(userData: data),
            ),
            (route) => false,
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(response['message'] ?? AppStrings.registrationFailed),
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
          setState(() => _isLoading = false);
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Header
            Container(
              height: 200,
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
                    Text(
                      AppStrings.registerTitle,
                      style: GoogleFonts.poppins(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      "Join the SafeDrive ecosystem",
                      style: GoogleFonts.poppins(
                        fontSize: 14,
                        color: Colors.white.withOpacity(0.8),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            // Registration Card
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
              child: Container(
                padding: const EdgeInsets.all(28),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.surface,
                  borderRadius: BorderRadius.circular(24),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.05),
                      blurRadius: 20,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                child: Form(
                  key: _formKey,
                  child: Column(
                    children: [
                      // [NEW] Vehicle Number + Verify Button
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            child: _buildFormField(
                              context: context,
                              label: AppStrings.plateNumberLabel,
                              hint: AppStrings.plateNumberHint,
                              controller: _plateController,
                              icon: Icons.directions_car_rounded,
                              validator: Validators.validatePlateNumber,
                              textCapitalization: TextCapitalization.characters,
                              readOnly: _isVerified, // Lock if verified
                            ),
                          ),
                          const SizedBox(width: 8),
                          if (!_isVerified)
                            Padding(
                              padding: const EdgeInsets.fromLTRB(0, 24, 0, 0),
                              child: ElevatedButton(
                                onPressed: _verifyVehicle,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppColors.primaryPurple,
                                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                                ),
                                child: const Text("Verify", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                              ),
                            )
                          else
                            const Padding(
                              padding: EdgeInsets.fromLTRB(0, 24, 8, 0),
                              child: Icon(Icons.check_circle, color: AppColors.rewardGreen, size: 32),
                            ),
                        ],
                      ),
                      _buildFormField(
                        context: context,
                        label: AppStrings.ownerNameLabel,
                        hint: AppStrings.ownerNameHint,
                        controller: _nameController,
                        icon: Icons.person_rounded,
                        validator: Validators.validateOwnerName,
                      ),
                      _buildFormField(
                        context: context,
                        label: AppStrings.mobileLabel,
                        hint: AppStrings.mobileHint,
                        controller: _mobileController,
                        icon: Icons.phone_android_rounded,
                        validator: Validators.validateMobileNumber,
                        keyboardType: TextInputType.phone,
                        // Mobile is distinct from RTO Email verification, keep editable
                      ),
                      _buildFormField(
                        context: context,
                        label: AppStrings.emailLabel,
                        hint: AppStrings.emailHint,
                        controller: _emailController,
                        icon: Icons.email_rounded,
                        validator: Validators.validateEmail,
                        keyboardType: TextInputType.emailAddress,
                        readOnly: _isVerified, // Lock Email after verification
                      ),
                      
                      // Vehicle Type Dropdown
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            AppStrings.vehicleTypeLabel,
                            style: GoogleFonts.poppins(
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                              color: Theme.of(context).hintColor,
                            ),
                          ),
                          const SizedBox(height: 8),
                          DropdownButtonFormField<String>(
                            value: _selectedVehicleType,
                            decoration: InputDecoration(
                              prefixIcon: const Icon(Icons.drive_eta_rounded, size: 20, color: AppColors.primaryPurple),
                              fillColor: Theme.of(context).brightness == Brightness.dark 
                                  ? Colors.white.withValues(alpha: 0.05) 
                                  : Colors.grey.withValues(alpha: 0.05),
                            ),
                            items: AppStrings.vehicleTypes.map((type) => DropdownMenuItem(
                              value: type,
                              child: Text(type, style: GoogleFonts.poppins(fontSize: 14)),
                            )).toList(),
                            onChanged: (val) => setState(() => _selectedVehicleType = val),
                            validator: Validators.validateVehicleType,
                          ),
                          const SizedBox(height: 20),
                        ],
                      ),
                      
                        _buildFormField(
                          context: context,
                          label: AppStrings.passwordLabel,
                          hint: AppStrings.passwordHint,
                          controller: _passwordController,
                          icon: Icons.lock_rounded,
                          validator: Validators.validatePassword,
                          obscureText: _obscurePassword,
                          suffixIcon: IconButton(
                            icon: Icon(
                              _obscurePassword ? Icons.visibility_off_rounded : Icons.visibility_rounded,
                              size: 20,
                              color: Theme.of(context).hintColor,
                            ),
                            onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                          ),
                        ),
                      _buildFormField(
                        context: context,
                        label: AppStrings.confirmPasswordLabel,
                        hint: AppStrings.confirmPasswordHint,
                        controller: _confirmPasswordController,
                        icon: Icons.check_circle_rounded,
                        validator: (val) => Validators.validateConfirmPassword(val, _passwordController.text),
                        obscureText: true,
                      ),
                      
                      const SizedBox(height: 12),
                      
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _handleRegister,
                          child: _isLoading
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                                )
                              : const Text(AppStrings.registerSubmitButton),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            
            // Back Button
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(
                "Cancel and Go Back",
                style: GoogleFonts.poppins(
                  color: AppColors.violationRed,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildFormField({
    required BuildContext context,
    required String label,
    required String hint,
    required TextEditingController controller,
    required IconData icon,
    String? Function(String?)? validator,
    bool obscureText = false,
    bool readOnly = false, // [NEW]
    TextInputType? keyboardType,
    TextCapitalization textCapitalization = TextCapitalization.none,
    Widget? suffixIcon,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: GoogleFonts.poppins(
            fontSize: 12,
            fontWeight: FontWeight.w500,
            color: Theme.of(context).hintColor,
          ),
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: controller,
          obscureText: obscureText,
          readOnly: readOnly, // [NEW] Use it
          validator: validator,
          keyboardType: keyboardType,
          textCapitalization: textCapitalization,
          decoration: InputDecoration(
            hintText: hint,
            prefixIcon: Icon(icon, size: 20, color: AppColors.primaryPurple),
            suffixIcon: suffixIcon,
            fillColor: Theme.of(context).brightness == Brightness.dark 
                ? Colors.white.withValues(alpha: 0.05) 
                : Colors.grey.withValues(alpha: 0.05),
            hintStyle: GoogleFonts.poppins(
              fontSize: 14,
              color: Theme.of(context).hintColor,
            ),
          ),
          style: GoogleFonts.poppins(fontSize: 14),
        ),
        const SizedBox(height: 20),
      ],
    );
  }
}
