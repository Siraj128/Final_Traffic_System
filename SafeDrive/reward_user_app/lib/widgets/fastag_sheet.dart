import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';
import '../services/card_service.dart';

class FastagSheet {
  static void show(BuildContext context, {
    required Function(bool) onLoading, 
    required Function onComplete
  }) {
    String? selectedToll;
    final tolls = ["KIAL Airport Toll", "Electronic City Toll", "NICE Road Toll", "Nelamangala Toll"];
    final amountController = TextEditingController(text: "50");

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => StatefulBuilder(
        builder: (context, setSheetState) => Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: Theme.of(context).cardColor,
            borderRadius: const BorderRadius.only(topLeft: Radius.circular(24), topRight: Radius.circular(24)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                   Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppColors.primaryPurple.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.directions_car_rounded, color: AppColors.primaryPurple, size: 24),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    "Pay Toll (FASTag)", 
                    style: GoogleFonts.poppins(
                      fontSize: 18, 
                      fontWeight: FontWeight.bold, 
                      color: Theme.of(context).brightness == Brightness.dark ? Colors.white : AppColors.primaryDark
                    )
                  ),
                ],
              ),
              const SizedBox(height: 24),
              
              // Toll Selection
              DropdownButtonFormField<String>(
                value: selectedToll,
                dropdownColor: Theme.of(context).cardColor,
                style: GoogleFonts.poppins(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black),
                hint: Text("Select Toll Plaza", style: GoogleFonts.poppins(color: AppColors.grey)),
                items: tolls.map((toll) => DropdownMenuItem(value: toll, child: Text(toll))).toList(),
                onChanged: (val) => setSheetState(() => selectedToll = val),
                decoration: InputDecoration(
                  filled: true,
                  fillColor: Colors.grey.withValues(alpha: 0.05),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                ),
              ),
              const SizedBox(height: 16),

              TextField(
                controller: amountController,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(
                  labelText: "Toll Amount",
                  prefixText: "₹ ",
                  filled: true,
                  fillColor: Colors.grey.withValues(alpha: 0.05),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
                ),
              ),
              const SizedBox(height: 24),
              
              ElevatedButton(
                onPressed: () async {
                  if (selectedToll == null) {
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text("Please select a toll plaza"))
                      );
                    }
                    return;
                  }
                  
                  final amountText = amountController.text.trim();
                  if (amountText.isEmpty) {
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text("Please enter an amount"))
                      );
                    }
                    return;
                  }

                  final amount = int.tryParse(amountText) ?? 0;
                  if (amount <= 0) return;

                  Navigator.pop(context);
                  onLoading(true);
                  try {
                    final res = await CardService.payFastag(amount, selectedToll!);
                    onComplete();
                    
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text(res['message'] ?? "Toll paid successfully"),
                          backgroundColor: res['success'] == true ? AppColors.rewardGreen : AppColors.violationRed,
                          behavior: SnackBarBehavior.floating,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        )
                      );
                    }
                  } catch (e) {
                    // handle error
                  } finally {
                    onLoading(false);
                  }
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primaryPurple,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  elevation: 0,
                ),
                child: Text("Pay Toll", style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}
