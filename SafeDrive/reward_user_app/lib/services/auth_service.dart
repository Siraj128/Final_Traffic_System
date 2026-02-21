import 'package:shared_preferences/shared_preferences.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'api_service.dart';
import 'session_manager.dart';

class AuthService {
  // Login
  static Future<Map<String, dynamic>> login(String plateNumber, String password) async {
    try {
      final response = await ApiService.login(plateNumber, password);

      if (response.containsKey('token')) {
        final token = response['token'];
        final user = response['user'] ?? response['data'];
        
        // Use SessionManager for persistent login
        await SessionManager.saveLogin(
          email: user['email'] ?? '',
          token: token,
          name: user['owner_name'] ?? user['name'],
          plate: user['plate_number'] ?? user['vehicle_number'],
          userId: (user['driver_id'] ?? user['_id']).toString(),
          userData: user, // Save full object
        );
        
        print("AuthService: Session Saved for ${user['email']}");
        return {"success": true, "token": token, "user": user};
      } else {
        return {"success": false, "message": response['message'] ?? "Login failed"};
      }
    } catch (e) {
      return {"success": false, "message": e.toString()};
    }
  }

  // Demo Mode Auto Login
  static Future<Map<String, dynamic>> loginAsJudge() async {
    final judgeUser = {
      "name": "Hackathon Judge",
      "email": "judge@hackathon.com",
      "plate_number": "KA-01-DEMO",
      "tier": "Gold",
      "wallet_points": 5000,
      "compliance_score": 100.0,
      "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Judge"
    };

    await SessionManager.saveLogin(
      email: 'judge@hackathon.com',
      token: 'mock_token_judge',
      name: 'Hackathon Judge',
      plate: 'KA-01-DEMO',
      userId: '9999',
      userData: judgeUser,
    );
    
    return {
      "success": true, 
      "user": judgeUser
    };
  }

  // RTO Email Lookup
  static Future<Map<String, dynamic>> lookupRtoEmail(String plateNumber) async {
    try {
      final response = await ApiService.rtoLookup(plateNumber);
      return response; // Expects { success: true, email: ..., masked_email: ... }
    } catch (e) {
      return {"success": false, "message": e.toString()};
    }
  }

  // OTP Methods (Email)
  static Future<Map<String, dynamic>> sendRtoEmailOtp(String email, String plate) async {
    try {
      return await ApiService.sendRtoEmailOtp(email, plate);
    } catch (e) {
      return {"success": false, "message": e.toString()};
    }
  }

  static Future<Map<String, dynamic>> verifyRtoEmailOtp(String email, String otp) async {
     try {
       return await ApiService.verifyRtoEmailOtp(email, otp);
     } catch (e) {
       return {"success": false, "message": e.toString()};
     }
  }

  // Register
  static Future<Map<String, dynamic>> register(String plateNumber, String ownerName, String mobile, String password) async {
    try {
      final emailMock = "$plateNumber@safedrive.com";
      final response = await ApiService.register(
        ownerName: ownerName, 
        email: emailMock, 
        password: password, 
        plateNumber: plateNumber,
        mobileNumber: mobile,
      );

      if (response.containsKey('token')) {
        return {"success": true, "data": response['user']};
      } else {
        return {"success": false, "message": "Registration failed"};
      }
    } catch (e) {
      return {"success": false, "message": e.toString()};
    }
  }

  // Google Sign-In
  static Future<Map<String, dynamic>> signInWithGoogle() async {
    try {
      final GoogleSignIn googleSignIn = GoogleSignIn(
        serverClientId: "365563827239-u64cjukkoc9gb236gvi4g0fd2ogicnir.apps.googleusercontent.com",
      );
      
      // Ensure specific account selection every time
      await googleSignIn.signOut(); 
      
      final GoogleSignInAccount? googleUser = await googleSignIn.signIn();

      if (googleUser == null) {
        return {"success": false, "message": "Google Sign-In aborted"};
      }

      final GoogleSignInAuthentication googleAuth = await googleUser.authentication;
      final String? accessToken = googleAuth.accessToken;
      final String? idToken = googleAuth.idToken;

      if (idToken == null) {
         return {"success": false, "message": "Failed to retrieve Google ID token"};
      }
      
      final response = await ApiService.googleLogin(userDetails: {
        'idToken': idToken,
        'email': googleUser.email,
        'name': googleUser.displayName,
        'picture': googleUser.photoUrl,
        'googleId': googleUser.id,
      });
      print("AuthService: Google Login API Response: $response");

      // Safety check for response type
      if (response is! Map) {
        return {"success": false, "message": "Invalid server response format"};
      }
      
      // Check if New User (Needs Registration)
      if (response['isNewUser'] == true) {
         return {
           "success": true, 
           "isNewUser": true, 
           "googleData": response // Pass the entire response as it contains the fields
         };
      }
      
      // Existing User Login
      if (response.containsKey('token')) {
         final token = response['token'];
         final user = response['data'] ?? response['user']; 
         
         await SessionManager.saveLogin(
          email: user['email'] ?? '',
          token: token,
          name: user['name'] ?? user['owner_name'] ?? 'Driver',
          plate: user['vehicle_number'] ?? user['plate_number'],
          userId: (user['_id'] ?? user['driver_id']).toString(),
          userData: user,
         );
         
         return {"success": true, "data": user};
      } else {
         return {"success": false, "message": response['message'] ?? response['msg'] ?? "Google Login Failed"};
      }
    } catch (e) {
      print("Google Sign-In Error: $e");
      // Fallback/Mock logic can remain here if needed, or return error
      return {"success": false, "message": "Google Sign-In Error: $e"};
    }
  }

  // Complete Google Registration
  static Future<Map<String, dynamic>> completeGoogleRegistration({
    required String name,
    required String email,
    required String googleId,
    required String? avatar,
    required String vehicleNumber,
    required String vehicleType,
    required String fuelType,
    required String mobile,
    required String city,
    required String fastagId,
  }) async {
    try {
      final data = {
        "name": name,
        "email": email,
        "googleId": googleId,
        "avatar": avatar,
        "vehicle_number": vehicleNumber,
        "vehicle_type": vehicleType,
        "fuel_type": fuelType,
        "mobile": mobile,
        "city": city,
        "fastag_id": fastagId,
      };

      final response = await ApiService.googleRegister(data);

      if (response['success'] == true || response.containsKey('token')) {
         final token = response['token'];
         final user = response['data'] ?? response['user'];
         
         await SessionManager.saveLogin(
          email: user['email'],
          token: token,
          name: user['name'] ?? user['owner_name'],
          plate: user['plate_number'] ?? user['vehicle_number'],
          userId: (user['driver_id'] ?? user['_id']).toString(),
          userData: user,
         );
         
         return {"success": true, "data": user};
      } else {
        return {"success": false, "message": response['message'] ?? "Google registration failed"};
      }
    } catch (e) {
      return {"success": false, "message": e.toString()};
    }
  }



  // Logout
  static Future<void> logout() async {
    await SessionManager.logout();
  }
  // Get Token
  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('authToken');
  }

  // Check Session
  static Future<Map<String, dynamic>> checkSession() async {
    final bool loggedIn = await SessionManager.isLoggedIn();
    final String? token = await SessionManager.getToken();
    final String? plateNumber = await SessionManager.getSelectedVehicleNumber();

    print("AuthService: checkSession - isLoggedIn: $loggedIn, plate: $plateNumber");

    if (!loggedIn) {
      return {"loggedIn": false};
    }

    // Handle Mock Judge
    if (token == 'mock_token_judge') {
       return await loginAsJudge();
    }

    // Try to get cached data first
    final cachedUser = await SessionManager.getUserData();
    print("AuthService: Cached User Exists: ${cachedUser != null}");

    if (token != null) {
      try {
        // Attempt network fetch
        final userData = await ApiService.getUserProfile();
        
        if (userData is Map && (userData.containsKey('plate_number') || userData.containsKey('email'))) {
           print("AuthService: Session validated via API for $plateNumber");
           
           // Update cache with fresh data
            await SessionManager.saveLogin(
              email: userData['email'] ?? '',
              token: token ?? '',
              name: userData['owner_name'] ?? userData['name'],
              plate: userData['plate_number'] ?? userData['vehicle_number'],
              userId: (userData['driver_id'] ?? userData['_id']).toString(),
              userData: Map<String, dynamic>.from(userData),
            );
           
           return {"loggedIn": true, "user": userData};
        } else if (userData is Map && userData['success'] == false) {
           // Token potentially invalid if API explicitly rejects it
           print("AuthService: API rejected session");
           // Only logout if 401 Unauthorized, but here we just get {success: false}
           // For safety, if we have cache, let's use it unless we are sure it's an auth error.
           // But if API is reachable and says 'fail', it might be expired.
           // For now, let's allow fallback if cachedUser exists, OR logout if we trust the API error.
           // Let's assume explicit failure = logout.
        }
      } catch (e) {
        print("AuthService: Network/API error: $e");
        print("AuthService: Falling back to cached session.");
      }
    }

    // Fallback to cache if API failed or threw exception (offline)
    if (cachedUser != null) {
      return {"loggedIn": true, "user": cachedUser};
    }

    return {"loggedIn": false};
  }

  // Get Saved Plate
  static Future<String?> getPlateNumber() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('vehicleNumber');
  }
}
