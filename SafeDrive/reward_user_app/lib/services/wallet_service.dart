import 'dart:convert';
import 'package:http/http.dart' as http;
import '../utils/api_constants.dart';
import '../models/wallet_model.dart';
import '../models/transaction_model.dart';
import 'auth_service.dart';

class WalletService {
  // Get Wallet
  static Future<WalletModel?> getWallet() async {
    try {
      final token = await AuthService.getToken();
      final plate = await AuthService.getPlateNumber();
      
      if (token == null || plate == null) return null;

      final response = await http.get(
        Uri.parse("${ApiConstants.wallet}/my"),
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer $token"
        },
      );

      if (response.statusCode == 200) {
        return WalletModel.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      // debugPrint("Wallet Fetch Error: $e");
    }
    return null;
  }

  // Get History
  static Future<List<TransactionModel>> getHistory() async {
    try {
      final token = await AuthService.getToken();
      final plate = await AuthService.getPlateNumber();
      
      if (token == null || plate == null) return [];

      final response = await http.get(
        Uri.parse("${ApiConstants.wallet}/history"),
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer $token"
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.map((e) => TransactionModel.fromJson(e)).toList();
      }
    } catch (e) {
      // debugPrint("History Fetch Error: $e");
    }
    return [];
  }
}
