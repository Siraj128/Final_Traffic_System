import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';
import '../models/redemption_model.dart';
import '../services/redemption_service.dart';

class RedemptionScreen extends StatefulWidget {
  final Map<String, dynamic> userData;
  const RedemptionScreen({super.key, required this.userData});

  @override
  State<RedemptionScreen> createState() => _RedemptionScreenState();
}

class _RedemptionScreenState extends State<RedemptionScreen> {
  List<RewardModel> _rewards = [];
  bool _isLoading = true;
  String _selectedCategory = "ALL";
  final List<String> _categories = ["ALL", "FUEL", "TOLL", "SERVICE", "SHOPPING", "INSURANCE"];

  @override
  void initState() {
    super.initState();
    _fetchCatalog();
  }

  Future<void> _fetchCatalog() async {
    final data = await RedemptionService.getCatalog();
    if (mounted) {
      setState(() {
        _rewards = data;
        _isLoading = false;
      });
    }
  }

  Future<void> _handleRedeem(RewardModel reward) async {
    // Show Confirmation Dialog
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text("Confirm Redemption", style: GoogleFonts.poppins(fontWeight: FontWeight.bold)),
        content: Text("Redeem '${reward.title}' for ${reward.pointsRequired} points?", style: GoogleFonts.poppins()),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text("Cancel", style: GoogleFonts.poppins(color: AppColors.grey))),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.primaryPurple),
            onPressed: () {
              Navigator.pop(context);
              _processRedemption(reward);
            },
            child: Text("Confirm", style: GoogleFonts.poppins(color: AppColors.white)),
          ),
        ],
      ),
    );
  }

  Future<void> _processRedemption(RewardModel reward) async {
    setState(() => _isLoading = true);
    final result = await RedemptionService.redeemReward(reward.id);
    setState(() => _isLoading = false);

    if (!mounted) return;

    if (result['success']) {
      _showSuccessDialog(reward, result['coupon']);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result['message'])));
    }
  }

  void _showSuccessDialog(RewardModel reward, String coupon) {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
               const Icon(Icons.check_circle_rounded, color: AppColors.rewardGreen, size: 60),
               const SizedBox(height: 16),
               Text("Redeemed!", style: GoogleFonts.poppins(fontSize: 22, fontWeight: FontWeight.bold)),
               const SizedBox(height: 8),
               Text("Enjoy your ${reward.title}", style: GoogleFonts.poppins(color: AppColors.grey), textAlign: TextAlign.center),
               const SizedBox(height: 24),
               Container(
                 padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                 decoration: BoxDecoration(
                   color: AppColors.lightGrey,
                   borderRadius: BorderRadius.circular(8),
                   border: Border.all(color: AppColors.primaryPurple, width: 1.5), // Standard border
                 ),
                 child: Text(coupon, style: GoogleFonts.poppins(fontSize: 20, fontWeight: FontWeight.bold, letterSpacing: 2, color: AppColors.primaryDark)),
               ),
               const SizedBox(height: 24),
               ElevatedButton(
                 style: ElevatedButton.styleFrom(
                   backgroundColor: AppColors.primaryPurple,
                   minimumSize: const Size(double.infinity, 48),
                   shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                 ),
                 onPressed: () => Navigator.pop(context),
                 child: Text("Done", style: GoogleFonts.poppins(color: Colors.white)),
               ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final filteredRewards = _selectedCategory == "ALL" 
        ? _rewards 
        : _rewards.where((r) => r.category == _selectedCategory).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text("Redeem Rewards"),
        centerTitle: true,
      ),
      body: Column(
        children: [
          const SizedBox(height: 12),
          _buildCategoryTabs(),
          const SizedBox(height: 12),
          Expanded(
            child: _isLoading
                ? Center(child: CircularProgressIndicator(color: theme.colorScheme.primary))
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    itemCount: filteredRewards.length,
                    itemBuilder: (context, index) => _buildRewardCard(filteredRewards[index]),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildCategoryTabs() {
    final theme = Theme.of(context);
    return SizedBox(
      height: 48,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: _categories.length,
        itemBuilder: (context, index) {
          final cat = _categories[index];
          final isSelected = _selectedCategory == cat;
          return GestureDetector(
            onTap: () => setState(() => _selectedCategory = cat),
            child: Container(
              margin: const EdgeInsets.only(right: 12),
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
              decoration: BoxDecoration(
                color: isSelected ? theme.colorScheme.primary : theme.colorScheme.surface,
                borderRadius: BorderRadius.circular(24),
                border: Border.all(
                  color: isSelected ? theme.colorScheme.primary : theme.colorScheme.onSurface.withValues(alpha: 0.1)
                ),
                boxShadow: isSelected ? [
                  BoxShadow(
                    color: theme.colorScheme.primary.withValues(alpha: 0.2),
                    blurRadius: 8,
                    offset: const Offset(0, 4),
                  )
                ] : [],
              ),
              child: Text(
                cat,
                style: theme.textTheme.labelLarge?.copyWith(
                  color: isSelected ? Colors.white : theme.colorScheme.onSurface.withValues(alpha: 0.7),
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildRewardCard(RewardModel reward) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: theme.cardTheme.color,
        borderRadius: BorderRadius.circular(20),
        boxShadow: isDark ? [] : [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 15,
            offset: const Offset(0, 8),
          ),
        ],
        border: isDark ? Border.all(color: Colors.white10) : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            height: 140,
            decoration: BoxDecoration(
              color: theme.colorScheme.primary.withValues(alpha: 0.05),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
            ),
            alignment: Alignment.center,
            child: Icon(
              _getIconForCategory(reward.category), 
              size: 56, 
              color: theme.colorScheme.primary
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.primary.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        reward.category, 
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: theme.colorScheme.primary,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 0.5,
                        )
                      ),
                    ),
                    Text(
                      "${reward.pointsRequired} pts", 
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: isDark ? theme.colorScheme.secondary : AppColors.textPrimary,
                      )
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Text(
                  reward.title, 
                  style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold, fontSize: 18)
                ),
                const SizedBox(height: 8),
                Text(
                  reward.description, 
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                    height: 1.4,
                  )
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () => _handleRedeem(reward),
                    child: const Text("Redeem Now"),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  IconData _getIconForCategory(String category) {
    switch (category) {
      case "FUEL": return Icons.local_gas_station_rounded;
      case "TOLL": return Icons.toll_rounded;
      case "SERVICE": return Icons.car_repair_rounded;
      case "SHOPPING": return Icons.shopping_bag_rounded;
      case "PARKING": return Icons.local_parking_rounded;
      case "INSURANCE": return Icons.security_rounded;
      default: return Icons.card_giftcard_rounded;
    }
  }
}
