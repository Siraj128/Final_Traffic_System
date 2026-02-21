import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'dart:async';
import '../constants/app_colors.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> with SingleTickerProviderStateMixin {
  late MobileScannerController _controller;
  late AnimationController _animationController;
  late Animation<double> _animation;
  
  bool _isProcessing = false;
  String? _lastScan;
  int _consecutiveMatches = 0;
  double _confidence = 0.0;
  Timer? _resetTimer;

  @override
  void initState() {
    super.initState();
    _controller = MobileScannerController(
      autoStart: false,
      detectionSpeed: DetectionSpeed.noDuplicates,
    );
    
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
    
    _animation = Tween<double>(begin: 0, end: 1).animate(_animationController);
    
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _controller.start();
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    _animationController.dispose();
    _resetTimer?.cancel();
    super.dispose();
  }

  void _handleBarcode(BarcodeCapture capture) {
    if (_isProcessing) return;
    
    final List<Barcode> barcodes = capture.barcodes;
    if (barcodes.isNotEmpty) {
      final String? code = barcodes.first.rawValue;
      if (code == null) return;

      // Triple Check Logic (Confidence Scoring)
      if (code == _lastScan) {
        _consecutiveMatches++;
      } else {
        _lastScan = code;
        _consecutiveMatches = 1;
      }

      _resetTimer?.cancel();
      _resetTimer = Timer(const Duration(milliseconds: 1500), () {
        if (mounted) {
          setState(() {
            _consecutiveMatches = 0;
            _confidence = 0.0;
          });
        }
      });

      setState(() {
        _confidence = (_consecutiveMatches / 3).clamp(0.0, 1.0);
      });

      if (_consecutiveMatches >= 3) {
        _isProcessing = true;
        _controller.stop();
        _showResultDialog(code);
      }
    }
  }

  void _showResultDialog(String code) {
    final isFastag = code.contains("FASTAG") || code.contains("UPI") || code.length > 10;
    
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      enableDrag: false,
      isDismissible: false,
      builder: (context) => _PaymentBottomSheet(
        code: code,
        isFastag: isFastag,
        onCancel: () {
          Navigator.pop(context);
          setState(() {
            _isProcessing = false;
            _consecutiveMatches = 0;
            _confidence = 0.0;
          });
          _controller.start();
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: Text("AI Scanner", style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
        actions: [
          ValueListenableBuilder(
            valueListenable: _controller,
            builder: (context, state, child) {
              final torchState = state.torchState;
              return IconButton(
                icon: Icon(
                  torchState == TorchState.on ? Icons.flash_on : Icons.flash_off,
                  color: torchState == TorchState.on ? Colors.yellow : Colors.white,
                ),
                onPressed: () => _controller.toggleTorch(),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.cameraswitch),
            onPressed: () => _controller.switchCamera(),
          ),
        ],
      ),
      body: Stack(
        children: [
          MobileScanner(
            controller: _controller,
            onDetect: _handleBarcode,
            errorBuilder: (context, error, child) => _buildErrorWidget(error),
          ),
          
          _buildOverlay(context),
          
          if (_confidence > 0 && _confidence < 1.0)
            Positioned(
              bottom: 120,
              left: 50,
              right: 50,
              child: Column(
                children: [
                   Text(
                    "Verifying... ${(_confidence * 100).toInt()}%",
                    style: GoogleFonts.poppins(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  LinearProgressIndicator(
                    value: _confidence,
                    backgroundColor: Colors.white24,
                    color: AppColors.primaryPurple,
                    borderRadius: BorderRadius.circular(10),
                  ),
                ],
              ),
            ),

          Align(
            alignment: Alignment.bottomCenter,
            child: Padding(
              padding: const EdgeInsets.all(32.0),
              child: Text(
                "Hold steady for high-confidence scan",
                textAlign: TextAlign.center,
                style: GoogleFonts.poppins(color: Colors.white70, fontSize: 13),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorWidget(MobileScannerException error) {
    return Center(
      child: Container(
        padding: const EdgeInsets.all(24),
        margin: const EdgeInsets.all(20),
        decoration: BoxDecoration(color: Colors.black87, borderRadius: BorderRadius.circular(20)),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.no_photography_rounded, color: AppColors.violationRed, size: 64),
            const SizedBox(height: 16),
            Text(
              "Camera Access Required",
              style: GoogleFonts.poppins(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              "Please enable camera permissions in settings to scan QR codes and FASTags.",
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(color: Colors.white70, fontSize: 14),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => _controller.start(),
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.primaryPurple),
              child: const Text("Retry Access"),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOverlay(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final scanAreaSize = constraints.maxWidth * 0.7;
        return Stack(
          children: [
            ColorFiltered(
              colorFilter: ColorFilter.mode(Colors.black.withValues(alpha: 0.6), BlendMode.srcOut),
              child: Stack(
                children: [
                  Container(decoration: const BoxDecoration(color: Colors.transparent, backgroundBlendMode: BlendMode.dstOut)),
                  Align(
                    alignment: Alignment.center,
                    child: Container(
                      width: scanAreaSize,
                      height: scanAreaSize,
                      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(24)),
                    ),
                  ),
                ],
              ),
            ),
            AnimatedBuilder(
              animation: _animation,
              builder: (context, child) {
                return Positioned(
                  top: (constraints.maxHeight - scanAreaSize) / 2 + (scanAreaSize * _animation.value),
                  left: (constraints.maxWidth - scanAreaSize) / 2,
                  child: Container(
                    width: scanAreaSize,
                    height: 3,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(colors: [AppColors.primaryPurple.withValues(alpha: 0), AppColors.primaryPurple, AppColors.primaryPurple.withValues(alpha: 0)]),
                      boxShadow: [BoxShadow(color: AppColors.primaryPurple.withValues(alpha: 0.8), blurRadius: 15, spreadRadius: 2)],
                    ),
                  ),
                );
              },
            ),
            Align(
              alignment: Alignment.center,
              child: Container(
                width: scanAreaSize,
                height: scanAreaSize,
                decoration: BoxDecoration(border: Border.all(color: Colors.white38, width: 1), borderRadius: BorderRadius.circular(24)),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _PaymentBottomSheet extends StatefulWidget {
  final String code;
  final bool isFastag;
  final VoidCallback onCancel;

  const _PaymentBottomSheet({required this.code, required this.isFastag, required this.onCancel});

  @override
  State<_PaymentBottomSheet> createState() => _PaymentBottomSheetState();
}

class _PaymentBottomSheetState extends State<_PaymentBottomSheet> {
  bool _isProcessing = false;
  String? _errorMessage;

  Future<void> _process() async {
    setState(() {
      _isProcessing = true;
      _errorMessage = null;
    });

    try {
      // Simulate API call with potential failure
      await Future.delayed(const Duration(seconds: 2));
      
      // Random failure for demo of retry logic (30% chance)
      // if (DateTime.now().millisecond % 3 == 0) throw Exception("Network Timeout");

      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Row(children: [Icon(Icons.check_circle, color: Colors.white), SizedBox(width: 8), Text("Payment Successful!")]),
            backgroundColor: Colors.green,
            behavior: SnackBarBehavior.floating,
          ),
        );
        widget.onCancel(); // Resume camera
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isProcessing = false;
          _errorMessage = "Network error. Please check your connection and retry.";
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: const BorderRadius.only(topLeft: Radius.circular(32), topRight: Radius.circular(32)),
        boxShadow: [BoxShadow(color: Colors.black26, blurRadius: 20, offset: const Offset(0, -5))],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2))),
          const SizedBox(height: 24),
          Row(
            children: [
              Container(padding: const EdgeInsets.all(12), decoration: BoxDecoration(color: AppColors.primaryPurple.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(16)), child: Icon(widget.isFastag ? Icons.toll_rounded : Icons.qr_code_scanner_rounded, color: AppColors.primaryPurple, size: 32)),
              const SizedBox(width: 16),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(widget.isFastag ? "Toll Payment" : "QR Result", style: GoogleFonts.poppins(fontSize: 18, fontWeight: FontWeight.bold)),
                  Text(widget.isFastag ? "Electronic City Phase 1" : "Verified Scan", style: GoogleFonts.poppins(color: Colors.grey, fontSize: 12)),
                ]),
              ),
              if (widget.isFastag) Text("₹50.00", style: GoogleFonts.poppins(fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.primaryPurple)),
            ],
          ),
          const SizedBox(height: 24),
          if (_errorMessage != null)
            Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(bottom: 20),
              decoration: BoxDecoration(color: Colors.red.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(12)),
              child: Row(children: [const Icon(Icons.error_outline, color: Colors.red, size: 20), const SizedBox(width: 8), Expanded(child: Text(_errorMessage!, style: const TextStyle(color: Colors.red, fontSize: 13)))]),
            ),
          Row(
            children: [
              Expanded(
                child: TextButton(
                  onPressed: _isProcessing ? null : widget.onCancel,
                  style: TextButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
                  child: Text("Cancel", style: GoogleFonts.poppins(color: Colors.grey, fontWeight: FontWeight.w600)),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: ElevatedButton(
                  onPressed: _isProcessing ? null : _process,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primaryPurple,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    elevation: 0,
                  ),
                  child: _isProcessing 
                    ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : Text(_errorMessage != null ? "Retry" : "Confirm", style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}
