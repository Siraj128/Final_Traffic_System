import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import '../constants/app_colors.dart';
import '../services/api_service.dart';

class EditProfileScreen extends StatefulWidget {
  final Map<String, dynamic> userData;

  const EditProfileScreen({super.key, required this.userData});

  @override
  State<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _nameController;
  late TextEditingController _mobileController;
  File? _imageFile;
  final ImagePicker _picker = ImagePicker();
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.userData['name'] ?? widget.userData['owner_name']);
    _mobileController = TextEditingController(text: widget.userData['mobile'] ?? widget.userData['mobile_number'] ?? '');
    _loadSavedProfile();
  }

  Future<void> _loadSavedProfile() async {
    final prefs = await SharedPreferences.getInstance();
    if (prefs.containsKey('user_name')) {
      setState(() {
        _nameController.text = prefs.getString('user_name')!;
      });
    }
  }

  Future<void> _pickImage() async {
    final XFile? pickedFile = await _picker.pickImage(source: ImageSource.gallery);
    if (pickedFile != null) {
      setState(() {
        _imageFile = File(pickedFile.path);
      });
    }
  }

  Future<void> _saveProfile() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isSaving = true);
      try {
        final prefs = await SharedPreferences.getInstance();
        final plateNumber = prefs.getString('vehicle_number');
        
        if (plateNumber != null) {
          // Update Backend
          final response = await ApiService.updateUserProfile(plateNumber, {
              "name": _nameController.text,
              "avatar": _imageFile != null ? "file://${_imageFile!.path}" : widget.userData['avatar']
          });
          
          if (response.containsKey('success') && response['success'] != false || response.containsKey('plate_number')) {
            await prefs.setString('user_name', _nameController.text);
            await prefs.setString('user_mobile', _mobileController.text);
            if (_imageFile != null) {
              await prefs.setString('user_pic', "file://${_imageFile!.path}");
            }

            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("Profile Updated Successfully")),
              );
              Navigator.pop(context, true); // Return true to trigger refresh
            }
          } else {
             throw Exception(response['message'] ?? "Unknown error");
          }
        }
      } catch (e) {
        if (mounted) {
           ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text("Error updating profile: $e")),
           );
        }
      } finally {
        if (mounted) setState(() => _isSaving = false);
      }
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _mobileController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        title: Text(
          "Edit Profile", 
          style: GoogleFonts.poppins(
            color: isDark ? Colors.white : AppColors.primaryDark, 
            fontWeight: FontWeight.bold
          )
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new_rounded, color: isDark ? Colors.white : AppColors.primaryDark),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
               Stack(
                 children: [
                   CircleAvatar(
                    radius: 60,
                    backgroundColor: AppColors.primaryPurple,
                    backgroundImage: _imageFile != null 
                        ? FileImage(_imageFile!) 
                        : (widget.userData['avatar'] != null && widget.userData['avatar'].startsWith('http')
                            ? NetworkImage(widget.userData['avatar']) 
                            : null) as ImageProvider?,
                    child: (_imageFile == null && (widget.userData['avatar'] == null || !widget.userData['avatar'].startsWith('http')))
                        ? Text(
                            (_nameController.text.isNotEmpty ? _nameController.text[0] : 'U').toUpperCase(),
                            style: GoogleFonts.poppins(fontSize: 40, color: Colors.white, fontWeight: FontWeight.bold),
                          )
                        : null,
                   ),
                   Positioned(
                     bottom: 0,
                     right: 0,
                     child: GestureDetector(
                       onTap: _pickImage,
                       child: Container(
                         padding: const EdgeInsets.all(8),
                         decoration: const BoxDecoration(color: AppColors.primaryPurple, shape: BoxShape.circle),
                         child: const Icon(Icons.camera_alt_rounded, color: Colors.white, size: 20),
                       ),
                     ),
                   ),
                 ],
               ),
              const SizedBox(height: 32),
              _buildTextField("Full Name", _nameController, Icons.person_outline),
              const SizedBox(height: 16),
              _buildTextField("Mobile Number", _mobileController, Icons.phone_android_rounded, keyboardType: TextInputType.phone),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isSaving ? null : _saveProfile,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primaryPurple,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  ),
                  child: _isSaving 
                    ? const CircularProgressIndicator(color: Colors.white)
                    : Text("Save Changes", style: GoogleFonts.poppins(fontWeight: FontWeight.bold, color: Colors.white)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(String label, TextEditingController controller, IconData icon, {TextInputType? keyboardType}) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      style: GoogleFonts.poppins(color: isDark ? Colors.white : AppColors.primaryDark),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: GoogleFonts.poppins(color: AppColors.grey),
        prefixIcon: Icon(icon, color: isDark ? Colors.white70 : AppColors.grey),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: isDark ? const BorderSide(color: Colors.white10) : const BorderSide(),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: isDark ? const BorderSide(color: Colors.white10) : const BorderSide(color: Colors.grey),
        ),
        filled: true,
        fillColor: Theme.of(context).cardColor,
      ),
      validator: (value) => value == null || value.isEmpty ? "Please enter $label" : null,
    );
  }
}
