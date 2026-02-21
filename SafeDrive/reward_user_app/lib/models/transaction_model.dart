class TransactionModel {
  final int transactionId;
  final String type;
  final int amount;
  final String description;
  final DateTime timestamp;

  TransactionModel({
    required this.transactionId,
    required this.type,
    required this.amount,
    required this.description,
    required this.timestamp,
  });

  factory TransactionModel.fromJson(Map<String, dynamic> json) {
    return TransactionModel(
      transactionId: json['transaction_id'] ?? 0,
      type: json['type'] ?? 'UNKNOWN',
      amount: json['amount'] ?? 0,
      description: json['description'] ?? '',
      timestamp: DateTime.parse(json['timestamp']),
    );
  }
}
