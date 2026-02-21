import 'package:flutter_test/flutter_test.dart';
import 'package:reward_user_app/utils/validators.dart';

void main() {
  group('Validators Tests', () {
    group('validatePlateNumber', () {
      test('should return null for valid plate number', () {
        expect(Validators.validatePlateNumber('DL01AB1234'), null);
        expect(Validators.validatePlateNumber('MH12CD5678'), null);
      });

      test('should return error for invalid format', () {
        expect(Validators.validatePlateNumber('DL01AB123'), isNotNull);
        expect(Validators.validatePlateNumber('1234567890'), isNotNull);
      });
    });

    group('validateEmail', () {
      test('should return null for valid email', () {
        expect(Validators.validateEmail('test@example.com'), null);
      });

      test('should return error for invalid email', () {
        expect(Validators.validateEmail('invalid-email'), isNotNull);
      });
    });

    group('validatePassword', () {
      test('should return null for valid password (min 6 chars, letter + digit)', () {
        expect(Validators.validatePassword('pass123'), null);
        expect(Validators.validatePassword('a1b2c3d4'), null);
      });

      test('should return error for short password', () {
        expect(Validators.validatePassword('p1'), isNotNull);
      });

      test('should return error for password without numbers', () {
        expect(Validators.validatePassword('password'), isNotNull);
      });

      test('should return error for password without letters', () {
        expect(Validators.validatePassword('123456'), isNotNull);
      });
    });

    group('validateConfirmPassword', () {
      test('should return null if passwords match', () {
        expect(Validators.validateConfirmPassword('pass123', 'pass123'), null);
      });

      test('should return error if passwords do not match', () {
        expect(Validators.validateConfirmPassword('wrong', 'pass123'), isNotNull);
      });
    });
  });
}
