class WalletModel {
  final String plateNumber;
  final int walletPoints;
  final double complianceScore;

  WalletModel({
    required this.plateNumber,
    required this.walletPoints,
    required this.complianceScore,
  });

  factory WalletModel.fromJson(Map<String, dynamic> json) {
    return WalletModel(
      plateNumber: json['plate_number'] ?? '',
      walletPoints: json['wallet_points'] ?? 0,
      complianceScore: (json['compliance_score'] ?? 0).toDouble(),
    );
  }
}
