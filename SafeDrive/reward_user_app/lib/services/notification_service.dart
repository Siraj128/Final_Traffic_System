import '../models/notification_model.dart';
import 'api_service.dart';
import 'auth_service.dart';

class NotificationService {
  static Future<List<NotificationModel>> getNotifications() async {
    try {
      final List<dynamic> data = await ApiService.getNotifications();
      return data.map((e) => NotificationModel.fromJson(e)).toList();
    } catch (e) {
      // debugPrint("Notification Fetch Error: $e");
    }
    return [];
  }
}
