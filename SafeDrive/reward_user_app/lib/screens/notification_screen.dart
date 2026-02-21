import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import '../constants/app_colors.dart';
import '../models/notification_model.dart';
import '../services/notification_service.dart';

class NotificationScreen extends StatefulWidget {
  const NotificationScreen({super.key});

  @override
  State<NotificationScreen> createState() => _NotificationScreenState();
}

class _NotificationScreenState extends State<NotificationScreen> {
  List<NotificationModel> _notifications = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchNotifications();
  }

  Future<void> _fetchNotifications() async {
    final data = await NotificationService.getNotifications();
    if (mounted) {
      setState(() {
        _notifications = data;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text("Notifications", style: GoogleFonts.poppins(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : AppColors.primaryDark, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new_rounded, color: Theme.of(context).brightness == Brightness.dark ? Colors.white : AppColors.primaryDark),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.primaryPurple))
          : _notifications.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.notifications_off_rounded, size: 60, color: AppColors.grey.withValues(alpha: 0.5)), // Fixed deprecated withOpacity
                      const SizedBox(height: 16),
                      Text("No new notifications", style: GoogleFonts.poppins(color: AppColors.grey)),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _notifications.length,
                  itemBuilder: (context, index) {
                    final note = _notifications[index];
                    return _buildNotificationCard(note);
                  },
                ),
    );
  }

  Widget _buildNotificationCard(NotificationModel note) {
    IconData icon;
    Color color;

    switch (note.type) {
      case "REWARD":
        icon = Icons.emoji_events_rounded;
        color = AppColors.rewardGreen;
        break;
      case "VIOLATION":
        icon = Icons.warning_rounded;
        color = AppColors.violationRed;
        break;
      case "TOLL":
        icon = Icons.toll_rounded;
        color = AppColors.primaryPurple;
        break;
      default:
        icon = Icons.notifications_rounded;
        color = AppColors.primaryPurple;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: note.isRead ? Theme.of(context).cardColor : AppColors.primaryPurple.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03), 
            blurRadius: 8,
            offset: const Offset(0, 4),
          )
        ],
        border: Border(left: BorderSide(color: color, width: 4)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Stack(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(icon, color: color, size: 20),
              ),
              if (!note.isRead)
                Positioned(
                  right: 0,
                  top: 0,
                  child: Container(
                    width: 10,
                    height: 10,
                    decoration: const BoxDecoration(
                      color: Colors.red,
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  note.title, 
                  style: GoogleFonts.poppins(
                    fontWeight: note.isRead ? FontWeight.w600 : FontWeight.bold, 
                    fontSize: 16,
                    color: Theme.of(context).brightness == Brightness.dark ? Colors.white : AppColors.darkGrey,
                  )
                ),
                const SizedBox(height: 4),
                Text(
                  note.message, 
                  style: GoogleFonts.poppins(
                    color: Theme.of(context).brightness == Brightness.dark ? Colors.white70 : AppColors.darkGrey, 
                    fontSize: 14,
                    fontWeight: note.isRead ? FontWeight.normal : FontWeight.w500,
                  )
                ),
                const SizedBox(height: 8),
                Text(
                  DateFormat('dd MMM, hh:mm a').format(note.timestamp.toLocal()),
                  style: GoogleFonts.poppins(color: AppColors.grey, fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
