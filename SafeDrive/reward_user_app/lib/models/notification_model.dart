class NotificationModel {
  final int id;
  final String title;
  final String message;
  final String type; // REWARD, VIOLATION, TOLL
  final DateTime timestamp;
  final bool isRead;

  NotificationModel({
    required this.id,
    required this.title,
    required this.message,
    required this.type,
    required this.timestamp,
    required this.isRead,
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    return NotificationModel(
      id: json['notification_id'],
      title: json['title'],
      message: json['message'],
      type: json['limit_type'],
      timestamp: DateTime.parse(json['timestamp']),
      isRead: json['is_read'],
    );
  }
}
