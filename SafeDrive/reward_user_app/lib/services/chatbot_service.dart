import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_service.dart';

class ChatbotService {
  static Future<Map<String, String>> getReply(String message) async {
    try {
      final lowerMsg = message.toLowerCase();

      // 1. Basic Content Relevance (NLP Filter)
      if (!_isTrafficRelated(lowerMsg)) {
        return {
          'reply': "I am specialized in traffic rules and road safety. How can I help you with fines or driving guidelines?",
          'fine': '',
          'impact': ''
        };
      }

      // 2. Call Backend AI Assistant
      final response = await ApiService.post('${ApiService.baseUrl}/assistant/query', {
        'message': message,
      });

      if (response != null && response is Map) {
        return {
          'reply': response['reply'] ?? 'I am currently learning more about this rule. Please refer to RTO handbook.',
          'fine': response['fine'] ?? '',
          'impact': response['impact'] ?? ''
        };
      }

      // 3. Fallback to Local logic if backend fails
      return _localFallback(lowerMsg);

    } catch (e) {
      return {
        'reply': "I'm having trouble connecting to my knowledge base. Please try again in a moment.",
        'fine': '',
        'impact': ''
      };
    }
  }

  static bool _isTrafficRelated(String message) {
    const keywords = [
      'fine', 'violation', 'rule', 'traffic', 'signal', 'helmet', 'license', 'pune', 
      'fastag', 'toll', 'parking', 'drunk', 'riding', 'seatbelt', 'speed', 'lane'
    ];
    return keywords.any((k) => message.contains(k));
  }

  static Map<String, String> _localFallback(String message) {
    if (message.contains('helmet')) {
      return {
        'reply': 'Wearing a helmet is mandatory. Fine is ₹500.',
        'fine': '₹500',
        'impact': '-2'
      };
    }
    return {
      'reply': 'Please follow traffic rules for a safer commute. Fines apply for violations.',
      'fine': 'Varies',
      'impact': 'Negative'
    };
  }
}
