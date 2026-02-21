import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class SessionManager {
  static const String _keyIsLoggedIn = 'isLoggedIn';
  static const String _keyToken = 'authToken';
  static const String _keyEmail = 'userEmail';
  static const String _keyName = 'userName';
  static const String _keyPlate = 'vehicleNumber'; // Legacy/Primary fallback
  static const String _keyUserId = 'userId';
  static const String _keyUserData = 'userData'; 
  
  static const String _keySelectedVehicleId = 'selectedVehicleId';
  static const String _keySelectedVehicleNumber = 'selectedVehicleNumber';

  static Future<void> saveLogin({
    required String email,
    required String token,
    String? name,
    String? plate,
    String? userId,
    Map<String, dynamic>? userData,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyIsLoggedIn, true);
    await prefs.setString(_keyToken, token);
    await prefs.setString(_keyEmail, email);
    if (name != null) await prefs.setString(_keyName, name);
    if (userId != null) await prefs.setString(_keyUserId, userId);
    
    // Save full user object
    if (userData != null) {
      await prefs.setString(_keyUserData, jsonEncode(userData));
      
      // Auto-select primary vehicle
      final List? vehicles = userData['vehicles'];
      if (vehicles != null && vehicles.isNotEmpty) {
        final primary = vehicles.firstWhere((v) => v['is_primary'] == true, orElse: () => vehicles.first);
        await setSelectedVehicle(primary['vehicle_id'], primary['plate_number']);
      }
    }
  }

  static Future<bool> isLoggedIn() async {
    final prefs = await SharedPreferences.getInstance();
    final loggedIn = prefs.getBool(_keyIsLoggedIn) ?? false;
    final token = prefs.getString(_keyToken);
    return loggedIn && token != null;
  }

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyToken);
  }

  static Future<String?> getEmail() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyEmail);
  }

  static Future<String?> getUserName() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyName);
  }

  static Future<String?> getUserId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyUserId);
  }

  static Future<int?> getUserIdInt() async {
    final idStr = await getUserId();
    if (idStr != null) return int.tryParse(idStr);
    return null;
  }

  static Future<int?> getSelectedVehicleId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_keySelectedVehicleId);
  }

  static Future<String?> getSelectedVehicleNumber() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keySelectedVehicleNumber);
  }

  static Future<void> setSelectedVehicle(int id, String plate) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_keySelectedVehicleId, id);
    await prefs.setString(_keySelectedVehicleNumber, plate);
    await prefs.setString(_keyPlate, plate); // Sync legacy plate for compatibility
  }

  static Future<Map<String, dynamic>?> getUserData() async {
    final prefs = await SharedPreferences.getInstance();
    final String? dataString = prefs.getString(_keyUserData);
    if (dataString != null) {
      try {
        return jsonDecode(dataString) as Map<String, dynamic>;
      } catch (e) {
        return null;
      }
    }
    return null;
  }

  static Future<List<dynamic>> getUserVehicles() async {
    final userData = await getUserData();
    if (userData != null && userData['vehicles'] is List) {
      return userData['vehicles'];
    }
    return [];
  }

  static Future<void> updateUserData(Map<String, dynamic> userData) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyUserData, jsonEncode(userData));
  }

  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
  }
}
