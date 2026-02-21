import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'session_manager.dart';
import 'dart:async';

class ApiService {
  static const String baseUrl = 'http://192.168.0.103:5000/api';
  static const String aiUrl = 'http://192.168.0.103:5001';

  static const bool isDemoMode = false;

  static Future<dynamic> get(String url) async {
    return _safeGet(url);
  }

  static Future<dynamic> post(String url, Map<String, dynamic> body) async {
    return _safePost(url, body);
  }

  // RTO Lookup
  static Future<dynamic> rtoLookup(String plateNumber) async {
    return _safePost('$baseUrl/auth/rto/lookup', {"plate_number": plateNumber});
  }

  static dynamic _processResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      final body = jsonDecode(response.body);
      if (body is Map && (body.containsKey('token') || body.containsKey('access_token'))) {
        return {
          "success": true,
          "token": body['token'] ?? body['access_token'],
          "user": body['user'],
          "data": body['user'] ?? body
        };
      }
      return body;
    } else {
      try {
        final error = jsonDecode(response.body);
        return {
          "success": false,
          "message": error is Map ? (error['msg'] ?? error['detail'] ?? "Request failed") : "Request failed"
        };
      } catch (_) {
         return {"success": false, "message": "Server error: ${response.statusCode}"};
      }
    }
  }

  static Future<Map<String, String>> _getHeaders() async {
    final token = await SessionManager.getToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  static Future<dynamic> _safePost(String url, Map<String, dynamic> body) async {
    try {
      final headers = await _getHeaders();
      final response = await http.post(
        Uri.parse(url),
        headers: headers,
        body: jsonEncode(body),
      ).timeout(const Duration(seconds: 10));
      return _processResponse(response);
    } on SocketException {
      return {"success": false, "message": "No Internet Connection"};
    } on TimeoutException {
       return {"success": false, "message": "Connection Timed Out"};
    } catch (e) {
      return {"success": false, "message": e.toString()};
    }
  }
  
  static Future<dynamic> _safeGet(String url) async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse(url),
        headers: headers,
      ).timeout(const Duration(seconds: 10));
      return _processResponse(response);
    } on SocketException {
      return {"success": false, "message": "No Internet Connection"};
    } on TimeoutException {
       return {"success": false, "message": "Connection Timed Out"};
    } catch (e) {
      return {"success": false, "message": e.toString()};
    }
  }

  static Future<dynamic> _safePut(String url, Map<String, dynamic> body) async {
    try {
      final headers = await _getHeaders();
      final response = await http.put(
        Uri.parse(url),
        headers: headers,
        body: jsonEncode(body),
      ).timeout(const Duration(seconds: 10));
      return _processResponse(response);
    } on SocketException {
      return {"success": false, "message": "No Internet Connection"};
    } on TimeoutException {
       return {"success": false, "message": "Connection Timed Out"};
    } catch (e) {
      return {"success": false, "message": e.toString()};
    }
  }

  static Future<dynamic> register({
    required String ownerName,
    required String email,
    required String password,
    required String plateNumber,
    required String mobileNumber,
    String vehicleType = 'Car',
  }) async {
    return post('$baseUrl/auth/register', {
      'owner_name': ownerName,
      'email': email,
      'password': password,
      'plate_number': plateNumber,
      'mobile': mobileNumber,
      'vehicle_type': vehicleType
    });
  }

  static Future<dynamic> login(String identifier, String password) async {
     return post('$baseUrl/auth/login', {
       'identifier': identifier,
       'password': password,
     });
  }

  static Future<dynamic> googleLogin({required Map<String, dynamic> userDetails}) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/google'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(userDetails),
      ).timeout(const Duration(seconds: 10));
      
      final responseBody = jsonDecode(response.body);
      if (responseBody['isNewUser'] == true) {
        return responseBody;
      }
      return _processResponse(response);
    } catch (e) {
      return {"success": false, "message": e.toString()};
    }
  }

  static Future<dynamic> googleRegister(Map<String, dynamic> data) async {
    return post('$baseUrl/auth/google/register', data);
  }

  // --- Vehicle Management ---
  static Future<List<dynamic>> getMyVehicles() async {
    final res = await get('$baseUrl/vehicles/my');
    if (res is List) return res;
    if (res is Map && res['success'] == true && res['data'] is List) return res['data'];
    return [];
  }

  static Future<dynamic> addVehicle(Map<String, dynamic> vehicleData) async {
    return post('$baseUrl/vehicles/add', vehicleData);
  }

  static Future<dynamic> setPrimaryVehicle(int vehicleId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.patch(
        Uri.parse('$baseUrl/vehicles/set-primary/$vehicleId'),
        headers: headers,
      ).timeout(const Duration(seconds: 10));
      return _processResponse(response);
    } catch (e) {
      return {"success": false, "message": e.toString()};
    }
  }

  static Future<dynamic> deleteVehicle(int vehicleId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.delete(
        Uri.parse('$baseUrl/vehicles/delete/$vehicleId'),
        headers: headers,
      ).timeout(const Duration(seconds: 10));
      return _processResponse(response);
    } catch (e) {
      return {"success": false, "message": e.toString()};
    }
  }

  // --- Profile & Wallet (Unified) ---
  static Future<dynamic> getUserProfile() async {
    return get('$baseUrl/auth/me');
  }

  static Future<dynamic> updateUserProfile(String plateNumber, Map<String, dynamic> data) async {
    return _safePut('$baseUrl/auth/update', data);
  }

  static Future<dynamic> getWallet() async {
    return get('$baseUrl/wallet/my');
  }

  static Future<List<dynamic>> getTransactionHistory() async {
    final res = await get('$baseUrl/wallet/history');
    if (res is List) return res;
    return [];
  }

  // --- Feature Specific (Vehicle-Aware) ---
  static Future<dynamic> getAnalytics(int vehicleId) async {
    return get('$baseUrl/analytics/vehicle/$vehicleId');
  }

  static Future<dynamic> getCardDetails() async {
    return get('$baseUrl/card/my');
  }

  static Future<List<dynamic>> getNotifications() async {
    final res = await get('$baseUrl/notifications/my');
    if (res is List) return res;
    return [];
  }

  // --- Leaderboard & Rewards ---
  static Future<List<dynamic>> getTopDrivers({int offset = 0, int limit = 50}) async {
    final res = await get('$baseUrl/leaderboard/top?offset=$offset&limit=$limit');
    if (res is List) return res;
    return []; 
  }

  static Future<dynamic> getUserRank(int driverId) async {
    final res = await get('$baseUrl/leaderboard/driver/$driverId');
    return res;
  }

  static Future<dynamic> getRewardsCatalog() async {
    return get('$baseUrl/rewards/catalog');
  }

  static Future<dynamic> redeemReward(int rewardId) async {
    return post('$baseUrl/rewards/redeem', {'reward_id': rewardId});
  }

  static Future<List<dynamic>> getRedemptionHistory() async {
    final res = await get('$baseUrl/rewards/history');
    if (res is List) return res;
    return [];
  }

  // --- AI Detection ---
  static Future<dynamic> detectImage(File imageFile) async {
    try {
      var request = http.MultipartRequest('POST', Uri.parse('$aiUrl/detect'));
      request.files.add(await http.MultipartFile.fromPath('image', imageFile.path));
      
      var streamedResponse = await request.send().timeout(const Duration(seconds: 15));
      var response = await http.Response.fromStream(streamedResponse);
      
      return _processResponse(response);
    } catch (e) {
      return {
        "success": true, 
        "vehicle_count": 1, 
        "violation_type": "None", 
        "plates": ["MOCK-123"]
      }; 
    }
  }

  static Future<void> uploadDetectionResult(String vehicleNumber, String violationType) async {
    await post('$baseUrl/events/violation', {
      'plate_number': vehicleNumber,
      'violation_type': violationType,
      'penalty_points': 50,
      'junction_id': 'AUTO-SCANNER'
    });
  }

  // --- RTO Email OTP ---
  static Future<dynamic> sendRtoEmailOtp(String email, String plate) async {
    return _safePost('$baseUrl/auth/rto/send-email-otp', {"email": email, "plate": plate});
  }

  static Future<dynamic> verifyRtoEmailOtp(String email, String otp) async {
    return _safePost('$baseUrl/auth/rto/verify-email-otp', {"email": email, "otp": otp});
  }
}
