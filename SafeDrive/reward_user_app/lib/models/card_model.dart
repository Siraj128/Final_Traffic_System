class VirtualCardModel {
  final String cardNumber;
  final String expiryDate;
  final String cvv;
  final String cardBalance;
  final bool isFrozen;
  final String ownerName;

  VirtualCardModel({
    required this.cardNumber,
    required this.expiryDate,
    required this.cvv,
    required this.cardBalance,
    required this.isFrozen,
    required this.ownerName,
  });

  factory VirtualCardModel.fromJson(Map<String, dynamic> json) {
    return VirtualCardModel(
      cardNumber: json['card_number'] ?? '**** **** **** ****',
      expiryDate: json['expiry_date'] ?? 'MM/YY',
      cvv: json['cvv'] ?? '***',
      cardBalance: json['card_balance']?.toString() ?? '0',
      isFrozen: json['is_frozen'] ?? false,
      ownerName: json['owner_name'] ?? '',
    );
  }
}
