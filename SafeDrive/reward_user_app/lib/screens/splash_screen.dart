import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'dart:async';
import 'auth_home_screen.dart';
import 'main_screen.dart';
import 'package:local_auth/local_auth.dart';
import '../services/auth_service.dart';
import '../services/session_manager.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: const Interval(0.0, 0.6, curve: Curves.easeIn)),
    );

    _scaleAnimation = Tween<double>(begin: 0.8, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: const Interval(0.0, 0.8, curve: Curves.elasticOut)),
    );

    _controller.forward().then((_) {
      Timer(const Duration(milliseconds: 800), () {
        if (mounted) {
          _fadeOutAndNavigate();
        }
      });
    });
  }

  void _fadeOutAndNavigate() async {
    print("SplashScreen: Starting Navigation Logic");
    
    // Check local session first
    final bool loggedIn = await SessionManager.isLoggedIn();
    Map<String, dynamic>? userData;
    bool authenticated = false;

    if (loggedIn) {
      // Try to get fresh profile if possible
      final session = await AuthService.checkSession();
      if (session['loggedIn'] == true) {
        userData = session['user'];
        
        try {
          final localAuth = LocalAuthentication();
          final canCheckBiometrics = await localAuth.canCheckBiometrics;
          final isBiometricSupported = await localAuth.isDeviceSupported();
          
          if (canCheckBiometrics && isBiometricSupported) {
            authenticated = await localAuth.authenticate(
              localizedReason: 'Please authenticate to access SafeDrive Rewards',
              options: const AuthenticationOptions(
                stickyAuth: true,
                biometricOnly: false,
              ),
            );
          } else {
            authenticated = true; 
          }
        } catch (e) {
          authenticated = true;
        }
      }
    }

    _controller.reverse().then((_) {
      if (mounted) {
        if (loggedIn && userData != null && authenticated) {
          print("SplashScreen: Auto-login Successful");
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (context) => MainScreen(userData: userData!)),
          );
        } else {
          print("SplashScreen: Navigating to Auth Home");
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (context) => const AuthHomeScreen()),
          );
        }
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF020617), // Professional deep blue-black
      body: Stack(
        children: [
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                AnimatedBuilder(
                  animation: _controller,
                  builder: (context, child) {
                    return Opacity(
                      opacity: _fadeAnimation.value,
                      child: Transform.scale(
                        scale: _scaleAnimation.value,
                        child: child,
                      ),
                    );
                  },
                  child: Hero(
                    tag: 'app_logo',
                    child: Image.asset(
                      'assets/images/startup.png',
                      width: 320, // Slightly larger for impact
                      height: 320,
                      fit: BoxFit.contain,
                    ),
                  ),
                ),
                const SizedBox(height: 48),
                // Progress Bar Container
                SizedBox(
                  width: 200,
                  height: 4,
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(2),
                    child: AnimatedBuilder(
                      animation: _controller,
                      builder: (context, child) {
                        // Ensure progress bar stays full during reverse animation
                        final progress = _controller.status == AnimationStatus.reverse 
                            ? 1.0 
                            : _controller.value;
                        return LinearProgressIndicator(
                          value: progress,
                          backgroundColor: Colors.white.withOpacity(0.05),
                          valueColor: const AlwaysStoppedAnimation<Color>(
                            Color(0xFF3B82F6), // Professional primary blue
                          ),
                        );
                      },
                    ),
                  ),
                ),
              ],
            ),
          ),
          // Subtle glow effect behind logo
          Positioned.fill(
            child: IgnorePointer(
              child: Center(
                child: Container(
                  width: 200,
                  height: 200,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF3B82F6).withOpacity(0.15),
                        blurRadius: 100,
                        spreadRadius: 20,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
