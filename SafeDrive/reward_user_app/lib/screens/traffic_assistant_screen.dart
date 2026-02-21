import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import '../constants/app_colors.dart';
import '../models/message_model.dart';
import '../services/chatbot_service.dart';

class TrafficAssistantScreen extends StatefulWidget {
  const TrafficAssistantScreen({super.key});

  @override
  State<TrafficAssistantScreen> createState() => _TrafficAssistantScreenState();
}

class _TrafficAssistantScreenState extends State<TrafficAssistantScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<MessageModel> _messages = [
    MessageModel(
      text: "Hello! I am your SafeDrive Traffic Assistant. How can I help you with traffic rules or fines today?",
      sender: MessageSender.bot,
      timestamp: DateTime.now(),
    ),
  ];
  bool _isTyping = false;

  final List<String> _suggestions = [
    "Signal violation fine",
    "Helmet rule",
    "FASTag problem",
    "License renewal",
    "Wrong parking fine",
    "Pune traffic rules"
  ];

  void _sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    setState(() {
      _messages.add(MessageModel(
        text: text,
        sender: MessageSender.user,
        timestamp: DateTime.now(),
      ));
      _isTyping = true;
    });

    _controller.clear();
    _scrollToBottom();

    // Get reply from service
    final res = await ChatbotService.getReply(text);

    if (mounted) {
      setState(() {
        _isTyping = false;
        _messages.add(MessageModel(
          text: res['reply']!,
          sender: MessageSender.bot,
          timestamp: DateTime.now(),
          fineAmount: res['fine'],
          rewardImpact: res['impact'],
        ));
      });
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(100),
        child: Container(
          decoration: BoxDecoration(
            gradient: AppColors.primaryGradient,
            borderRadius: const BorderRadius.only(
              bottomLeft: Radius.circular(30),
              bottomRight: Radius.circular(30),
            ),
          ),
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white),
                    onPressed: () => Navigator.pop(context),
                  ),
                  const CircleAvatar(
                    backgroundColor: Colors.white24,
                    child: Icon(Icons.shield_rounded, color: Colors.white),
                  ),
                  const SizedBox(width: 15),
                  Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        "Traffic Assistant",
                        style: GoogleFonts.poppins(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        "Ask about traffic rules & fines",
                        style: GoogleFonts.poppins(
                          color: Colors.white70,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(20),
              itemCount: _messages.length,
              itemBuilder: (context, index) => _ChatBubble(
                message: _messages[index],
                width: width,
              ),
            ),
          ),
          if (_isTyping)
            const Padding(
              padding: EdgeInsets.only(left: 20, bottom: 10),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text("Assistant is typing...", style: TextStyle(color: Colors.grey, fontSize: 12, fontStyle: FontStyle.italic)),
              ),
            ),
          
          // Suggestions
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 10),
            child: Row(
              children: _suggestions.map((s) => Padding(
                padding: const EdgeInsets.symmetric(horizontal: 5),
                child: ActionChip(
                  label: Text(s, style: GoogleFonts.poppins(fontSize: 12)),
                  backgroundColor: isDark ? Colors.white10 : Colors.white,
                  onPressed: () => _sendMessage(s),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                ),
              )).toList(),
            ),
          ),

          // Input Bar
          Padding(
            padding: const EdgeInsets.all(20),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 15),
              decoration: BoxDecoration(
                color: isDark ? Colors.white.withValues(alpha: 0.05) : Colors.grey.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(30),
                border: Border.all(color: isDark ? Colors.white12 : Colors.black12),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      style: GoogleFonts.poppins(fontSize: 14),
                      decoration: InputDecoration(
                        hintText: "Ask traffic rule or violation...",
                        hintStyle: GoogleFonts.poppins(color: Colors.grey, fontSize: 14),
                        border: InputBorder.none,
                      ),
                      onSubmitted: _sendMessage,
                    ),
                  ),
                  IconButton(
                    icon: Icon(Icons.mic_none_rounded, color: AppColors.primaryPurple, size: 22),
                    onPressed: () {}, // Voice Input placeholder
                  ),
                  Container(
                    margin: const EdgeInsets.symmetric(vertical: 5),
                    decoration: BoxDecoration(
                      color: AppColors.primaryPurple,
                      shape: BoxShape.circle,
                    ),
                    child: IconButton(
                      icon: const Icon(Icons.send_rounded, color: Colors.white, size: 18),
                      onPressed: () => _sendMessage(_controller.text),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ChatBubble extends StatelessWidget {
  final MessageModel message;
  final double width;

  const _ChatBubble({required this.message, required this.width});

  @override
  Widget build(BuildContext context) {
    final isBot = message.sender == MessageSender.bot;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: Column(
        crossAxisAlignment: isBot ? CrossAxisAlignment.start : CrossAxisAlignment.end,
        children: [
          Container(
            constraints: BoxConstraints(maxWidth: width * 0.75),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: isBot 
                  ? (isDark ? Colors.white10 : Colors.grey.withValues(alpha: 0.15))
                  : AppColors.primaryPurple,
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(20),
                topRight: const Radius.circular(20),
                bottomLeft: Radius.circular(isBot ? 0 : 20),
                bottomRight: Radius.circular(isBot ? 20 : 0),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  message.text,
                  style: GoogleFonts.poppins(
                    color: isBot 
                        ? (isDark ? Colors.white : AppColors.primaryDark) 
                        : Colors.white,
                    fontSize: 14,
                  ),
                ),
                if (message.fineAmount != null && message.fineAmount!.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.red.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        "Fine: ${message.fineAmount}",
                        style: GoogleFonts.poppins(color: Colors.redAccent, fontSize: 12, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 5),
          Text(
            DateFormat('hh:mm a').format(message.timestamp),
            style: GoogleFonts.poppins(color: Colors.grey, fontSize: 10),
          ),
        ],
      ),
    );
  }
}
