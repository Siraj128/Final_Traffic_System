import '../constants/app_strings.dart';

/// Input validation utilities
class Validators {
  /// Validates vehicle plate number format: [A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}
  /// Example: DL01AB1234
  static String? validatePlateNumber(String? value) {
    if (value == null || value.isEmpty) {
      return AppStrings.plateRequiredError;
    }

    // Remove any spaces or dashes
    final cleanedValue = value.replaceAll(RegExp(r'[\s-]'), '').toUpperCase();

    // Regex pattern: [A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}
    final RegExp plateRegex = RegExp(r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$');

    if (!plateRegex.hasMatch(cleanedValue)) {
      return AppStrings.plateFormatError;
    }

    return null; // Valid
  }

  /// Validates email format
  static String? validateEmail(String? value) {
    if (value == null || value.isEmpty) {
      return AppStrings.emailRequiredError;
    }

    // Basic email regex pattern
    final RegExp emailRegex = RegExp(
      r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    );

    if (!emailRegex.hasMatch(value.trim())) {
      return AppStrings.emailFormatError;
    }

    return null; // Valid
  }

  /// Validates mobile number (10 digits)
  static String? validateMobileNumber(String? value) {
    if (value == null || value.isEmpty) {
      return AppStrings.mobileRequiredError;
    }

    // Remove any spaces, dashes, or parentheses
    final cleanedValue = value.replaceAll(RegExp(r'[\s\-\(\)]'), '');

    // Check if it's exactly 10 digits
    final RegExp mobileRegex = RegExp(r'^[0-9]{10}$');

    if (!mobileRegex.hasMatch(cleanedValue)) {
      return AppStrings.mobileFormatError;
    }

    return null; // Valid
  }

  /// Validates required text fields
  static String? validateRequired(String? value, String fieldName) {
    if (value == null || value.trim().isEmpty) {
      return '$fieldName is required';
    }
    return null; // Valid
  }

  /// Validates owner name
  static String? validateOwnerName(String? value) {
    if (value == null || value.trim().isEmpty) {
      return AppStrings.nameRequiredError;
    }
    return null; // Valid
  }

  /// Validates vehicle type selection
  static String? validateVehicleType(String? value) {
    if (value == null || value.isEmpty) {
      return AppStrings.vehicleTypeRequiredError;
    }
    return null; // Valid
  }

  /// Validates password — min 6 chars, at least 1 letter and 1 digit
  static String? validatePassword(String? value) {
    if (value == null || value.isEmpty) {
      return AppStrings.passwordRequiredError;
    }
    if (value.length < 6) {
      return AppStrings.passwordFormatError;
    }
    if (!RegExp(r'[a-zA-Z]').hasMatch(value)) {
      return AppStrings.passwordFormatError;
    }
    if (!RegExp(r'[0-9]').hasMatch(value)) {
      return AppStrings.passwordFormatError;
    }
    return null; // Valid
  }

  /// Validates confirm password — must match the original password
  static String? validateConfirmPassword(String? value, String password) {
    if (value == null || value.isEmpty) {
      return AppStrings.passwordRequiredError;
    }
    if (value != password) {
      return AppStrings.confirmPasswordError;
    }
    return null; // Valid
  }
}
