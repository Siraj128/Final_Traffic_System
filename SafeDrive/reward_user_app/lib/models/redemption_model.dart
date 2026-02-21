class RewardModel {
  final int id;
  final String title;
  final String description;
  final int pointsRequired;
  final String category;
  final String vendorName;
  final String? imageUrl;

  RewardModel({
    required this.id,
    required this.title,
    required this.description,
    required this.pointsRequired,
    required this.category,
    required this.vendorName,
    this.imageUrl,
  });

  factory RewardModel.fromJson(Map<String, dynamic> json) {
    return RewardModel(
      id: json['reward_id'],
      title: json['title'],
      description: json['description'],
      pointsRequired: json['points_required'],
      category: json['category'],
      vendorName: json['vendor_name'],
      imageUrl: json['image_url'],
    );
  }
}

class RedemptionHistoryModel {
  final int id;
  final String rewardTitle;
  final int pointsSpent;
  final String couponCode;
  final DateTime timestamp;
  final String status;

  RedemptionHistoryModel({
    required this.id,
    required this.rewardTitle,
    required this.pointsSpent,
    required this.couponCode,
    required this.timestamp,
    required this.status,
  });

  factory RedemptionHistoryModel.fromJson(Map<String, dynamic> json) {
    return RedemptionHistoryModel(
      id: json['transaction_id'],
      rewardTitle: json['reward_title'],
      pointsSpent: json['points_spent'],
      couponCode: json['coupon_code'],
      timestamp: DateTime.parse(json['timestamp']),
      status: json['status'],
    );
  }
}
