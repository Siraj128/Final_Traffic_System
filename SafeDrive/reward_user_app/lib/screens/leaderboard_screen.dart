import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../constants/app_colors.dart';
import '../models/leaderboard_model.dart';
import '../services/leaderboard_service.dart';

class LeaderboardScreen extends StatefulWidget {
  const LeaderboardScreen({super.key});

  @override
  State<LeaderboardScreen> createState() => _LeaderboardScreenState();
}

class _LeaderboardScreenState extends State<LeaderboardScreen> {
  final ScrollController _scrollController = ScrollController();
  List<LeaderboardEntry> _topDrivers = [];
  LeaderboardEntry? _myRank;
  bool _isLoading = true;
  bool _isLoadingMore = false;
  bool _hasMore = true;
  int _offset = 0;
  final int _limit = 20;

  @override
  void initState() {
    super.initState();
    _fetchInitialData();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _fetchInitialData() async {
    setState(() => _isLoading = true);
    final top = await LeaderboardService.getTopDrivers(offset: 0, limit: _limit);
    final myRank = await LeaderboardService.getUserRank();
    
    if (mounted) {
      setState(() {
        _topDrivers = top;
        _myRank = myRank;
        _isLoading = false;
        _offset = top.length;
        _hasMore = top.length >= _limit;
      });
    }
  }

  Future<void> _fetchMoreDrivers() async {
    if (_isLoadingMore || !_hasMore) return;

    setState(() => _isLoadingMore = true);
    final more = await LeaderboardService.getTopDrivers(offset: _offset, limit: _limit);
    
    if (mounted) {
      setState(() {
        _topDrivers.addAll(more);
        _isLoadingMore = false;
        _offset += more.length;
        _hasMore = more.length >= _limit;
      });
    }
  }

  void _onScroll() {
    if (_scrollController.position.pixels >= _scrollController.position.maxScrollExtent - 200) {
      _fetchMoreDrivers();
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text("Leaderboard", style: GoogleFonts.poppins(color: isDark ? Colors.white : AppColors.primaryDark, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new_rounded, color: isDark ? Colors.white : AppColors.primaryDark),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.primaryPurple))
          : Column(
              children: [
                const SizedBox(height: 20),
                if (_topDrivers.length >= 3) _buildPodium(),
                const SizedBox(height: 20),
                if (_myRank != null) _buildMyRankCard(),
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    decoration: BoxDecoration(
                      color: Theme.of(context).cardColor,
                      borderRadius: const BorderRadius.only(topLeft: Radius.circular(30), topRight: Radius.circular(30)),
                    ),
                    child: Column(
                      children: [
                        const SizedBox(height: 20),
                        Text(
                          "Global Rankings", 
                          style: GoogleFonts.poppins(
                            fontSize: 18, 
                            fontWeight: FontWeight.bold, 
                            color: isDark ? Colors.white : AppColors.primaryDark
                          )
                        ),
                        const SizedBox(height: 10),
                        Expanded(
                          child: ListView.separated(
                            controller: _scrollController,
                            itemCount: _topDrivers.isEmpty ? 0 : (_topDrivers.length - 3 < 0 ? 0 : _topDrivers.length - 3) + (_hasMore ? 1 : 0),
                            separatorBuilder: (_, __) => Divider(color: Theme.of(context).dividerColor),
                            itemBuilder: (context, index) {
                              if (index == (_topDrivers.length - 3 < 0 ? 0 : _topDrivers.length - 3)) {
                                return const Padding(
                                  padding: EdgeInsets.symmetric(vertical: 20),
                                  child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
                                );
                              }
                              final driver = _topDrivers[index + 3];
                              return _buildDriverTile(driver);
                            },
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

  Widget _buildPodium() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        _buildPodiumStep(_topDrivers[1], 2, 140, const Color(0xFFC0C0C0)), // Silver
        _buildPodiumStep(_topDrivers[0], 1, 170, const Color(0xFFFFD700)), // Gold
        _buildPodiumStep(_topDrivers[2], 3, 120, const Color(0xFFCD7F32)), // Bronze
      ],
    );
  }

  Widget _buildPodiumStep(LeaderboardEntry driver, int rank, double height, Color color) {
    return Column(
      children: [
        _buildAvatar(driver, radius: 24),
        const SizedBox(height: 8),
        Container(
          width: 90,
          height: height,
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.2),
            borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
            border: Border.all(color: color, width: 2),
            boxShadow: [
              BoxShadow(
                color: color.withValues(alpha: 0.3),
                blurRadius: 10,
                offset: const Offset(0, -2),
              )
            ],
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text("$rank", style: GoogleFonts.poppins(fontSize: 32, fontWeight: FontWeight.bold, color: color)),
              const SizedBox(height: 4),
              Text(
                "${driver.walletPoints}",
                style: GoogleFonts.poppins(
                  fontSize: 14, 
                  fontWeight: FontWeight.w600, 
                  color: Theme.of(context).brightness == Brightness.dark ? Colors.white70 : AppColors.darkGrey
                ),
              ),
              Text("pts", style: GoogleFonts.poppins(fontSize: 10, color: AppColors.grey)),
              const SizedBox(height: 8),
              Padding(
                 padding: const EdgeInsets.symmetric(horizontal: 4),
                 child: Text(
                  driver.ownerName,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: GoogleFonts.poppins(fontSize: 12, fontWeight: FontWeight.w500),
                  textAlign: TextAlign.center,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildAvatar(LeaderboardEntry driver, {double radius = 20}) {
    if (driver.avatar != null && driver.avatar!.startsWith('http')) {
      return CircleAvatar(
        radius: radius,
        backgroundColor: Colors.transparent,
        child: ClipOval(
          child: CachedNetworkImage(
            imageUrl: driver.avatar!,
            placeholder: (context, url) => const CircularProgressIndicator(strokeWidth: 2),
            errorWidget: (context, url, error) => _buildInitialAvatar(driver, radius),
            fit: BoxFit.cover,
            width: radius * 2,
            height: radius * 2,
          ),
        ),
      );
    }
    return _buildInitialAvatar(driver, radius);
  }

  Widget _buildInitialAvatar(LeaderboardEntry driver, double radius) {
    return CircleAvatar(
      radius: radius,
      backgroundColor: AppColors.primaryPurple,
      child: Text(
        driver.ownerName[0].toUpperCase(),
        style: GoogleFonts.poppins(fontWeight: FontWeight.bold, color: Colors.white, fontSize: radius * 0.8),
      ),
    );
  }

  Widget _buildMyRankCard() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: AppColors.primaryGradient,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryPurple.withValues(alpha: 0.3),
            blurRadius: 10,
            offset: const Offset(0, 4),
          )
        ],
      ),
      child: Row(
        children: [
          Text(
            "#${_myRank!.rankPosition}",
            style: GoogleFonts.poppins(fontSize: 24, fontWeight: FontWeight.bold, color: AppColors.white),
          ),
          const SizedBox(width: 16),
          _buildAvatar(_myRank!, radius: 18),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("My Rank", style: GoogleFonts.poppins(fontSize: 12, color: AppColors.white.withValues(alpha: 0.8))),
                Text(
                  _myRank!.ownerName,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: GoogleFonts.poppins(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.white),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: AppColors.white.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                const Icon(Icons.stars_rounded, color: AppColors.white, size: 16),
                const SizedBox(width: 4),
                Text(
                  "${_myRank!.walletPoints} pts",
                  style: GoogleFonts.poppins(fontWeight: FontWeight.bold, color: AppColors.white, fontSize: 13),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDriverTile(LeaderboardEntry driver) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return ListTile(
      leading: SizedBox(
        width: 80,
        child: Row(
          children: [
            Text(
              "#${driver.rankPosition}",
              style: GoogleFonts.poppins(fontSize: 15, fontWeight: FontWeight.bold, color: isDark ? Colors.white70 : AppColors.grey),
            ),
            const SizedBox(width: 10),
            _buildAvatar(driver),
          ],
        ),
      ),
      title: Text(
        driver.ownerName, 
        style: GoogleFonts.poppins(fontWeight: FontWeight.w600, color: isDark ? Colors.white : AppColors.primaryDark)
      ),
      subtitle: Text("Level: ${driver.rankScore.toInt()}", style: GoogleFonts.poppins(fontSize: 11, color: AppColors.grey)),
      trailing: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: AppColors.primaryPurple.withValues(alpha: 0.1), 
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          "${driver.walletPoints} pts",
          style: GoogleFonts.poppins(fontWeight: FontWeight.bold, color: AppColors.primaryPurple),
        ),
      ),
    );
  }
}
