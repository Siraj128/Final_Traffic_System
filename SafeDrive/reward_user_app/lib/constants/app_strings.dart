/// App-wide string constants
class AppStrings {
  // App Name & Branding
  static const String appName = 'SafeDrive';
  static const String appTagline = 'Drive Safe, Earn Rewards';

  // Auth Home Screen
  static const String welcomeTitle = 'Welcome to SafeDrive';
  static const String welcomeMessage =
      'Join our intelligent traffic management rewards system';
  static const String loginButton = 'Login';
  static const String registerButton = 'New Register';
  static const String googleLoginButton = 'Continue with Google';

  // Login Screen
  static const String loginTitle = 'Driver Login';
  static const String plateNumberLabel = 'Vehicle Number Plate';
  static const String plateNumberHint = 'e.g., DL01AB1234';
  static const String passwordLabel = 'Password';
  static const String passwordHint = 'Enter your password';
  static const String loginSubmitButton = 'Login';
  static const String forgotPassword = 'Forgot Password?';

  // Registration Screen
  static const String registerTitle = 'New Driver Registration';
  static const String ownerNameLabel = 'Owner Full Name';
  static const String ownerNameHint = 'Enter your full name';
  static const String mobileLabel = 'Mobile Number';
  static const String mobileHint = '10-digit mobile number';
  static const String emailLabel = 'Email ID';
  static const String emailHint = 'your.email@example.com';
  static const String vehicleTypeLabel = 'Vehicle Type';
  static const String vehicleTypeHint = 'Select vehicle type';
  static const String confirmPasswordLabel = 'Confirm Password';
  static const String confirmPasswordHint = 'Re-enter your password';
  static const String registerSubmitButton = 'Register';

  // Vehicle Types
  static const List<String> vehicleTypes = [
    'Car',
    'Bike',
    'Truck',
    'Auto',
    'Bus',
  ];

  // Validation Messages
  static const String plateFormatError =
      'Invalid plate format. Use: AA00BB0000';
  static const String plateRequiredError = 'Vehicle plate number is required';
  static const String nameRequiredError = 'Owner name is required';
  static const String mobileFormatError = 'Mobile number must be 10 digits';
  static const String mobileRequiredError = 'Mobile number is required';
  static const String emailFormatError = 'Invalid email address';
  static const String emailRequiredError = 'Email is required';
  static const String vehicleTypeRequiredError =
      'Please select a vehicle type';
  static const String passwordRequiredError = 'Password is required';
  static const String passwordFormatError =
      'Min 6 chars with at least 1 letter and 1 digit';
  static const String confirmPasswordError = 'Passwords do not match';

  // Success Messages
  static const String loginSuccess = 'Login successful!';
  static const String registrationSuccess = 'Registration successful!';
  static const String googleLoginSuccess = 'Google login successful!';

  // Error Messages
  static const String loginFailed = 'Login failed. Please try again.';
  static const String registrationFailed =
      'Registration failed. Please try again.';
  static const String networkError =
      'Network error. Please check your connection.';
  static const String googleLoginFailed =
      'Google login failed. Please try again.';

  // Dashboard
  static const String dashboardTitle = 'Dashboard';
  static const String dashboardWelcome = 'Welcome to your dashboard!';
  static const String dashboardPlaceholder =
      'Dashboard features coming soon...';
  static const String logoutButton = 'Logout';

  // Legacy — kept for backward compat with existing tests
  static const String driverIdLabel = 'Driver ID (Optional)';
  static const String driverIdHint = 'Enter your driver ID';
}
