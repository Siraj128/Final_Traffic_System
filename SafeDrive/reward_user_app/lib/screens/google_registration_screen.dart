import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';
import '../services/auth_service.dart';
import 'main_screen.dart';
import '../utils/validators.dart';

class GoogleRegistrationScreen extends StatefulWidget {
  final Map<String, dynamic> googleData;

  const GoogleRegistrationScreen({super.key, required this.googleData});

  @override
  State<GoogleRegistrationScreen> createState() => _GoogleRegistrationScreenState();
}

class _GoogleRegistrationScreenState extends State<GoogleRegistrationScreen> {
  final _formKey = GlobalKey<FormState>();
  
  late TextEditingController _nameController;
  late TextEditingController _emailController;
  final _vehicleNumberController = TextEditingController();
  final _mobileController = TextEditingController();
  final _cityController = TextEditingController();
  final _fastagController = TextEditingController();
  
  String _selectedVehicleType = 'Car';
  String _selectedFuelType = 'Petrol';
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.googleData['name']);
    _emailController = TextEditingController(text: widget.googleData['email']);
  }

  Future<void> _submitRegistration() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);
      
      try {
        final response = await AuthService.completeGoogleRegistration(
          name: _nameController.text.trim(),
          email: _emailController.text.trim(),
          googleId: widget.googleData['googleId'],
          avatar: widget.googleData['picture'],
          vehicleNumber: _vehicleNumberController.text.trim().toUpperCase(),
          vehicleType: _selectedVehicleType,
          fuelType: _selectedFuelType,
          mobile: _mobileController.text.trim(),
          city: _cityController.text.trim(),
          fastagId: _fastagController.text.trim(),
        );

        if (!mounted) return;

        if (response['success'] == true) {
           Navigator.pushAndRemoveUntil(
            context,
            MaterialPageRoute(
              builder: (context) => MainScreen(userData: response['data']),
            ),
            (route) => false,
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(response['message'] ?? "Registration Failed"), backgroundColor: AppColors.violationRed),
          );
        }
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Error: $e"), backgroundColor: AppColors.violationRed),
        );
      } finally {
        if (mounted) setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text("Complete Profile", style: GoogleFonts.poppins(color: isDark ? Colors.white : AppColors.primaryDark, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        automaticallyImplyLeading: false, 
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
                Text(
                  "One last step! 👋",
                  style: GoogleFonts.poppins(
                    fontSize: 24, 
                    fontWeight: FontWeight.bold, 
                    color: isDark ? Colors.white : AppColors.primaryDark
                  ),
                ),
               Text(
                 "Tell us about your vehicle to start earning rewards.",
                 style: GoogleFonts.poppins(fontSize: 14, color: AppColors.grey),
               ),
               const SizedBox(height: 24),
               
               // Read-Only Google Fields
               _buildTextField("Full Name", _nameController, Icons.person, readOnly: true),
               _buildTextField("Email Address", _emailController, Icons.email, readOnly: true),
               
               const Divider(height: 32),
               
               // Vehicle Details
               _buildTextField("Vehicle Number", _vehicleNumberController, Icons.directions_car, isCapital: true, 
                  validator: Validators.validatePlateNumber),
               
               const SizedBox(height: 16),
               _buildDropdown("Vehicle Type", _selectedVehicleType, ["Car", "Bike", "Truck", "Bus"], (val) => setState(() => _selectedVehicleType = val!)),
               const SizedBox(height: 16),
               
                _buildTextField("Mobile Number", _mobileController, Icons.phone, inputType: TextInputType.phone, 
                  validator: (v) => (v != null && v.length >= 10) ? null : "Enter valid mobile number"),
               
               const SizedBox(height: 16),
               _buildDropdown("Fuel Type", _selectedFuelType, ["Petrol", "Diesel", "Electric", "CNG"], (val) => setState(() => _selectedFuelType = val!)),
               const SizedBox(height: 16),
               
               _buildTextField("City", _cityController, Icons.location_city, 
                  validator: (v) => (v != null && v.isNotEmpty) ? null : "Enter your city"),
                  
               _buildTextField("FASTag ID (Optional)", _fastagController, Icons.tag),

               const SizedBox(height: 32),
               
               SizedBox(
                 width: double.infinity,
                 height: 56,
                 child: ElevatedButton(
                   onPressed: _isLoading ? null : _submitRegistration,
                   style: ElevatedButton.styleFrom(
                     backgroundColor: AppColors.primaryPurple,
                     shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                   ),
                   child: _isLoading 
                      ? const CircularProgressIndicator(color: Colors.white)
                      : Text("Complete Registration", style: GoogleFonts.poppins(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                 ),
               ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(String label, TextEditingController controller, IconData icon, 
      {bool readOnly = false, bool isCapital = false, TextInputType? inputType, String? Function(String?)? validator}) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: GoogleFonts.poppins(
            fontSize: 12,
            fontWeight: FontWeight.w500,
            color: Theme.of(context).hintColor,
          ),
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: controller,
          readOnly: readOnly,
          validator: validator,
          keyboardType: inputType,
          textCapitalization: isCapital ? TextCapitalization.characters : TextCapitalization.none,
          decoration: InputDecoration(
            hintText: "Enter $label",
            prefixIcon: Icon(icon, size: 20, color: readOnly ? AppColors.grey : AppColors.primaryPurple),
            fillColor: isDark ? Colors.white10 : Colors.grey.withValues(alpha: 0.05),
          ),
          style: GoogleFonts.poppins(
            fontSize: 14,
            color: readOnly ? AppColors.grey : (isDark ? Colors.white : AppColors.primaryDark),
          ),
        ),
        const SizedBox(height: 16),
      ],
    );
  }

  Widget _buildDropdown(String label, String value, List<String> items, Function(String?) onChanged) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: GoogleFonts.poppins(
            fontSize: 12,
            fontWeight: FontWeight.w500,
            color: Theme.of(context).hintColor,
          ),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          value: value,
          decoration: InputDecoration(
            prefixIcon: Icon(label.contains("Type") ? Icons.category : Icons.local_gas_station, size: 20, color: AppColors.primaryPurple),
            fillColor: isDark ? Colors.white10 : Colors.grey.withValues(alpha: 0.05),
          ),
          items: items.map((e) => DropdownMenuItem(value: e, child: Text(e, style: GoogleFonts.poppins(fontSize: 14)))).toList(),
          onChanged: onChanged,
        ),
      ],
    );
  }
}
