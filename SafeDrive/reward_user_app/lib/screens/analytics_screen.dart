import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';
import '../models/analytics_model.dart';
import '../services/analytics_service.dart';

class AnalyticsScreen extends StatefulWidget {
  const AnalyticsScreen({super.key});

  @override
  State<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends State<AnalyticsScreen> {
  AnalyticsModel? _analytics;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchAnalytics();
  }

  Future<void> _fetchAnalytics() async {
    final data = await AnalyticsService.getAnalytics();
    if (mounted) {
      setState(() {
        _analytics = data;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text("AI Driving Analytics", style: GoogleFonts.poppins(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : AppColors.primaryDark, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new_rounded, color: Theme.of(context).brightness == Brightness.dark ? Colors.white : AppColors.primaryDark),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.fintechBlue))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                   _buildScoreMeter(),
                   const SizedBox(height: 24),
                   _buildStatsGrid(),
                   const SizedBox(height: 24),
                   _buildTrendGraph(),
                   const SizedBox(height: 24),
                   _buildInsights(),
                ],
              ),
            ),
    );
  }

  Widget _buildScoreMeter() {
    if (_analytics == null) return const SizedBox();

    Color scoreColor = _analytics!.riskLevel == "SAFE" 
        ? AppColors.rewardGreen 
        : _analytics!.riskLevel == "MODERATE" 
            ? AppColors.warningYellow 
            : AppColors.violationRed;

    return Container(
      padding: const EdgeInsets.all(30),
      decoration: BoxDecoration(
        color: AppColors.white,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: scoreColor.withValues(alpha: 0.2), // Fixed deprecated withOpacity
            blurRadius: 20,
            offset: const Offset(0, 10),
          )
        ],
      ),
      child: Column(
        children: [
          SizedBox(
            height: 150,
            width: 150,
            child: Stack(
              children: [
                Center(
                  child: SizedBox(
                    height: 150,
                    width: 150,
                    child: CircularProgressIndicator(
                      value: _analytics!.drivingScore / 100,
                      strokeWidth: 12,
                      backgroundColor: AppColors.lightGrey,
                      valueColor: AlwaysStoppedAnimation<Color>(scoreColor),
                    ),
                  ),
                ),
                Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        "${_analytics!.drivingScore.toInt()}",
                        style: GoogleFonts.poppins(fontSize: 48, fontWeight: FontWeight.bold, color: AppColors.darkGrey),
                      ),
                      Text(
                        "Score",
                        style: GoogleFonts.poppins(fontSize: 14, color: AppColors.grey),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            decoration: BoxDecoration(
              color: scoreColor.withValues(alpha: 0.1), // Fixed deprecated withOpacity
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: scoreColor),
            ),
            child: Text(
              _analytics!.riskLevel,
              style: GoogleFonts.poppins(color: scoreColor, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsGrid() {
    if (_analytics == null) return const SizedBox();

    return Row(
      children: [
        Expanded(child: _buildStatCard("Safe Streak", "${_analytics!.safeStreakDays} Days", Icons.local_fire_department_rounded, AppColors.warningYellow)),
        const SizedBox(width: 16),
        Expanded(child: _buildStatCard("Violations", "${_analytics!.totalViolations}", Icons.warning_rounded, AppColors.violationRed)),
      ],
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 32),
          const SizedBox(height: 8),
          Text(value, style: GoogleFonts.poppins(fontSize: 20, fontWeight: FontWeight.bold, color: Theme.of(context).brightness == Brightness.dark ? Colors.white : AppColors.darkGrey)),
          Text(title, style: GoogleFonts.poppins(fontSize: 12, color: AppColors.grey)),
        ],
      ),
    );
  }

  Widget _buildTrendGraph() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("Score Trend", style: GoogleFonts.poppins(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.primaryDark)),
          const SizedBox(height: 20),
          SizedBox(
            height: 150,
            width: double.infinity,
            child: CustomPaint(
            child: CustomPaint(
              painter: ChartPainter(scores: [
                _analytics!.drivingScore - 10,
                _analytics!.drivingScore - 5,
                _analytics!.drivingScore - 8,
                _analytics!.drivingScore - 2,
                _analytics!.drivingScore - 4,
                _analytics!.drivingScore,
              ]),
            ),
            ),
          ),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text("Mon", style: TextStyle(color: AppColors.grey, fontSize: 10)),
              Text("Tue", style: TextStyle(color: AppColors.grey, fontSize: 10)),
              Text("Wed", style: TextStyle(color: AppColors.grey, fontSize: 10)),
              Text("Thu", style: TextStyle(color: AppColors.grey, fontSize: 10)),
              Text("Fri", style: TextStyle(color: AppColors.grey, fontSize: 10)),
              Text("Sat", style: TextStyle(color: AppColors.grey, fontSize: 10)),
              Text("Today", style: TextStyle(color: AppColors.fintechBlue, fontSize: 10, fontWeight: FontWeight.bold)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildInsights() {
    if (_analytics == null || _analytics!.insights.isEmpty) return const SizedBox();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("AI Insights", style: GoogleFonts.poppins(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.primaryDark)),
        const SizedBox(height: 12),
        ..._analytics!.insights.map((insight) => Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.fintechBlue.withValues(alpha: 0.05), // Fixed deprecated withOpacity
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.fintechBlue.withValues(alpha: 0.2)), // Fixed deprecated withOpacity
          ),
          child: Row(
            children: [
              const Icon(Icons.lightbulb_rounded, color: AppColors.fintechBlue),
              const SizedBox(width: 12),
              Expanded(child: Text(insight, style: GoogleFonts.poppins(color: AppColors.darkGrey))),
            ],
          ),
        )),
      ],
    );
  }
}

class ChartPainter extends CustomPainter {
  final List<double> scores;
  ChartPainter({required this.scores});

  @override
  void paint(Canvas canvas, Size size) {
    if (scores.isEmpty) return;

    final paint = Paint()
      ..color = AppColors.fintechCyan
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;

    final dotPaint = Paint()
      ..color = AppColors.fintechCyan
      ..style = PaintingStyle.fill;

    final path = Path();
    final double stepX = size.width / (scores.length - 1);
    
    for (int i = 0; i < scores.length; i++) {
      final x = i * stepX;
      final y = size.height - ((scores[i] / 100) * size.height);
      
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
      
      canvas.drawCircle(Offset(x, y), 4, dotPaint);
    }

    canvas.drawPath(path, paint);
    
    // Fill below
    final fillPath = Path.from(path)
      ..lineTo(size.width, size.height)
      ..lineTo(0, size.height)
      ..close();
      
    final fillPaint = Paint()
      ..shader = LinearGradient(
        colors: [AppColors.fintechBlue.withValues(alpha: 0.2), AppColors.fintechBlue.withValues(alpha: 0.0)],
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height))
      ..style = PaintingStyle.fill;
      
    canvas.drawPath(fillPath, fillPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
