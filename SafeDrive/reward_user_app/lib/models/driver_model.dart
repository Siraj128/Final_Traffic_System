class DriverModel {
  final int driverId;
  final String plateNumber;
  final String ownerName;
  final int walletPoints;
  final String tier;

  DriverModel({
    required this.driverId,
    required this.plateNumber,
    required this.ownerName,
    required this.walletPoints,
    required this.complianceScore,
    this.tier = 'Silver', // Default
  });

  factory DriverModel.fromJson(Map<String, dynamic> json) {
    return DriverModel(
      driverId: json['driver_id'] ?? 0,
      plateNumber: json['plate_number'] ?? '',
      ownerName: json['owner_name'] ?? '',
      walletPoints: json['wallet_points'] ?? 0,
      complianceScore: (json['compliance_score'] ?? 0).toDouble(),
      tier: json['tier'] ?? 'Silver',
    );
  }
}
