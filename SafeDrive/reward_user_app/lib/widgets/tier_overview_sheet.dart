import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';

class TierOverviewSheet extends StatelessWidget {
  final int currentCredits;

  const TierOverviewSheet({super.key, required this.currentCredits});

  static void show(BuildContext context, int credits) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => TierOverviewSheet(currentCredits: credits),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final width = MediaQuery.of(context).size.width;

    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: Colors.grey.withValues(alpha: 0.3),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            "Reward Tiers",
            style: GoogleFonts.poppins(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: isDark ? Colors.white : AppColors.primaryDark,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            "Earn credits to unlock premium benefits",
            style: GoogleFonts.poppins(
              fontSize: 14,
              color: AppColors.grey,
            ),
          ),
          const SizedBox(height: 32),
          _buildTierItem(
            context,
            title: "Gold Tier",
            threshold: 2000,
            color: const Color(0xFFFFD700),
            emoji: "🥇",
            benefits: ["5% Fuel Cashback", "Unlimited Parking Quota", "Priority Road Support"],
            isUnlocked: currentCredits >= 2000,
            width: width,
          ),
          const SizedBox(height: 16),
          _buildTierItem(
            context,
            title: "Silver Tier",
            threshold: 1000,
            color: const Color(0xFFC0C0C0),
            emoji: "🥈",
            benefits: ["2% Fuel Cashback", "4h Weekly Parking", "Tiered Toll Discount"],
            isUnlocked: currentCredits >= 1000,
            width: width,
          ),
          const SizedBox(height: 16),
          _buildTierItem(
            context,
            title: "Bronze Tier",
            threshold: 0,
            color: const Color(0xFFCD7F32),
            emoji: "🥉",
            benefits: ["1% Fuel Cashback", "2h Weekly Parking", "Safe Driver Badge"],
            isUnlocked: true, // Bronze is now the default starting tier
            width: width,
          ),
          const SizedBox(height: 32),
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primaryPurple,
              foregroundColor: Colors.white,
              minimumSize: const Size(double.infinity, 56),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              elevation: 0,
            ),
            child: Text(
              "Keep Driving Safe",
              style: GoogleFonts.poppins(fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildTierItem(
    BuildContext context, {
    required String title,
    required int threshold,
    required Color color,
    required String emoji,
    required List<String> benefits,
    required bool isUnlocked,
    required double width,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isUnlocked 
            ? color.withValues(alpha: 0.1) 
            : (isDark ? Colors.white.withValues(alpha: 0.05) : Colors.grey.withValues(alpha: 0.05)),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isUnlocked ? color.withValues(alpha: 0.3) : Colors.transparent,
          width: 2,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.2),
                  shape: BoxShape.circle,
                ),
                child: Text(emoji, style: const TextStyle(fontSize: 20)),
              ),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: GoogleFonts.poppins(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                      color: isDark ? Colors.white : AppColors.primaryDark,
                    ),
                  ),
                  Text(
                    "$threshold+ Credits",
                    style: GoogleFonts.poppins(
                      fontSize: 12,
                      color: AppColors.grey,
                    ),
                  ),
                ],
              ),
              const Spacer(),
              if (isUnlocked)
                const Icon(Icons.check_circle_rounded, color: Colors.green, size: 24)
              else
                Icon(Icons.lock_outline_rounded, color: AppColors.grey.withValues(alpha: 0.5), size: 20),
            ],
          ),
          if (isUnlocked) ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: benefits.map((benefit) => Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  benefit,
                  style: GoogleFonts.poppins(
                    fontSize: 10,
                    fontWeight: FontWeight.w500,
                    color: isDark ? Colors.white70 : AppColors.primaryDark.withValues(alpha: 0.7),
                  ),
                ),
              )).toList(),
            ),
          ],
        ],
      ),
    );
  }
}
