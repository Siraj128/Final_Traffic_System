class AnalyticsModel {
  final String plateNumber;
  final double drivingScore;
  final String riskLevel;
  final int safeStreakDays;
  final int totalRewards;
  final int totalViolations;
  final List<String> insights;

  AnalyticsModel({
    required this.plateNumber,
    required this.drivingScore,
    required this.riskLevel,
    required this.safeStreakDays,
    required this.totalRewards,
    required this.totalViolations,
    required this.insights,
  });

  factory AnalyticsModel.fromJson(Map<String, dynamic> json) {
    return AnalyticsModel(
      plateNumber: json['plate_number'],
      drivingScore: (json['driving_score'] as num).toDouble(),
      riskLevel: json['risk_level'],
      safeStreakDays: json['safe_streak_days'],
      totalRewards: json['total_rewards'],
      totalViolations: json['total_violations'],
      insights: List<String>.from(json['insights'] ?? []),
    );
  }
}
