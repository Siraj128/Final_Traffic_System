import 'dart:convert';
import 'package:http/http.dart' as http;
import '../utils/api_constants.dart';
import '../models/redemption_model.dart';
import 'auth_service.dart';

class RedemptionService {
  static Future<List<RewardModel>> getCatalog() async {
    try {
      final token = await AuthService.getToken();
      if (token == null) return [];

      final response = await http.get(
        Uri.parse("${ApiConstants.baseUrl}/rewards/catalog"),
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer $token"
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((e) => RewardModel.fromJson(e)).toList();
      }
    } catch (e) {
      // debugPrint("Catalog Fetch Error: $e");
    }
    return [];
  }

  static Future<Map<String, dynamic>> redeemReward(int rewardId) async {
    try {
      final token = await AuthService.getToken();
      final plate = await AuthService.getPlateNumber();
      
      if (token == null || plate == null) return {"success": false, "message": "Auth Error"};

      final response = await http.post(
        Uri.parse("${ApiConstants.baseUrl}/rewards/redeem"),
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer $token"
        },
        body: jsonEncode({
          "plate_number": plate,
          "reward_id": rewardId
        }),
      );

      final data = jsonDecode(response.body);
      if (response.statusCode == 200) {
         return {"success": true, "message": "Redeemed!", "coupon": data['coupon_code']};
      } else {
         return {"success": false, "message": data['detail'] ?? "Redemption Failed"};
      }
    } catch (e) {
      return {"success": false, "message": e.toString()};
    }
  }
}
