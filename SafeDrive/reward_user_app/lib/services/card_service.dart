import 'package:flutter/foundation.dart';
import '../utils/api_constants.dart';
import '../models/card_model.dart';
import 'api_service.dart';
import 'auth_service.dart';

class CardService {
  // Get Card
  static Future<VirtualCardModel?> getCard() async {
    try {
      final plate = await AuthService.getPlateNumber();
      if (plate == null) return null;

      final response = await ApiService.get("${ApiConstants.card}/$plate");
      if (response.containsKey('card_number')) {
         return VirtualCardModel.fromJson(response);
      }
    } catch (e) {
      debugPrint("Card Fetch Error: $e");
    }
    return null;
  }

  // Send OTP
  static Future<dynamic> sendOtp() async {
    try {
      final plate = await AuthService.getPlateNumber();
      if (plate == null) return {'success': false, 'message': 'User not found'};

      return await ApiService.post("${ApiConstants.card}/send-otp", {"plate_number": plate});
    } catch (e) {
      return {'success': false, 'message': 'Connection Error: $e'};
    }
  }

  // Resend Details with OTP
  static Future<dynamic> resendDetails(String otp) async {
    try {
      final plate = await AuthService.getPlateNumber();
      if (plate == null) return {'success': false, 'message': 'User vehicle not found'};

      return await ApiService.post("${ApiConstants.card}/resend-details", {
          "plate_number": plate,
          "otp": otp
      });
    } catch (e) {
      return {'success': false, 'message': 'Connection Error: $e'};
    }
  }

  static Future<dynamic> pay(int amount, String merchant) async {
    try {
      final plate = await AuthService.getPlateNumber();
      if (plate == null) return {"success": false, "message": "Auth Error"};

      return await ApiService.post(ApiConstants.pay, {
          "plate_number": plate,
          "amount": amount,
          "merchant": merchant
      });
    } catch (e) {
      return {"success": false, "message": e.toString()};
    }
  }
  
  // FASTag Pay
  static Future<dynamic> payFastag(int amount, String tollPlazaId) async {
    try {
      final plate = await AuthService.getPlateNumber();
      if (plate == null) return {"success": false, "message": "Auth Error"};

      return await ApiService.post(ApiConstants.fastagPay, {
          "plate_number": plate,
          "amount": amount,
          "toll_plaza_id": tollPlazaId
      });
    } catch (e) {
      return {"success": false, "message": e.toString()};
    }
  }

  // Freeze Card
  static Future<dynamic> freezeCard(bool freeze) async {
    try {
      final plate = await AuthService.getPlateNumber();
      if (plate == null) return {'success': false, 'message': 'User not found'};

      return await ApiService.post("${ApiConstants.card}/freeze", {
         "plate_number": plate,
         "freeze": freeze
      });
    } catch (e) {
      return {'success': false, 'message': 'Connection Error: $e'};
    }
  }

  // Redeem
  static Future<dynamic> redeem(int points, String type) async {
    return ApiService.post(ApiConstants.redeem, {
       "points": points,
       "redeem_type": type
    });
  } // End Class Default
}
