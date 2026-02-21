import '../models/leaderboard_model.dart';
import 'api_service.dart';
import 'auth_service.dart';
import 'session_manager.dart';

class LeaderboardService {
  static Future<List<LeaderboardEntry>> getTopDrivers({int offset = 0, int limit = 20}) async {
    try {
      final List<dynamic> data = await ApiService.getTopDrivers(offset: offset, limit: limit);
      return data.map((e) => LeaderboardEntry.fromJson(Map<String, dynamic>.from(e))).toList();
    } catch (e) {
      // debugPrint("Leaderboard Fetch Error: $e");
    }
    return [];
  }

  static Future<LeaderboardEntry?> getUserRank() async {
    try {
      final driverId = await SessionManager.getUserIdInt();
      if (driverId == null) return null;

      final data = await ApiService.getUserRank(driverId);
      if (data != null && data is Map && !data.containsKey('success')) {
        return LeaderboardEntry.fromJson(Map<String, dynamic>.from(data));
      }
    } catch (e) {
      // debugPrint("User Rank Fetch Error: $e");
    }
    return null;
  }
}

