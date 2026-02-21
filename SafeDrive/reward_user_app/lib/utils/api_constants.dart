class ApiConstants {
  // Use 10.0.2.2 for Android Emulator to access localhost
  // static const String baseUrl = "http://10.0.2.2:5000";
  // Physical Device (Your static IP)
  static const String baseUrl = "http://192.168.0.103:5000/api";
  
  // Auth
  static const String login = "$baseUrl/auth/login";
  static const String register = "$baseUrl/auth/register";
  
  // Wallet
  static const String wallet = "$baseUrl/wallet"; // + /{plate_number}
  static const String transactions = "$baseUrl/wallet"; // + /{plate_number}/history
  
  // Card
  static const String card = "$baseUrl/card"; // + /{plate_number}
  static const String freezeCard = "$baseUrl/card/freeze";
  static const String pay = "$baseUrl/card/pay"; // Legacy
  static const String fastagPay = "$baseUrl/card/fastag/pay";
  static const String redeem = "$baseUrl/card/redeem";
}
