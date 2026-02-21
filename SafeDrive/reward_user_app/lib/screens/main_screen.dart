import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';
import 'dashboard_screen.dart';
import 'virtual_card_screen.dart';
import 'scan_screen.dart';
import 'notification_screen.dart';
import 'profile_screen.dart';

class MainScreen extends StatefulWidget {
  final Map<String, dynamic> userData;

  const MainScreen({super.key, required this.userData});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> with SingleTickerProviderStateMixin {
  int _currentIndex = 0;
  late final List<Widget> _screens;
  late AnimationController _animationController;
  late Animation<double> _glowAnimation;

  @override
  void initState() {
    super.initState();
    _screens = [
      DashboardScreen(
        userData: widget.userData,
        onScanSelected: _triggerScan,
      ),
      VirtualCardScreen(userData: widget.userData), // Rewards/Wallet
      const ScanScreen(),
      const NotificationScreen(), // Alerts
      ProfileScreen(userData: widget.userData),
    ];
    
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    _glowAnimation = Tween<double>(begin: 4, end: 12).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
  }

  void _triggerScan() {
    Navigator.push(
      context, 
      MaterialPageRoute(builder: (context) => const ScanScreen())
    );
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return PopScope(
      canPop: false,
      onPopInvoked: (didPop) async {
        if (didPop) return;
        if (_currentIndex != 0) {
          setState(() => _currentIndex = 0);
        } else {
           // Allow app exit or show dialog
           // SystemNavigator.pop(); 
        }
      },
      child: Scaffold(
        extendBody: true,
        resizeToAvoidBottomInset: false,
        body: IndexedStack(
          index: _currentIndex,
          children: _screens,
        ),
        floatingActionButton: AnimatedBuilder(
          animation: _glowAnimation,
          builder: (context, child) {
            return Container(
              height: 64, // Fixed acceptable size for FAB
              width: 64,
              decoration: BoxDecoration(
                color: AppColors.primaryPurple,
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primaryPurple.withValues(alpha: 0.4),
                    blurRadius: _glowAnimation.value + 6,
                    spreadRadius: _glowAnimation.value - 2,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: child,
            );
          },
          child: FloatingActionButton(
            onPressed: _triggerScan,
            backgroundColor: Colors.transparent,
            elevation: 0,
            shape: const CircleBorder(),
            child: const Icon(Icons.qr_code_scanner_rounded, color: Colors.white, size: 32),
          ),
        ),
        floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
        bottomNavigationBar: BottomAppBar(
          shape: const CircularNotchedRectangle(),
          notchMargin: 8,
          color: isDark ? const Color(0xFF1E293B) : Colors.white,
          elevation: 10,
          padding: EdgeInsets.zero,
          child: SizedBox(
            height: 70,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildNavItem(0, Icons.home_rounded, "Home", width),
                _buildNavItem(1, Icons.account_balance_wallet_rounded, "Rewards", width),
                const SizedBox(width: 48), // Fixed spacer for FAB
                _buildNavItem(3, Icons.notifications_rounded, "Alerts", width),
                _buildNavItem(4, Icons.person_rounded, "Profile", width),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(int index, IconData icon, String label, double screenWidth) {
    final isSelected = _currentIndex == index;
    return InkWell(
      onTap: () => setState(() => _currentIndex = index),
      customBorder: const CircleBorder(),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              color: isSelected ? AppColors.primaryPurple : AppColors.grey,
              size: 26,
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: GoogleFonts.poppins(
                fontSize: 10,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                color: isSelected ? AppColors.primaryPurple : AppColors.grey,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
