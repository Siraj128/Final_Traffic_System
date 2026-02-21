import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'dart:math' as math;
import 'dart:ui';
import '../constants/app_colors.dart';
import '../models/card_model.dart';
import '../models/transaction_model.dart';
import '../services/card_service.dart';
import '../widgets/fastag_sheet.dart';
import 'scan_screen.dart';
import '../services/wallet_service.dart';
import 'package:intl/intl.dart';

class VirtualCardScreen extends StatefulWidget {
  final Map<String, dynamic> userData;

  const VirtualCardScreen({super.key, required this.userData});

  @override
  State<VirtualCardScreen> createState() => _VirtualCardScreenState();
}

class _VirtualCardScreenState extends State<VirtualCardScreen> with SingleTickerProviderStateMixin {
  bool _isBackSide = false;
  bool _isBalanceVisible = true;
  bool _isNumberVisible = false;
  late AnimationController _flipController;
  late Animation<double> _flipAnimation;
  
  // Data
  VirtualCardModel? _card;
  List<TransactionModel> _history = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _flipController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _flipAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _flipController, curve: Curves.easeInOutBack),
    );
    _fetchData();
  }

  Future<void> _fetchData() async {
    setState(() => _isLoading = true);
    try {
      final card = await CardService.getCard();
      final history = await WalletService.getHistory();
      
      if (mounted) {
        setState(() {
          _card = card;
          _history = history;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  void dispose() {
    _flipController.dispose();
    super.dispose();
  }

  void _flipCard() {
    if (_isBackSide) {
      _flipController.reverse();
    } else {
      _flipController.forward();
    }
    setState(() => _isBackSide = !_isBackSide);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final width = MediaQuery.of(context).size.width;
    final height = MediaQuery.of(context).size.height;
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text("My Wallet"),
        centerTitle: true,
        automaticallyImplyLeading: false,
      ),
      body: RefreshIndicator(
        onRefresh: _fetchData,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
        child: Column(
          children: [
            SizedBox(height: height * 0.02),
            
            // Flip Card Area
            GestureDetector(
              onTap: _flipCard,
              child: AnimatedBuilder(
                animation: _flipAnimation,
                builder: (context, child) {
                  final angle = _flipAnimation.value * math.pi;
                  final isUnder = angle > math.pi / 2;
                  final transform = Matrix4.identity()
                    ..setEntry(3, 2, 0.001)
                    ..rotateY(angle);
                  
                  return Transform(
                    transform: transform,
                    alignment: Alignment.center,
                    child: isUnder
                        ? Transform(
                            transform: Matrix4.identity()..rotateY(math.pi),
                            alignment: Alignment.center,
                            child: _buildCardBack(width),
                          )
                        : _buildCardFront(width, isDark),
                  );
                },
              ),
            ),
            
            SizedBox(height: height * 0.04),
            
            // Actions
            _buildActionButtons(width),
            
            SizedBox(height: height * 0.02),
            
            TextButton.icon(
              onPressed: _resendCardDetails,
              icon: Icon(Icons.email_outlined, size: width * 0.045, color: theme.colorScheme.primary),
              label: Text("Resend Card Details to Email", style: GoogleFonts.poppins(color: theme.colorScheme.primary, fontSize: width * 0.035, fontWeight: FontWeight.w500)),
              style: TextButton.styleFrom(
                backgroundColor: theme.colorScheme.primary.withValues(alpha: 0.1),
                padding: EdgeInsets.symmetric(horizontal: width * 0.05, vertical: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
              ),
            ),

            SizedBox(height: height * 0.04),
            
            // Recent Transactions
            _buildTransactionHistory(width),
            const SizedBox(height: 100), // FAB Spacing
          ],
          ),
        ),
      ),
    );
  }


  Widget _buildCardFront(double width, bool isDark) {
    return AspectRatio(
      aspectRatio: 1.586,
      child: Container(
        margin: EdgeInsets.symmetric(horizontal: width * 0.06),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: isDark 
              ? [AppColors.fintechBlue, AppColors.fintechNavy] 
              : [AppColors.fintechBlue, AppColors.fintechCyan],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(24),
          boxShadow: [
            BoxShadow(
              color: AppColors.fintechBlue.withValues(alpha: isDark ? 0.3 : 0.2),
              blurRadius: 20,
              offset: const Offset(0, 10),
            ),
          ],
        ),
      child: Stack(
        children: [
          // Glass Effect - Adjusted for visibility in Light Mode
          ClipRRect(
            borderRadius: BorderRadius.circular(24),
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 5, sigmaY: 5),
              child: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      Colors.white.withValues(alpha: isDark ? 0.1 : 0.15),
                      Colors.white.withValues(alpha: 0.05),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
              ),
            ),
          ),
          
          // Freeze Overlay
          if (_card?.isFrozen == true)
            Container(
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.6),
                borderRadius: BorderRadius.circular(24),
              ),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.lock_rounded, color: Colors.white, size: 48),
                    const SizedBox(height: 8),
                    Text(
                      "CARD FROZEN",
                      style: GoogleFonts.poppins(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 2,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          
          // Card Content
          Padding(
            padding: EdgeInsets.all(width * 0.06),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        "SafeDrive Rewards",
                        style: GoogleFonts.poppins(color: Colors.white, fontSize: width * 0.03, fontWeight: FontWeight.w600),
                      ),
                    ),
                    Icon(Icons.contactless_rounded, color: Colors.white, size: width * 0.07),
                  ],
                ),
                
                Row(
                  children: [
                    Text(
                      _isBalanceVisible 
                          ? "₹ ${_card?.cardBalance ?? widget.userData['rewards_points'] ?? '0'}" 
                          : "₹ ••••",
                      style: GoogleFonts.poppins(
                        color: Colors.white,
                        fontSize: width * 0.07,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(width: 12),
                    InkWell(
                      onTap: () => setState(() => _isBalanceVisible = !_isBalanceVisible),
                      child: Icon(
                        _isBalanceVisible ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                        color: Colors.white.withValues(alpha: 0.7),
                        size: width * 0.05,
                      ),
                    ),
                  ],
                ),
                
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: FittedBox(
                            fit: BoxFit.scaleDown,
                            alignment: Alignment.centerLeft,
                            child: Text(
                              _isNumberVisible 
                                  ? (_card?.cardNumber ?? "**** **** **** 4587")
                                  : "**** **** **** ${(_card?.cardNumber?.replaceAll(' ', '') ?? '0000000000004587').substring(math.max(0, (_card?.cardNumber?.replaceAll(' ', '').length ?? 16) - 4))}",                              style: GoogleFonts.robotoMono(
                                color: Colors.white.withValues(alpha: 0.8),
                                fontSize: width * 0.045,
                                letterSpacing: 2,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        InkWell(
                          onTap: () => setState(() => _isNumberVisible = !_isNumberVisible),
                          child: Icon(
                            _isNumberVisible ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                            color: Colors.white.withValues(alpha: 0.6),
                            size: width * 0.045,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Text(
                            (_card?.ownerName ?? widget.userData['name'] ?? widget.userData['owner_name'] ?? 'DRIVER NAME').toUpperCase(),
                            style: GoogleFonts.poppins(
                              color: Colors.white,
                              fontSize: width * 0.035,
                              fontWeight: FontWeight.w600,
                              letterSpacing: 1,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          "EXP ${_card?.expiryDate ?? '12/28'}",
                          style: GoogleFonts.poppins(
                            color: Colors.white.withValues(alpha: 0.8),
                            fontSize: width * 0.03,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
      ),
    );
  }


  bool _isCvvVisible = false;

  // ... (existing helper methods)

  Widget _buildCardBack(double width) {
    return AspectRatio(
      aspectRatio: 1.586,
      child: Container(
        margin: EdgeInsets.symmetric(horizontal: width * 0.06),
        decoration: BoxDecoration(
          color: AppColors.primaryDark,
          borderRadius: BorderRadius.circular(24),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.2),
              blurRadius: 20,
              offset: const Offset(0, 10),
            ),
          ],
        ),
      child: Column(
        children: [
          const SizedBox(height: 30),
          Container(
            height: 40,
            color: Colors.black,
          ),
          const SizedBox(height: 20),
          Padding(
            padding: EdgeInsets.symmetric(horizontal: width * 0.06),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Expanded(
                  flex: 3,
                  child: Container(
                    height: 30,
                    color: Colors.white.withValues(alpha: 0.8),
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.only(right: 8),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Text(
                          "CVV ",
                          style: GoogleFonts.poppins(color: Colors.black, fontSize: width * 0.025),
                        ),
                        Text(
                          _isCvvVisible ? (_card?.cvv ?? '123') : "***",
                          style: GoogleFonts.poppins(
                            color: Colors.black,
                            fontWeight: FontWeight.bold,
                            fontStyle: FontStyle.italic,
                            fontSize: width * 0.03,
                          ),
                        ),
                        const SizedBox(width: 8),
                        InkWell(
                          onTap: () => setState(() => _isCvvVisible = !_isCvvVisible),
                          child: Icon(
                            _isCvvVisible ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                            color: Colors.black.withValues(alpha: 0.6),
                            size: width * 0.04,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                // QR Code
                Container(
                  color: Colors.white,
                  padding: const EdgeInsets.all(4),
                  child: Image.network(
                    "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${_card?.cardNumber ?? 'SafeDrive'}",
                    height: width * 0.15,
                    width: width * 0.15,
                    errorBuilder: (c, e, s) => Icon(Icons.qr_code, size: width * 0.15),
                  ),
                ),
              ],
            ),
          ),
          const Spacer(),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(
              "Use this card for fuel, tolls, and authorized service stations only. Terms apply.",
              style: GoogleFonts.poppins(color: Colors.white.withValues(alpha: 0.5), fontSize: width * 0.025),
              textAlign: TextAlign.center,
            ),
          ),
        ],
      ),
    ),
    );
  }


  Widget _buildActionButtons(double width) {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: width * 0.06),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _buildActionButton(Icons.directions_car_rounded, 'FASTag', _showFastagSheet, width),
          _buildActionButton(Icons.redeem_rounded, 'Redeem', _showRedeemSheet, width),
          _buildActionButton(Icons.receipt_long_rounded, 'History', () => _showHistorySheet(width), width),
          _buildActionButton(
              _card?.isFrozen == true ? Icons.lock_open_rounded : Icons.ac_unit_rounded, 
              _card?.isFrozen == true ? 'Unfreeze' : 'Freeze', 
              () async {
             setState(() => _isLoading = true);
             final success = await CardService.freezeCard(!(_card?.isFrozen ?? false));
             await _fetchData();
             if(mounted) {
               setState(() => _isLoading = false);
               ScaffoldMessenger.of(context).showSnackBar(
                 SnackBar(
                   content: Text(success['message'] ?? "Status Updated"),
                   backgroundColor: success['success'] == true ? AppColors.rewardGreen : AppColors.violationRed,
                 )
               );
             }
          }, width),
        ],
      ),
    );
  }

  Widget _buildActionButton(IconData icon, String label, VoidCallback onTap, double width) {
    final theme = Theme.of(context);
    return Column(
      children: [
        InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(30),
          child: Container(
            height: width * 0.15,
            width: width * 0.15,
            decoration: BoxDecoration(
              color: theme.colorScheme.secondary,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: theme.colorScheme.secondary.withValues(alpha: 0.3),
                  blurRadius: 10,
                  offset: const Offset(0, 5),
                ),
              ],
            ),
            child: Icon(icon, color: Colors.white, size: width * 0.06),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          label,
          style: theme.textTheme.labelMedium?.copyWith(
            fontSize: width * 0.028,
            fontWeight: FontWeight.w600,
            color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
          ),
        ),
      ],
    );
  }

  
  void _showFastagSheet() {
    FastagSheet.show(
      context,
      onLoading: (val) => setState(() => _isLoading = val),
      onComplete: () => _fetchData(),
    );
  }

  void _showRedeemSheet() {
    final theme = Theme.of(context);
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        padding: const EdgeInsets.fromLTRB(24, 12, 24, 32),
        decoration: BoxDecoration(
          color: theme.colorScheme.surface,
          borderRadius: const BorderRadius.only(topLeft: Radius.circular(32), topRight: Radius.circular(32)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.1),
              blurRadius: 20,
              offset: const Offset(0, -5),
            )
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 24),
                decoration: BoxDecoration(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            Text(
              "Redeem Rewards", 
              style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)
            ),
            const SizedBox(height: 8),
            Text(
              "Select a category to use your points", 
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6)
              )
            ),
            const SizedBox(height: 24),
            _buildRedeemOption(Icons.local_gas_station_rounded, "Fuel Station"),
            const SizedBox(height: 12),
            _buildRedeemOption(Icons.add_road_rounded, "Toll Payment"),
            const SizedBox(height: 12),
            _buildRedeemOption(Icons.local_parking_rounded, "Parking Fees"),
          ],
        ),
      ),
    );
  }

  void _showHistorySheet(double width) {
    final theme = Theme.of(context);
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.4,
        maxChildSize: 0.9,
        expand: false,
        builder: (_, controller) => Container(
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: const BorderRadius.only(topLeft: Radius.circular(24), topRight: Radius.circular(24)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 12),
              Center(child: Container(width: 40, height: 4, decoration: BoxDecoration(color: theme.colorScheme.onSurface.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(2)))),
              const SizedBox(height: 24),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Text("Transaction History", style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
              ),
              const SizedBox(height: 16),
              Expanded(
                child: _history.isEmpty 
                  ? _buildEmptyTransactions(width)
                  : ListView.separated(
                      controller: controller,
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                      itemCount: _history.length,
                      separatorBuilder: (context, index) => Divider(height: 1, color: theme.colorScheme.onSurface.withValues(alpha: 0.05)),
                      itemBuilder: (context, index) {
                        final txn = _history[index];
                        return _buildTransactionItem(
                          txn.description,
                          "${txn.amount > 0 ? '+' : ''}${txn.amount} pts",
                          txn.timestamp,
                          txn.amount >= 0,
                          width
                        );
                      },
                    ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyTransactions(double width) {
    final theme = Theme.of(context);
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.receipt_long_outlined, size: 64, color: theme.colorScheme.onSurface.withValues(alpha: 0.2)),
          const SizedBox(height: 16),
          Text(
            "No transactions yet", 
            style: theme.textTheme.bodyLarge?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
              fontWeight: FontWeight.w500,
            )
          ),
        ],
      ),
    );
  }
  
  Widget _buildRedeemOption(IconData icon, String title) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.lightGrey.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.black.withValues(alpha: 0.05)),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        leading: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: AppColors.primaryPurple.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: AppColors.primaryPurple, size: 22),
        ),
        title: Text(
          title, 
          style: GoogleFonts.poppins(fontWeight: FontWeight.w600, color: AppColors.primaryDark, fontSize: 15)
        ),
        trailing: Icon(Icons.arrow_forward_ios_rounded, size: 16, color: AppColors.grey.withValues(alpha: 0.6)),
        onTap: () async {
          if (mounted) Navigator.pop(context);
          
          setState(() => _isLoading = true);
          // Demo redeem points - in real app, title maps to an ID
          final res = await CardService.redeem(100, title);
          await _fetchData();
          
          if (!mounted) return;
          setState(() => _isLoading = false);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(res['message'] ?? "Redemption processed"),
              backgroundColor: res['success'] == true ? AppColors.rewardGreen : AppColors.violationRed,
              behavior: SnackBarBehavior.floating,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            )
          );
        },
      ),
    );
  }

  Future<void> _resendCardDetails() async {
    setState(() => _isLoading = true);
    try {
      // Step 1: Send OTP
      final otpRes = await CardService.sendOtp();
      setState(() => _isLoading = false);
      
      if (!otpRes['success']) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(otpRes['message'])));
        return;
      }

      if (!mounted) return;

      // Step 2: Show OTP Dialog
      final otpController = TextEditingController();
      final shouldVerify = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: Text("Enter OTP", style: GoogleFonts.poppins(fontWeight: FontWeight.bold)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text("A verification code has been sent to your email.", style: GoogleFonts.poppins(fontSize: 12)),
              const SizedBox(height: 16),
              TextField(
                controller: otpController,
                keyboardType: TextInputType.number,
                maxLength: 6,
                textAlign: TextAlign.center,
                style: GoogleFonts.poppins(letterSpacing: 4, fontSize: 18, fontWeight: FontWeight.bold),
                decoration: InputDecoration(
                  counterText: "",
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  filled: true,
                  fillColor: Colors.grey[100],
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: Text("Cancel", style: GoogleFonts.poppins(color: Colors.grey)),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(ctx, true),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primaryPurple,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: Text("Verify & Send", style: GoogleFonts.poppins(color: Colors.white)),
            ),
          ],
        ),
      );

      if (shouldVerify == true && otpController.text.isNotEmpty) {
         setState(() => _isLoading = true);
         // Step 3: Verify & Send
         final res = await CardService.resendDetails(otpController.text);
         
         if (!mounted) return;
         ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(res['message']),
              backgroundColor: res['success'] ? AppColors.rewardGreen : AppColors.violationRed,
            )
          );
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Failed to process request")));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Widget _buildTransactionHistory(double width) {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: width * 0.06),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "Recent Transactions", 
            style: GoogleFonts.poppins(
              fontSize: width * 0.045, 
              fontWeight: FontWeight.bold, 
              color: Theme.of(context).brightness == Brightness.dark ? Colors.white : AppColors.darkGrey
            )
          ),
          const SizedBox(height: 16),
          ..._history.map((txn) => _buildTransactionItem(
            txn.description,
            "${txn.amount > 0 ? '+' : ''}${txn.amount} pts",
            txn.timestamp,
            txn.amount >= 0,
            width
          )),
          if (_history.isEmpty && !_isLoading)
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Text("No transactions yet", style: GoogleFonts.poppins(color: AppColors.grey, fontSize: width * 0.03)),
            ),
        ],
      ),
    );
  }


  Widget _buildTransactionItem(String title, String amount, DateTime date, bool isCredit, double width) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).brightness == Brightness.dark ? Colors.white.withValues(alpha: 0.05) : Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.02), blurRadius: 5)],
      ),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: AppColors.primaryPurple.withValues(alpha: 0.1),
            child: Icon(isCredit ? Icons.add : Icons.remove, color: AppColors.primaryPurple, size: width * 0.04),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title, 
                  style: GoogleFonts.poppins(fontWeight: FontWeight.w600, fontSize: width * 0.035),
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  DateFormat('dd MMM, hh:mm a').format(date), 
                  style: GoogleFonts.poppins(fontSize: width * 0.03, color: AppColors.grey)
                ),
              ],
            ),
          ),
          Text(
            amount, 
            style: GoogleFonts.poppins(
              fontWeight: FontWeight.bold, 
              fontSize: width * 0.035,
              color: isCredit ? AppColors.rewardGreen : AppColors.violationRed,
            )
          ),
        ],
      ),
    );
  }
}

