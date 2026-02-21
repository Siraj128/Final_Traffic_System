import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'dart:async';
import '../services/auth_service.dart';
import '../constants/app_colors.dart';

class OtpScreen extends StatefulWidget {
  final String destination; // Email or Mobile
  final VoidCallback onVerified;

  const OtpScreen({super.key, required this.destination, required this.onVerified});

  @override
  State<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends State<OtpScreen> {
  final List<TextEditingController> _controllers = List.generate(4, (_) => TextEditingController());
  final List<FocusNode> _focusNodes = List.generate(4, (_) => FocusNode());
  int _counter = 30;
  Timer? _timer;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _startTimer();
  }

  void _startTimer() {
    _counter = 30;
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_counter > 0) {
        setState(() => _counter--);
      } else {
        _timer?.cancel();
      }
    });
  }

  void _verifyOtp() async {
    String otp = _controllers.map((e) => e.text).join();
    if (otp.length != 4) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Please enter full 4-digit OTP")));
      return;
    }

    setState(() => _isLoading = true);
    
    // Call Backend
    // Call Backend (Using RTO Verify for consistency)
    final response = await AuthService.verifyRtoEmailOtp(widget.destination, otp);
    
    if (mounted) {
      setState(() => _isLoading = false);
      
      if (response['success'] == true) {
        widget.onVerified();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(response['message'] ?? "Invalid OTP")),
        );
      }
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    for (var c in _controllers) c.dispose();
    for (var f in _focusNodes) f.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: AppColors.primaryDark),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "Verification Code",
              style: GoogleFonts.poppins(fontSize: 24, fontWeight: FontWeight.bold, color: AppColors.primaryDark),
            ),
            const SizedBox(height: 8),
            Text(
              "We have sent the code verification to\n${widget.destination}",
              style: GoogleFonts.poppins(color: AppColors.grey),
            ),
            const SizedBox(height: 48),
            
            // OTP Fields
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: List.generate(4, (index) {
                return SizedBox(
                  width: 60,
                  height: 60,
                  child: TextField(
                    controller: _controllers[index],
                    focusNode: _focusNodes[index],
                    textAlign: TextAlign.center,
                    keyboardType: TextInputType.number,
                    maxLength: 1,
                    style: GoogleFonts.poppins(fontSize: 24, fontWeight: FontWeight.bold),
                    decoration: InputDecoration(
                      counterText: "",
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      filled: true,
                      fillColor: AppColors.white,
                    ),
                    onChanged: (value) {
                      if (value.isNotEmpty && index < 3) {
                        _focusNodes[index + 1].requestFocus();
                      } else if (value.isEmpty && index > 0) {
                        _focusNodes[index - 1].requestFocus();
                      }
                      if (index == 3 && value.isNotEmpty) {
                        _verifyOtp();
                      }
                    },
                  ),
                );
              }),
            ),
            
            const SizedBox(height: 32),
            
            // Timer & Resend
            Center(
              child: _counter > 0
                  ? Text("Resend code in 00:${_counter.toString().padLeft(2, '0')}", style: GoogleFonts.poppins(color: AppColors.primaryPurple))
                  : TextButton(
                      onPressed: () {
                        _startTimer();
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("OTP Resent")));
                      },
                      child: Text("Resend OTP", style: GoogleFonts.poppins(fontWeight: FontWeight.bold)),
                    ),
            ),
            
            const Spacer(),
            
            // Verify Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _verifyOtp,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primaryPurple,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                child: _isLoading
                    ? const CircularProgressIndicator(color: Colors.white)
                    : Text("Verify", style: GoogleFonts.poppins(fontWeight: FontWeight.bold, color: Colors.white)),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
