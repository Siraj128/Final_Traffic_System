import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';
import '../models/benefits_model.dart';
import '../services/benefits_service.dart';

class BenefitsScreen extends StatefulWidget {
  const BenefitsScreen({super.key});

  @override
  State<BenefitsScreen> createState() => _BenefitsScreenState();
}

class _BenefitsScreenState extends State<BenefitsScreen> {
  BenefitsModel? _benefits;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchBenefits();
  }

  Future<void> _fetchBenefits() async {
    final data = await BenefitsService.getBenefits();
    if (mounted) {
      setState(() {
        _benefits = data;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text(
          "My Tier & Benefits", 
          style: GoogleFonts.poppins(
            color: isDark ? Colors.white : AppColors.primaryDark, 
            fontWeight: FontWeight.bold
          )
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new_rounded, color: isDark ? Colors.white : AppColors.primaryDark),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.primaryPurple))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                   _buildTierCard(),
                   const SizedBox(height: 24),
                   Text(
                     "Your Exclusive Benefits", 
                     style: GoogleFonts.poppins(
                       fontSize: 18, 
                       fontWeight: FontWeight.bold, 
                       color: isDark ? Colors.white : AppColors.primaryDark
                     )
                   ),
                   const SizedBox(height: 16),
                   _buildBenefitsGrid(),
                ],
              ),
            ),
    );
  }

  Widget _buildTierCard() {
    if (_benefits == null) return const SizedBox();

    Color tierColor;
    String emoji;
    switch (_benefits!.tier) {
      case "Bronze": 
        tierColor = const Color(0xFFCD7F32); 
        emoji = "🥉";
        break;
      case "Silver": 
        tierColor = const Color(0xFFC0C0C0); 
        emoji = "🥈";
        break;
      case "Gold": 
        tierColor = const Color(0xFFFFD700); 
        emoji = "🥇";
        break;
      default: 
        tierColor = AppColors.primaryPurple;
        emoji = "🌱";
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [tierColor.withValues(alpha: 0.8), tierColor]), // Fixed deprecated withOpacity
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: tierColor.withValues(alpha: 0.4), // Fixed deprecated withOpacity
            blurRadius: 15,
            offset: const Offset(0, 8),
          )
        ],
      ),
      child: Column(
        children: [
          Text(emoji, style: const TextStyle(fontSize: 48)),
          const SizedBox(height: 8),
          Text(_benefits!.tier.toUpperCase(), style: GoogleFonts.poppins(fontSize: 24, fontWeight: FontWeight.bold, color: AppColors.white, letterSpacing: 2)),
          const SizedBox(height: 4),
          Text("Current Membership Status", style: GoogleFonts.poppins(color: AppColors.white.withValues(alpha: 0.8), fontSize: 12)), // Fixed deprecated withOpacity
          const SizedBox(height: 24),
          
          // Progress
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text("Progress to Next Tier", style: GoogleFonts.poppins(color: AppColors.white, fontWeight: FontWeight.w600)),
                  Text("${_benefits!.totalCredits} / ${_benefits!.nextTierTarget}", style: GoogleFonts.poppins(color: AppColors.white, fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: LinearProgressIndicator(
                  value: _benefits!.nextTierProgress,
                  backgroundColor: AppColors.white.withValues(alpha: 0.3), // Fixed deprecated withOpacity
                  valueColor: const AlwaysStoppedAnimation<Color>(AppColors.white),
                  minHeight: 8,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildBenefitsGrid() {
    if (_benefits == null) return const SizedBox();

    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      crossAxisSpacing: 16,
      mainAxisSpacing: 16,
      childAspectRatio: 1.1,
      children: [
        _buildBenefitCard("Parking Quota", "${_benefits!.parkingQuota} Hours", Icons.local_parking_rounded, AppColors.primaryPurple),
        _buildBenefitCard("Fuel Cashback", "₹ ${_benefits!.fuelCashback}", Icons.local_gas_station_rounded, AppColors.notificationBlue),
        _buildBenefitCard("Service Coupons", "${_benefits!.serviceCoupons} Available", Icons.car_repair_rounded, AppColors.violationRed),
        _buildBenefitCard("Green Wave", _benefits!.greenWaveEligible ? "Active" : "Locked", Icons.traffic_rounded, _benefits!.greenWaveEligible ? AppColors.rewardGreen : AppColors.grey),
      ],
    );
  }

  Widget _buildBenefitCard(String title, String value, IconData icon, Color color) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(20),
        boxShadow: isDark ? [] : [
          BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 10, offset: const Offset(0, 4)),
        ],
        border: isDark ? Border.all(color: Colors.white10) : null,
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1), 
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: color, size: 28),
          ),
          const SizedBox(height: 12),
          Text(
            value, 
            style: GoogleFonts.poppins(
              fontSize: 16, 
              fontWeight: FontWeight.bold, 
              color: isDark ? Colors.white : AppColors.darkGrey
            )
          ),
          const SizedBox(height: 4),
          Text(title, style: GoogleFonts.poppins(fontSize: 12, color: AppColors.grey), textAlign: TextAlign.center),
        ],
      ),
    );
  }
}
