import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';
import '../services/api_service.dart';

class AddVehicleScreen extends StatefulWidget {
  const AddVehicleScreen({super.key});

  @override
  State<AddVehicleScreen> createState() => _AddVehicleScreenState();
}

class _AddVehicleScreenState extends State<AddVehicleScreen> {
  final _formKey = GlobalKey<FormState>();
  final _plateController = TextEditingController();
  final _brandController = TextEditingController();
  final _modelController = TextEditingController();
  final _colorController = TextEditingController();
  final _fastagController = TextEditingController();
  
  String _vehicleType = 'Car';
  bool _isLoading = false;

  final List<String> _types = ['Car', 'Bike', 'Truck', 'Bus'];

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    
    final vehicleData = {
      'plate_number': _plateController.text.trim().toUpperCase(),
      'vehicle_type': _vehicleType,
      'brand': _brandController.text.trim(),
      'model': _modelController.text.trim(),
      'color': _colorController.text.trim(),
      'fastag_id': _fastagController.text.trim(),
    };

    try {
      final res = await ApiService.addVehicle(vehicleData);
      setState(() => _isLoading = false);
      
      if (res['success'] == true || res.containsKey('vehicle_id')) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Vehicle added successfully!')),
          );
          Navigator.pop(context, true);
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(res['message'] ?? 'Failed to add vehicle')),
          );
        }
      }
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Add New Vehicle', style: GoogleFonts.poppins(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildSectionTitle('Vehicle Details'),
              const SizedBox(height: 16),
              _buildTextField(
                controller: _plateController,
                label: 'Plate Number',
                hint: 'e.g. MH12AB1234',
                icon: Icons.numbers,
                validator: (v) => v!.isEmpty ? 'Plate number is required' : null,
              ),
              const SizedBox(height: 20),
              _buildDropdown(),
              const SizedBox(height: 20),
              Row(
                children: [
                  Expanded(
                    child: _buildTextField(
                      controller: _brandController,
                      label: 'Brand',
                      hint: 'e.g. Toyota',
                      icon: Icons.branding_watermark,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: _buildTextField(
                      controller: _modelController,
                      label: 'Model',
                      hint: 'e.g. Camry',
                      icon: Icons.model_training,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              _buildTextField(
                controller: _colorController,
                label: 'Color',
                hint: 'e.g. White',
                icon: Icons.color_lens,
              ),
              const SizedBox(height: 32),
              _buildSectionTitle('Optional Details'),
              const SizedBox(height: 16),
              _buildTextField(
                controller: _fastagController,
                label: 'FASTag ID',
                hint: 'Mapping for rewards',
                icon: Icons.payments,
              ),
              const SizedBox(height: 48),
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _submit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primaryPurple,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  ),
                  child: _isLoading
                      ? const CircularProgressIndicator(color: Colors.white)
                      : Text(
                          'REGISTER VEHICLE',
                          style: GoogleFonts.poppins(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: GoogleFonts.poppins(
        color: AppColors.primaryPurple,
        fontWeight: FontWeight.bold,
        fontSize: 14,
        letterSpacing: 1.2,
      ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required String hint,
    required IconData icon,
    String? Function(String?)? validator,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return TextFormField(
      controller: controller,
      validator: validator,
      style: GoogleFonts.poppins(color: isDark ? Colors.white : AppColors.textPrimary),
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        prefixIcon: Icon(icon, color: isDark ? Colors.white70 : AppColors.textSecondary),
        labelStyle: TextStyle(color: isDark ? Colors.white70 : AppColors.textSecondary),
        hintStyle: TextStyle(color: isDark ? Colors.white24 : AppColors.textSecondary.withValues(alpha: 0.5)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: isDark ? Colors.white10 : AppColors.lightGrey),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.primaryPurple, width: 2),
        ),
        filled: true,
        fillColor: isDark ? Colors.white.withOpacity(0.05) : AppColors.white,
      ),
    );
  }

  Widget _buildDropdown() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: _vehicleType,
          dropdownColor: Colors.grey[900],
          isExpanded: true,
          style: GoogleFonts.poppins(color: Colors.white),
          items: _types.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
          onChanged: (v) => setState(() => _vehicleType = v!),
        ),
      ),
    );
  }
}
