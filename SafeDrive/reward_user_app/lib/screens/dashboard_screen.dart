import 'package:flutter/material.dart';
import 'dart:io';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';
import '../services/api_service.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/session_manager.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'profile_screen.dart';
import 'leaderboard_screen.dart';
import 'analytics_screen.dart';
import 'traffic_assistant_screen.dart';
import '../widgets/fastag_sheet.dart';
import '../widgets/tier_overview_sheet.dart';
import 'package:flutter_svg/flutter_svg.dart';

class DashboardScreen extends StatefulWidget {
  final Map<String, dynamic>? userData;
  final VoidCallback? onScanSelected;
  const DashboardScreen({super.key, this.userData, this.onScanSelected});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic> _userData = {};
  List<dynamic> _vehicles = [];
  int? _selectedVehicleId;
  String? _selectedVehicleNumber;
  Map<String, dynamic> _analyticsData = {};
  bool _isLoading = false;
  bool get _isGhostUser => _userData.containsKey('ghost') && _userData['ghost'] == true;

  String get safeBalance {
    try {
      final raw = _userData['balance'] ?? _userData['wallet_balance'] ?? 0;
      final val = double.tryParse(raw.toString()) ?? 0.0;
      return val.toStringAsFixed(2);
    } catch (e) {
      print("Error parsing balance: $e");
      return "0.00";
    }
  }

  @override
  void initState() {
    super.initState();
    if (widget.userData != null) {
      _userData = widget.userData!;
    } else {
      _fetchUserData();
    }
  }

  Future<void> _fetchUserData() async {
    setState(() => _isLoading = true);
    try {
      // 1. Fetch Profile (Unified)
      final profile = await ApiService.getWallet(); // Uses token to get driver wallet
      
      // 2. Fetch Fleet
      final vehicles = await ApiService.getMyVehicles();
      
      // 3. Get Selected Vehicle
      int? selectedId = await SessionManager.getSelectedVehicleId();
      String? selectedPlate = await SessionManager.getSelectedVehicleNumber();

      if (vehicles.isNotEmpty) {
        if (selectedId == null || !vehicles.any((v) => v['vehicle_id'] == selectedId)) {
          final primary = vehicles.firstWhere((v) => v['is_primary'] == true, orElse: () => vehicles.first);
          selectedId = primary['vehicle_id'];
          selectedPlate = primary['plate_number'];
          await SessionManager.setSelectedVehicle(selectedId!, selectedPlate!);
        }
      }

      // 4. Fetch Analytics for selected
      Map<String, dynamic> analytics = {};
      if (selectedId != null) {
        analytics = await ApiService.getAnalytics(selectedId);
      }

      setState(() {
        _userData = profile;
        _vehicles = vehicles;
        _selectedVehicleId = selectedId;
        _selectedVehicleNumber = selectedPlate;
        _analyticsData = analytics;
        _isLoading = false;
      });
      
      // Update session with latest user data if possible
      await SessionManager.updateUserData(profile);
      
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _onVehicleSwitched(dynamic vehicle) async {
    await SessionManager.setSelectedVehicle(vehicle['vehicle_id'], vehicle['plate_number']);
    _fetchUserData();
  }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    final height = MediaQuery.of(context).size.height;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _fetchUserData,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: EdgeInsets.all(width * 0.05),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            Flexible(
                              child: Text(
                                "Hello, ${_userData['name'] ?? 'Driver'} 👋",
                                style: GoogleFonts.poppins(
                                  color: isDark ? Colors.white : AppColors.primaryDark,
                                  fontSize: width * 0.05,
                                  fontWeight: FontWeight.bold,
                                ),
                                overflow: TextOverflow.ellipsis,
                                maxLines: 1,
                              ),
                            ),
                            const SizedBox(width: 8),
                            GestureDetector(
                              onTap: () => TierOverviewSheet.show(context, _userData['wallet_points'] ?? 0),
                              child: _buildRankBadge(_userData['wallet_points'] ?? 0, width),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        GestureDetector(
                          onTap: _showVehiclePicker,
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: isDark ? Colors.white10 : Colors.black.withOpacity(0.05),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: AppColors.primaryPurple.withOpacity(0.3)),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.directions_car_filled, size: 14, color: AppColors.primaryPurple),
                                const SizedBox(width: 6),
                                Text(
                                  _selectedVehicleNumber ?? "Select Vehicle",
                                  style: GoogleFonts.poppins(
                                    color: isDark ? Colors.white70 : AppColors.primaryDark,
                                    fontSize: width * 0.03,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const Icon(Icons.keyboard_arrow_down, size: 16, color: AppColors.grey),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  GestureDetector(
                    onTap: () async {
                      final refresh = await Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => ProfileScreen(userData: _userData),
                        ),
                      );
                      if (refresh == true) _fetchUserData();
                    },
                    child: Container(
                      padding: const EdgeInsets.all(2),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(color: AppColors.primaryPurple, width: 2),
                      ),
                      child: CircleAvatar(
                        radius: width * 0.06,
                        backgroundColor: AppColors.primaryPurple,
                        backgroundImage: _userData['avatar'] != null && _userData['avatar'].startsWith('http')
                            ? CachedNetworkImageProvider(_userData['avatar'])
                            : (_userData['user_pic'] != null && _userData['user_pic'].startsWith('file://')
                                ? FileImage(File(_userData['user_pic'].replaceAll('file://', '')))
                                : null) as ImageProvider?,
                        child: (_userData['avatar'] == null && _userData['user_pic'] == null)
                            ? Text(
                                (_userData['name'] ?? 'U')[0].toUpperCase(),
                                style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.bold, fontSize: width * 0.04),
                              )
                            : null,
                      ),
                    ),
                  ),
                ],
              ),
              
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _ActionButton(
                    icon: Icons.analytics_rounded,
                    label: "Stats",
                    color: Colors.orange,
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AnalyticsScreen())),
                    width: width,
                  ),
                  _ActionButton(
                    icon: Icons.payment_rounded,
                    label: "FASTag",
                    color: Colors.blueAccent,
                    onTap: () => FastagSheet.show(
                      context, 
                      onLoading: (val) => setState(() => _isLoading = val),
                      onComplete: () => _fetchUserData(),
                    ),
                    width: width,
                  ),
                ],
              ),
              
              SizedBox(height: height * 0.03),

              // --- ENHANCED REWARDS WALLET CARD ---
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(28),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: isDark 
                        ? [AppColors.primaryPurple.withOpacity(0.9), AppColors.primaryPurple.withOpacity(0.5)]
                        : [AppColors.primaryPurple, const Color(0xFF6366F1)], // Modern Indigo-Purple mix
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(32),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primaryPurple.withOpacity(0.4),
                      blurRadius: 25,
                      offset: const Offset(0, 12),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "SafeDrive Rewards",
                              style: GoogleFonts.poppins(
                                color: Colors.white.withOpacity(0.9),
                                fontSize: width * 0.035,
                                fontWeight: FontWeight.w600,
                                letterSpacing: 0.5,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text(
                                  "${_userData['points'] ?? _userData['wallet_points'] ?? 0}",
                                  style: GoogleFonts.poppins(
                                    color: Colors.white,
                                    fontSize: width * 0.1,
                                    fontWeight: FontWeight.bold,
                                    height: 1,
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Padding(
                                  padding: const EdgeInsets.only(bottom: 4),
                                  child: Text(
                                    "PTS",
                                    style: GoogleFonts.poppins(
                                      color: Colors.white70,
                                      fontSize: width * 0.04,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                        Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.2),
                            shape: BoxShape.circle,
                            border: Border.all(color: Colors.white24),
                          ),
                          child: Icon(Icons.stars_rounded, color: AppColors.primaryGold, size: width * 0.09),
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: Colors.white12),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(6),
                                decoration: const BoxDecoration(color: AppColors.primaryGold, shape: BoxShape.circle),
                                child: const Icon(Icons.currency_rupee_rounded, color: Colors.white, size: 14),
                              ),
                              const SizedBox(width: 10),
                              Text(
                                "Wallet Balance (Updated)",
                                style: GoogleFonts.poppins(color: Colors.white.withValues(alpha: 0.8), fontSize: width * 0.035, fontWeight: FontWeight.w500),
                              ),
                            ],
                          ),
                          Text(
                            "₹$safeBalance",
                            style: GoogleFonts.poppins(
                              color: Colors.white,
                              fontSize: width * 0.045,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              SizedBox(height: height * 0.03),

              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: _StatusBadge(
                      icon: Icons.verified_user_rounded,
                      label: "${_analyticsData['compliance_score'] ?? 100}% Compliance",
                      color: AppColors.rewardGreen, 
                      width: width,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _StatusBadge(
                      icon: Icons.local_fire_department_rounded,
                      label: "${_analyticsData['safeStreakDays'] ?? _userData['safe_streak'] ?? 0} Day Streak",
                      color: Colors.orangeAccent,
                      width: width,
                    ),
                  ),
                ],
              ),
              
              Container(
                margin: const EdgeInsets.only(top: 24),
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AppColors.primaryPurple, AppColors.primaryDark],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(24),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primaryPurple.withValues(alpha: 0.3),
                      blurRadius: 15,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "SafeDrive Assistant",
                            style: GoogleFonts.poppins(
                              color: Colors.white,
                              fontSize: width * 0.045,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            "Ask about traffic rules & fines",
                            style: GoogleFonts.poppins(
                              color: Colors.white70,
                              fontSize: width * 0.03,
                            ),
                          ),
                          const SizedBox(height: 12),
                          ElevatedButton(
                            onPressed: () => Navigator.push(
                              context, 
                              MaterialPageRoute(builder: (_) => const TrafficAssistantScreen())
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.white,
                              foregroundColor: AppColors.primaryPurple,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                              elevation: 0,
                            ),
                            child: Text(
                              "Chat Now",
                              style: GoogleFonts.poppins(fontWeight: FontWeight.bold, fontSize: width * 0.03),
                            ),
                          ),
                        ],
                      ),
                    ),
                    Icon(Icons.shield_rounded, color: Colors.white.withValues(alpha: 0.1), size: width * 0.2),
                    const SizedBox(width: 8),
                    SvgPicture.asset(
                      'assets/images/logo.svg',
                      height: width * 0.15,
                      colorFilter: const ColorFilter.mode(Colors.white12, BlendMode.srcIn),
                    ),
                  ],
                ),
              ),
              
              SizedBox(height: height * 0.04),
              
              Text(
                "Driving Insights",
                style: GoogleFonts.poppins(
                  fontSize: width * 0.045,
                  fontWeight: FontWeight.bold,
                  color: isDark ? Colors.white : AppColors.primaryDark,
                ),
              ),
              SizedBox(height: height * 0.02),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: isDark ? Colors.white.withValues(alpha: 0.05) : Colors.white,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: isDark ? Colors.white10 : Colors.black.withValues(alpha: 0.05)),
                  boxShadow: isDark ? [] : [
                    BoxShadow(color: Colors.black.withValues(alpha: 0.03), blurRadius: 10, offset: const Offset(0, 4)),
                  ],
                ),
                child: Column(
                  children: [
                    _buildInsightRow("Avg. Speed", "${_analyticsData['avg_speed'] ?? '0'} km/h", Icons.speed_rounded, Colors.blue, width),
                    const Divider(height: 24),
                    _buildInsightRow("Safety Score", "${_analyticsData['safety_score'] ?? '0'}/100", Icons.verified_user_rounded, Colors.green, width),
                    const Divider(height: 24),
                    _buildInsightRow("Monthly Trips", "${(_analyticsData['trips'] ?? []).length}", Icons.route_rounded, Colors.orange, width),
                  ],
                ),
              ),
              
              SizedBox(height: height * 0.04),

              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    "Recent Activity",
                    style: GoogleFonts.poppins(
                      fontSize: width * 0.045,
                      fontWeight: FontWeight.bold,
                      color: isDark ? Colors.white : AppColors.primaryDark,
                    ),
                  ),
                  TextButton(
                    onPressed: () {},
                    child: Text("View All", style: GoogleFonts.poppins(color: AppColors.primaryPurple, fontSize: width * 0.03)),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              _buildActivityItem("Morning Drive", "2.4 km • 15 mins", "+12 pts", Icons.directions_car_rounded, width, isDark),
              _buildActivityItem("Weekly Bonus", "Compliance Reward", "+50 pts", Icons.stars_rounded, width, isDark),
              _buildActivityItem("Fastag Payment", "NH4 Toll Plaza", "-₹35.00", Icons.payment_rounded, width, isDark),

              const SizedBox(height: 100),
            ],
          ),
        ),
        ),
      ),
    );
  }

  Widget _buildInsightRow(String label, String value, IconData icon, Color color, double width) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(10)),
          child: Icon(icon, color: color, size: 20),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            label, 
            style: GoogleFonts.poppins(color: AppColors.grey, fontSize: width * 0.035),
            overflow: TextOverflow.ellipsis,
          ),
        ),
        Text(value, style: GoogleFonts.poppins(fontWeight: FontWeight.bold, fontSize: width * 0.035)),
      ],
    );
  }

  Widget _buildActivityItem(String title, String sub, String reward, IconData icon, double width, bool isDark) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isDark ? Colors.white.withValues(alpha: 0.03) : Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isDark ? Colors.white10 : Colors.black.withValues(alpha: 0.05)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppColors.primaryPurple.withValues(alpha: 0.1),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: AppColors.primaryPurple, size: 20),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title, 
                  style: GoogleFonts.poppins(fontWeight: FontWeight.bold, fontSize: width * 0.035),
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  sub, 
                  style: GoogleFonts.poppins(color: AppColors.grey, fontSize: width * 0.028),
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          Text(
            reward,
            style: GoogleFonts.poppins(
              fontWeight: FontWeight.bold,
              color: reward.startsWith('+') ? AppColors.rewardGreen : Colors.redAccent,
              fontSize: width * 0.035,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRankBadge(int credits, double width) {
    String rank = "Bronze";
    Color color = const Color(0xFFCD7F32);
    String emoji = "🥉";
    
    if (credits >= 2000) {
      rank = "Gold";
      color = const Color(0xFFFFD700);
      emoji = "🥇";
    } else if (credits >= 1000) {
      rank = "Silver";
      color = const Color(0xFFC0C0C0);
      emoji = "🥈";
    } else {
      rank = "Bronze";
      color = const Color(0xFFCD7F32);
      emoji = "🥉";
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withValues(alpha: 0.5), width: 1.5),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(emoji, style: TextStyle(fontSize: width * 0.035)),
          const SizedBox(width: 4),
          Flexible(
            child: Text(
              rank,
              style: GoogleFonts.poppins(
                color: color,
                fontSize: width * 0.03,
                fontWeight: FontWeight.bold,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  void _showVehiclePicker() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        decoration: BoxDecoration(
          color: Theme.of(context).cardColor,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(30)),
        ),
        padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: Text(
                'Switch Vehicle',
                style: GoogleFonts.poppins(fontSize: 20, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(height: 16),
            Flexible(
              child: _vehicles.isEmpty 
                ? Padding(
                    padding: const EdgeInsets.all(20),
                    child: Text("No vehicles found", style: GoogleFonts.poppins()),
                  )
                : ListView.builder(
                    shrinkWrap: true,
                    itemCount: _vehicles.length,
                    itemBuilder: (context, index) {
                      final v = _vehicles[index];
                      final isSelected = v['vehicle_id'] == _selectedVehicleId;
                      return ListTile(
                        leading: Icon(Icons.directions_car, color: isSelected ? AppColors.primaryPurple : AppColors.grey),
                        title: Text(v['plate_number'], style: GoogleFonts.poppins(fontWeight: isSelected ? FontWeight.bold : FontWeight.normal)),
                        subtitle: Text('${v['brand'] ?? ''} ${v['model'] ?? ''}'),
                        trailing: isSelected ? const Icon(Icons.check_circle, color: AppColors.rewardGreen) : null,
                        onTap: () {
                          Navigator.pop(context);
                          _onVehicleSwitched(v);
                        },
                      );
                    },
                  ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final double width;

  const _StatusBadge({required this.icon, required this.label, required this.color, required this.width});

  @override
  Widget build(BuildContext context) {
    bool isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      padding: EdgeInsets.symmetric(horizontal: width * 0.03, vertical: 8),
      decoration: BoxDecoration(
        color: isDark ? Colors.white.withValues(alpha: 0.1) : Colors.grey.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: width * 0.04),
          const SizedBox(width: 6),
          Flexible(
            child: Text(
              label,
              style: GoogleFonts.poppins(
                color: isDark ? Colors.white : AppColors.darkGrey, 
                fontWeight: FontWeight.bold, 
                fontSize: width * 0.03,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;
  final double width;

  const _ActionButton({required this.icon, required this.label, required this.color, required this.onTap, required this.width});

  @override
  Widget build(BuildContext context) {
    bool isDark = Theme.of(context).brightness == Brightness.dark;
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            padding: EdgeInsets.all(width * 0.04),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Icon(icon, color: color, size: width * 0.07),
          ),
          const SizedBox(height: 8),
          Text(
            label,
            style: GoogleFonts.poppins(
              color: isDark ? Colors.white70 : AppColors.darkGrey, 
              fontSize: width * 0.03, 
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}
