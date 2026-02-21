class LeaderboardEntry {
  final String plateNumber;
  final String ownerName;
  final int walletPoints;
  final double complianceScore;
  final double rankScore;
  final int rankPosition;
  final String? avatar;

  LeaderboardEntry({
    required this.plateNumber,
    required this.ownerName,
    required this.walletPoints,
    required this.complianceScore,
    required this.rankScore,
    required this.rankPosition,
    this.avatar,
  });

  factory LeaderboardEntry.fromJson(Map<String, dynamic> json) {
    return LeaderboardEntry(
      plateNumber: json['plate_number'],
      ownerName: json['owner_name'],
      walletPoints: json['wallet_points'],
      complianceScore: (json['compliance_score'] as num).toDouble(),
      rankScore: (json['rank_score'] as num).toDouble(),
      rankPosition: json['rank_position'],
      avatar: json['avatar'],
    );
  }
}
