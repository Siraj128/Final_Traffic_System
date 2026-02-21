import 'package:flutter_test/flutter_test.dart';
import 'package:reward_user_app/services/api_service.dart';

void main() {
  late ApiService apiService;

  setUp(() {
    apiService = ApiService();
  });

  group('ApiService Tests', () {
    group('loginDriver', () {
      test('should return success response with mock data', () async {
        final response = await apiService.loginDriver(
          plateNumber: 'DL01AB1234',
          password: 'password123',
        );

        expect(response['success'], true);
        expect(response['message'], 'Login successful');
        expect(response['data'], isNotNull);
        expect(response['data']['plate_number'], 'DL01AB1234');
        expect(response['data']['token'], isNotNull);
      });

      test('should simulate network delay', () async {
        final stopwatch = Stopwatch()..start();
        await apiService.loginDriver(
          plateNumber: 'DL01AB1234',
          password: 'password123',
        );
        stopwatch.stop();

        expect(stopwatch.elapsedMilliseconds, greaterThanOrEqualTo(900));
      });
    });

    group('registerDriver', () {
      test('should return success response with all registration data', () async {
        final response = await apiService.registerDriver(
          plateNumber: 'KA03EF9012',
          ownerName: 'John Doe',
          mobileNumber: '9876543210',
          email: 'john@example.com',
          password: 'password123',
          vehicleType: 'Car',
        );

        expect(response['success'], true);
        expect(response['message'], 'Registration successful');
        expect(response['data'], isNotNull);
        expect(response['data']['plate_number'], 'KA03EF9012');
      });
    });

    group('googleLogin', () {
      test('should return success response for Google OAuth', () async {
        final response = await apiService.googleLogin(
          googleToken: 'mock_token',
        );

        expect(response['success'], true);
        expect(response['data']['auth_provider'], 'google');
      });
    });

    group('Error simulation', () {
      test('loginDriverWithError should return failure', () async {
        final response = await apiService.loginDriverWithError();
        expect(response['success'], false);
      });
    });
  });
}
