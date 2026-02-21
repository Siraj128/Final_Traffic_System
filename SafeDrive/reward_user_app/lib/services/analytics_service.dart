import '../models/analytics_model.dart';
import 'api_service.dart';
import 'session_manager.dart';

class AnalyticsService {
  static Future<AnalyticsModel?> getAnalytics() async {
    try {
      final vehicleId = await SessionManager.getSelectedVehicleId();
      if (vehicleId == null) return null;

      final response = await ApiService.getAnalytics(vehicleId);

      if (response != null && response is Map && response.containsKey('driving_score')) {
        return AnalyticsModel.fromJson(Map<String, dynamic>.from(response));
      }
    } catch (e) {
      // debugPrint("Analytics Fetch Error: $e");
    }
    return null;
  }
}
