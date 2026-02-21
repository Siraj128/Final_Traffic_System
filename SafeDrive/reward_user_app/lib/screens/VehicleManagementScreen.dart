import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../constants/app_colors.dart';
import 'AddVehicleScreen.dart';
import '../services/api_service.dart';
import '../services/session_manager.dart';
import 'vehicle_details_screen.dart'; // [NEW] Import added

class VehicleManagementScreen extends StatefulWidget {
  const VehicleManagementScreen({super.key});

  @override
  State<VehicleManagementScreen> createState() => _VehicleManagementScreenState();
}

class _VehicleManagementScreenState extends State<VehicleManagementScreen> {
  List<dynamic> _vehicles = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchVehicles();
  }

  Future<void> _fetchVehicles({bool showLoader = true}) async {
    if (showLoader) setState(() => _isLoading = true);
    try {
      final vehicles = await ApiService.getMyVehicles();
      setState(() {
        _vehicles = vehicles;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load vehicles: $e')),
        );
      }
    }
  }

  Future<void> _setPrimary(int vehicleId) async {
    final res = await ApiService.setPrimaryVehicle(vehicleId);
    if (res['success'] == true || res.containsKey('vehicle_id')) {
      _fetchVehicles();
      // Update local session if needed
      final updatedVehicle = _vehicles.firstWhere((v) => v['vehicle_id'] == vehicleId);
      await SessionManager.setSelectedVehicle(vehicleId, updatedVehicle['plate_number']);
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(res['message'] ?? 'Failed to set primary vehicle')),
        );
      }
    }
  }

  Future<void> _deleteVehicle(int vehicleId) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Vehicle'),
        content: const Text('Are you sure you want to remove this vehicle? This will also delete its history.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirm == true) {
      final res = await ApiService.deleteVehicle(vehicleId);
      if (res['success'] == true || res.containsKey('message')) {
        _fetchVehicles();
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(res['message'] ?? 'Failed to delete vehicle')),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: Text('My Fleet', style: GoogleFonts.poppins(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: RefreshIndicator(
        onRefresh: () => _fetchVehicles(showLoader: false),
        child: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.primaryPurple))
          : _vehicles.isEmpty
              ? _buildEmptyState()
              : _buildVehicleList(),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (context) => const AddVehicleScreen()),
        ).then((_) => _fetchVehicles()),
        backgroundColor: AppColors.primaryPurple,
        icon: const Icon(Icons.add, color: Colors.white),
        label: Text('Add Vehicle', style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.bold)),
      ),
    );
  }

  Widget _buildEmptyState() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      children: [
        SizedBox(height: MediaQuery.of(context).size.height * 0.25),
        Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.directions_car_outlined, size: 80, color: isDark ? Colors.white30 : AppColors.textSecondary.withValues(alpha: 0.3)),
          const SizedBox(height: 16),
          Text(
            'No vehicles registered',
            style: GoogleFonts.poppins(color: isDark ? Colors.white70 : AppColors.textPrimary, fontSize: 18),
          ),
          const SizedBox(height: 8),
          Text(
            'Add your first vehicle to start earning rewards',
            style: GoogleFonts.poppins(color: isDark ? Colors.white38 : AppColors.textSecondary, fontSize: 14),
          ),
        ],
      ),
        ),
      ],
    );
  }

  Widget _buildVehicleList() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final width = MediaQuery.of(context).size.width;

    return ListView.builder(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(20),
      itemCount: _vehicles.length,
      itemBuilder: (context, index) {
        final vehicle = _vehicles[index];
        final isPrimary = vehicle['is_primary'] == true;

        return Container(
          margin: const EdgeInsets.only(bottom: 16),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: isDark 
                  ? [Colors.white.withOpacity(0.08), Colors.white.withOpacity(0.02)]
                  : [Colors.white, Colors.grey.withOpacity(0.05)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: isPrimary ? AppColors.primaryPurple.withOpacity(0.6) : (isDark ? Colors.white10 : Colors.black.withOpacity(0.05)),
              width: 2,
            ),
            boxShadow: [
              BoxShadow(
                color: isPrimary 
                    ? AppColors.primaryPurple.withOpacity(0.15) 
                    : Colors.black.withOpacity(0.05),
                blurRadius: 15,
                offset: const Offset(0, 8),
              )
            ],
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              borderRadius: BorderRadius.circular(24),
              onTap: () => Navigator.push(
                context, 
                MaterialPageRoute(builder: (_) => VehicleDetailsScreen(vehicle: vehicle))
              ),
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Row(
                  children: [
                    _getVehicleIcon(vehicle['vehicle_type']),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Text(
                                vehicle['plate_number'],
                                style: GoogleFonts.poppins(
                                  color: isDark ? Colors.white : AppColors.primaryDark,
                                  fontWeight: FontWeight.bold,
                                  fontSize: width * 0.045,
                                  letterSpacing: 1,
                                ),
                              ),
                              if (isPrimary) ...[
                                const SizedBox(width: 8),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: AppColors.primaryPurple,
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: Text(
                                    'PRIMARY',
                                    style: GoogleFonts.poppins(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold),
                                  ),
                                ),
                              ],
                            ],
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '${vehicle['brand'] ?? 'SafeDrive'} ${vehicle['model'] ?? 'Premium'}',
                            style: GoogleFonts.poppins(
                              color: isDark ? Colors.white60 : Colors.black54,
                              fontSize: width * 0.035,
                            ),
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              Icon(Icons.shield_outlined, size: 14, color: AppColors.rewardGreen),
                              const SizedBox(width: 4),
                              Text(
                                'Certified Safe',
                                style: GoogleFonts.poppins(
                                  color: AppColors.rewardGreen,
                                  fontSize: width * 0.03,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    PopupMenuButton<String>(
                      icon: Icon(Icons.more_vert_rounded, color: isDark ? Colors.white38 : Colors.black38),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                      onSelected: (value) {
                        if (value == 'primary') _setPrimary(vehicle['vehicle_id']);
                        if (value == 'delete') _deleteVehicle(vehicle['vehicle_id']);
                      },
                      itemBuilder: (context) => [
                        if (!isPrimary)
                          PopupMenuItem(
                            value: 'primary',
                            child: Row(
                              children: [
                                Icon(Icons.star_border_rounded, size: 18, color: AppColors.primaryPurple),
                                const SizedBox(width: 8),
                                const Text('Set Primary'),
                              ],
                            ),
                          ),
                        PopupMenuItem(
                          value: 'delete',
                          child: Row(
                            children: const [
                              Icon(Icons.delete_outline_rounded, size: 18, color: Colors.redAccent),
                              SizedBox(width: 8),
                              Text('Remove', style: TextStyle(color: Colors.redAccent)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _getVehicleIcon(String? type) {
    IconData icon;
    switch (type?.toLowerCase()) {
      case 'car':
        icon = Icons.directions_car;
        break;
      case 'bike':
      case 'motorcycle':
        icon = Icons.motorcycle;
        break;
      case 'truck':
        icon = Icons.local_shipping;
        break;
      default:
        icon = Icons.directions_car;
    }
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppColors.primaryPurple.withOpacity(0.1),
        shape: BoxShape.circle,
      ),
      child: Icon(icon, color: AppColors.primaryPurple),
    );
  }
}
