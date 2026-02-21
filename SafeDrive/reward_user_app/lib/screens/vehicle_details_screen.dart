import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../constants/app_colors.dart';

class VehicleDetailsScreen extends StatefulWidget {
  final Map<String, dynamic> vehicle;

  const VehicleDetailsScreen({super.key, required this.vehicle});

  @override
  State<VehicleDetailsScreen> createState() => _VehicleDetailsScreenState();
}

class _VehicleDetailsScreenState extends State<VehicleDetailsScreen> {
  late TextEditingController _plateController;
  late TextEditingController _ownerController;
  late TextEditingController _typeController;
  late TextEditingController _fuelController;
  
  bool _isEditing = false;

  @override
  void initState() {
    super.initState();
    _plateController = TextEditingController(text: widget.vehicle['plate_number'] ?? widget.vehicle['vehicle_number'] ?? '');
    _ownerController = TextEditingController(text: widget.vehicle['owner_name'] ?? widget.vehicle['name'] ?? widget.vehicle['user_name'] ?? '');
    _typeController = TextEditingController(text: widget.vehicle['vehicle_type'] ?? '');
    _fuelController = TextEditingController(text: widget.vehicle['fuel_type'] ?? 'Petrol');
    _loadSavedDetails();
  }

  Future<void> _loadSavedDetails() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      if (prefs.containsKey('vehicleNumber')) _plateController.text = prefs.getString('vehicleNumber')!;
      if (prefs.containsKey('vehicleType')) _typeController.text = prefs.getString('vehicleType')!;
      if (prefs.containsKey('fuel_type')) _fuelController.text = prefs.getString('fuel_type')!;
      if (prefs.containsKey('userName')) _ownerController.text = prefs.getString('userName')!;
    });
  }

  Future<void> _saveDetails() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('vehicleNumber', _plateController.text);
    await prefs.setString('vehicleType', _typeController.text);
    await prefs.setString('fuel_type', _fuelController.text);
    // await prefs.setString('userName', _ownerController.text);

    setState(() {
      _isEditing = false;
    });

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Vehicle Details Saved Locally")),
      );
    }
  }

  @override
  void dispose() {
    _plateController.dispose();
    _ownerController.dispose();
    _typeController.dispose();
    _fuelController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    
    return Scaffold(
      appBar: AppBar(
        title: const Text("Vehicle Details"),
        actions: [
          IconButton(
            icon: Icon(
              _isEditing ? Icons.check_circle_rounded : Icons.edit_rounded, 
              color: theme.colorScheme.primary,
              size: 28,
            ),
            onPressed: () {
              if (_isEditing) {
                _saveDetails();
              } else {
                setState(() => _isEditing = true);
              }
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
        children: [
          _buildDetailField("Vehicle Number", _plateController, Icons.directions_car),
          _buildDetailField("Owner Name", _ownerController, Icons.person, readOnly: true),
          _buildDetailField("Vehicle Type", _typeController, Icons.local_taxi),
          _buildDetailField("Fuel Type", _fuelController, Icons.local_gas_station),
          
          if (_isEditing)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 20),
              child: Text(
                "Note: Owner name can be updated from your Profile screen.",
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
                textAlign: TextAlign.center,
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildDetailField(String label, TextEditingController controller, IconData icon, {bool readOnly = false}) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    bool canEdit = _isEditing && !readOnly;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: theme.cardTheme.color,
        borderRadius: BorderRadius.circular(20),
        boxShadow: isDark ? [] : [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 15,
            offset: const Offset(0, 8),
          ),
        ],
        border: isDark ? Border.all(color: Colors.white10) : null,
      ),
      child: Padding(
        padding: const EdgeInsets.all(4), // Subtle inner padding for the card feel
        child: TextField(
          controller: controller,
          enabled: canEdit,
          style: theme.textTheme.bodyLarge?.copyWith(
            fontWeight: FontWeight.bold,
            letterSpacing: 0.5,
          ),
          decoration: InputDecoration(
            labelText: label,
            labelStyle: theme.textTheme.labelMedium?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
              fontWeight: FontWeight.w500,
            ),
            prefixIcon: Padding(
              padding: const EdgeInsets.all(12),
              child: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primary.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: theme.colorScheme.primary, size: 22),
              ),
            ),
            border: InputBorder.none,
            enabledBorder: InputBorder.none,
            focusedBorder: InputBorder.none,
            disabledBorder: InputBorder.none,
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
            filled: false, // card handles the background
          ),
        ),
      ),
    );
  }
}
