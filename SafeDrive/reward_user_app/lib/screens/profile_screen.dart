import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../constants/app_colors.dart';
import '../services/auth_service.dart';
import '../services/session_manager.dart';
import 'auth_home_screen.dart';
import 'traffic_assistant_screen.dart';

import 'edit_profile_screen.dart';
import 'vehicle_details_screen.dart';
import 'notification_screen.dart';
import 'privacy_security_screen.dart';
import 'forgot_password_screen.dart';
import 'help_support_screen.dart';
import 'VehicleManagementScreen.dart';

import 'package:image_picker/image_picker.dart';
import 'dart:io';

class ProfileScreen extends StatefulWidget {
  final Map<String, dynamic> userData;

  const ProfileScreen({super.key, required this.userData});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  File? _localImage;
  late Map<String, dynamic> _userData;

  @override
  void initState() {
    super.initState();
    _userData = widget.userData;
  }

  void _showLogoutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Theme.of(context).cardColor,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Text(
          "Logout",
          style: GoogleFonts.poppins(fontWeight: FontWeight.bold),
        ),
        content: Text(
          "Are you sure you want to logout?",
          style: GoogleFonts.poppins(),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text("Cancel", style: GoogleFonts.poppins(color: AppColors.grey)),
          ),
          ElevatedButton(
            onPressed: () async {
              await AuthService.logout();
              if (context.mounted) {
                Navigator.pushAndRemoveUntil(
                  context,
                  MaterialPageRoute(builder: (context) => const AuthHomeScreen()),
                  (route) => false,
                );
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.violationRed,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: Text("Logout", style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final image = await picker.pickImage(source: ImageSource.gallery);
    if (image != null) {
      setState(() {
        _localImage = File(image.path);
      });
      // Optionally save automatically or just wait for Edit Profile save
      // For now, let's navigate to Edit Profile if they pick an image here
      if (mounted) {
        Navigator.push(
          context, 
          MaterialPageRoute(builder: (context) => EditProfileScreen(userData: _userData))
        ).then((updated) {
           if (updated == true) {
              // Refresh logic would go here
           }
        });
      }
    }
  }

  ImageProvider? _getAvatarImage() {
    if (_localImage != null) return FileImage(_localImage!);
    
    final avatarUrl = _userData['user_pic'] ?? _userData['avatar'];
    if (avatarUrl != null && avatarUrl.toString().isNotEmpty) {
      if (avatarUrl.startsWith('file://')) {
        return FileImage(File(avatarUrl.replaceFirst('file://', '')));
      }
      return CachedNetworkImageProvider(avatarUrl);
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    final height = MediaQuery.of(context).size.height;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: RefreshIndicator(
        onRefresh: () async {
          // Refresh user data logic would normally go here
          await Future.delayed(const Duration(seconds: 1));
          if (mounted) setState(() {});
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: Column(
            children: [
              // Premium Gradient Header
              Stack(
                alignment: Alignment.center,
                clipBehavior: Clip.none,
                children: [
                  Container(
                    height: height * 0.15,
                    width: double.infinity,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [
                          AppColors.primaryPurple,
                          AppColors.primaryPurple.withValues(alpha: 0.7),
                        ],
                      ),
                      borderRadius: const BorderRadius.only(
                        bottomLeft: Radius.circular(30),
                        bottomRight: Radius.circular(30),
                      ),
                    ),
                  ),
                  Positioned(
                    top: height * 0.08,
                    child: Stack(
                      children: [
                        Container(
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(color: Colors.white, width: 4),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withValues(alpha: 0.2),
                                blurRadius: 10,
                                spreadRadius: 2,
                              ),
                            ],
                          ),
                            child: CircleAvatar(
                              radius: 60,
                              backgroundColor: AppColors.primaryGold.withValues(alpha: 0.2),
                              backgroundImage: _getAvatarImage(),
                              child: _getAvatarImage() == null
                                  ? Text(
                                      ((_userData['owner_name'] ?? _userData['user_name'] ?? _userData['name'] ?? 'U').toString().isNotEmpty 
                                          ? (_userData['owner_name'] ?? _userData['user_name'] ?? _userData['name'] ?? 'U').toString()[0] 
                                          : 'U').toUpperCase(),
                                      style: GoogleFonts.poppins(fontSize: 40, color: AppColors.primaryGold, fontWeight: FontWeight.bold),
                                    )
                                  : null,
                            ),
                        ),
                        Positioned(
                          bottom: 0,
                          right: 4,
                          child: GestureDetector(
                            onTap: _pickImage,
                            child: Container(
                              padding: const EdgeInsets.all(8),
                              decoration: const BoxDecoration(
                                color: Colors.white,
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.camera_alt, color: AppColors.primaryPurple, size: 20),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              
              SizedBox(height: height * 0.12), // Increased to prevent avatar overlap
              
              // Profile Info
              Padding(
                padding: EdgeInsets.symmetric(horizontal: width * 0.06),
                child: Column(
                  children: [
                    Text(
                      _userData['name'] ?? _userData['owner_name'] ?? _userData['user_name'] ?? 'Driver',
                      textAlign: TextAlign.center,
                      overflow: TextOverflow.ellipsis,
                      style: GoogleFonts.poppins(
                        fontSize: width * 0.06,
                        fontWeight: FontWeight.bold,
                        color: isDark ? Colors.white : AppColors.primaryDark,
                      ),
                      maxLines: 1,
                    ),
                    FutureBuilder<String?>(
                      future: SessionManager.getSelectedVehicleNumber(),
                      builder: (context, snapshot) {
                        return Text(
                          snapshot.data ?? _userData['vehicle_number'] ?? _userData['plate_number'] ?? 'N/A',
                          style: GoogleFonts.poppins(
                            fontSize: width * 0.035,
                            color: AppColors.grey,
                            letterSpacing: 1.2,
                          ),
                        );
                      }
                    ),
                    const SizedBox(height: 12),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                          decoration: BoxDecoration(
                            color: AppColors.primaryGold.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(24),
                            border: Border.all(color: AppColors.primaryGold.withOpacity(0.3), width: 1.5),
                            boxShadow: [
                               BoxShadow(
                                 color: AppColors.primaryGold.withOpacity(0.05),
                                 blurRadius: 10,
                                 offset: const Offset(0, 4),
                               )
                            ],
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.stars_rounded, color: AppColors.primaryGold, size: 22),
                              const SizedBox(width: 10),
                              Text(
                                "${_userData['points'] ?? _userData['wallet_points'] ?? 0} PTS Earned",
                                style: GoogleFonts.poppins(
                                  fontSize: width * 0.04,
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.primaryGold,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              
              SizedBox(height: height * 0.04),

              // Menu List
              Padding(
                padding: EdgeInsets.symmetric(horizontal: width * 0.04),
                child: Container(
                  decoration: BoxDecoration(
                    color: isDark ? Colors.white.withValues(alpha: 0.05) : Colors.white,
                    borderRadius: BorderRadius.circular(24),
                    boxShadow: isDark ? [] : [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.05),
                        blurRadius: 20,
                        offset: const Offset(0, 10),
                      ),
                    ],
                  ),
                  child: ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(8),
                    itemCount: 8,
                    separatorBuilder: (context, index) => Divider(
                      height: 1, 
                      color: isDark ? Colors.white.withValues(alpha: 0.1) : Colors.grey.withValues(alpha: 0.1),
                      indent: 60,
                    ),
                    itemBuilder: (context, index) {
                      final items = [
                        {"icon": Icons.person_outline, "title": "Edit Profile", "screen": EditProfileScreen(userData: _userData)},
                        {"icon": Icons.directions_car_filled_outlined, "title": "Manage Fleet", "screen": const VehicleManagementScreen()},
                        {"icon": Icons.lock_reset_outlined, "title": "Change Password", "screen": const ForgotPasswordScreen()},
                        {"icon": Icons.directions_car_outlined, "title": "Vehicle Details", "screen": VehicleDetailsScreen(vehicle: _userData)},
                        {"icon": Icons.notifications_outlined, "title": "Notifications", "screen": const NotificationScreen()},
                        {"icon": Icons.shield_outlined, "title": "Traffic Rules & Assistant", "screen": const TrafficAssistantScreen()},
                        {"icon": Icons.security_outlined, "title": "Privacy & Security", "screen": const PrivacySecurityScreen()},
                        {"icon": Icons.help_outline, "title": "Help & Support", "screen": const HelpSupportScreen()},
                      ];
                      
                      final item = items[index];
                      return Container(
                        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(16),
                          child: Material(
                            color: Colors.transparent,
                            child: InkWell(
                              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (context) => item['screen'] as Widget)),
                              child: Container(
                                padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                                decoration: BoxDecoration(
                                  color: isDark ? Colors.white.withValues(alpha: 0.05) : Colors.black.withValues(alpha: 0.02),
                                  borderRadius: BorderRadius.circular(16),
                                  border: Border.all(color: isDark ? Colors.white10 : Colors.black.withValues(alpha: 0.05)),
                                ),
                                child: Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.all(10),
                                      decoration: BoxDecoration(
                                        color: AppColors.primaryPurple.withValues(alpha: 0.1),
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      child: Icon(item['icon'] as IconData, color: AppColors.primaryPurple, size: 22),
                                    ),
                                    const SizedBox(width: 16),
                                    Expanded(
                                      child: Text(
                                        item['title'] as String,
                                        style: GoogleFonts.poppins(
                                          fontWeight: FontWeight.w600, 
                                          fontSize: width * 0.04,
                                          color: isDark ? Colors.white : AppColors.darkGrey,
                                        ),
                                      ),
                                    ),
                                    Icon(Icons.arrow_forward_ios_rounded, size: 16, color: AppColors.grey.withValues(alpha: 0.5)),
                                    const SizedBox(width: 8),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ),

              SizedBox(height: height * 0.04),

              // Logout Button
              Padding(
                padding: EdgeInsets.symmetric(horizontal: width * 0.06),
                child: SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(18),
                      gradient: const LinearGradient(
                        colors: [AppColors.violationRed, Color(0xFFFF6B6B)],
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.violationRed.withValues(alpha: 0.3),
                          blurRadius: 10,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: ElevatedButton(
                      onPressed: () => _showLogoutDialog(context),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        foregroundColor: Colors.white,
                        shadowColor: Colors.transparent,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                      ),
                      child: Text(
                        "LOGOUT",
                        style: GoogleFonts.poppins(fontWeight: FontWeight.bold, letterSpacing: 1.2),
                      ),
                    ),
                  ),
                ),
              ),

              // FAB Overlap Prevention Spacing
              const SizedBox(height: 120),
            ],
          ),
        ),
      ),
    );
  }
}
