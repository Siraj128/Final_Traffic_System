import 'package:flutter/material.dart';

enum MessageSender { user, bot }

class MessageModel {
  final String text;
  final MessageSender sender;
  final DateTime timestamp;
  final String? fineAmount;
  final String? rewardImpact;

  MessageModel({
    required this.text,
    required this.sender,
    required this.timestamp,
    this.fineAmount,
    this.rewardImpact,
  });

  Map<String, dynamic> toJson() => {
    'text': text,
    'sender': sender.index,
    'timestamp': timestamp.toIso8601String(),
    'fineAmount': fineAmount,
    'rewardImpact': rewardImpact,
  };

  factory MessageModel.fromJson(Map<String, dynamic> json) => MessageModel(
    text: json['text'],
    sender: MessageSender.values[json['sender']],
    timestamp: DateTime.parse(json['timestamp']),
    fineAmount: json['fineAmount'],
    rewardImpact: json['rewardImpact'],
  );
}
