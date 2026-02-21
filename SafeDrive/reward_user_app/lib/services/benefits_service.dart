import 'dart:convert';
import 'package:http/http.dart' as http;
import '../utils/api_constants.dart';
import '../models/benefits_model.dart';
import 'auth_service.dart';

class BenefitsService {
  static Future<BenefitsModel?> getBenefits() async {
    try {
      final token = await AuthService.getToken();
      final plate = await AuthService.getPlateNumber();
      
      if (token == null || plate == null) return null;

      final response = await http.get(
        Uri.parse("${ApiConstants.baseUrl}/driver/benefits/$plate"),
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer $token"
        },
      );

      if (response.statusCode == 200) {
        return BenefitsModel.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      // debugPrint("Benefits Fetch Error: $e");
    }
    return null;
  }
}
