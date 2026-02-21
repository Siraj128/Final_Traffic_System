class BenefitsModel {
  final String tier;
  final int totalCredits;
  final double nextTierProgress;
  final int nextTierTarget;
  final int parkingQuota;
  final int fuelCashback;
  final int serviceCoupons;
  final bool greenWaveEligible;

  BenefitsModel({
    required this.tier,
    required this.totalCredits,
    required this.nextTierProgress,
    required this.nextTierTarget,
    required this.parkingQuota,
    required this.fuelCashback,
    required this.serviceCoupons,
    required this.greenWaveEligible,
  });

  factory BenefitsModel.fromJson(Map<String, dynamic> json) {
    return BenefitsModel(
      tier: json['tier'],
      totalCredits: json['total_credits'],
      nextTierProgress: (json['next_tier_progress'] as num).toDouble(),
      nextTierTarget: json['next_tier_target'],
      parkingQuota: json['parking_quota'],
      fuelCashback: json['fuel_cashback'],
      serviceCoupons: json['service_coupon_count'],
      greenWaveEligible: json['green_wave_eligible'],
    );
  }
}
