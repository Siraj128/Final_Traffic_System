import 'package:flutter_test/flutter_test.dart';
import 'package:reward_user_app/main.dart';
import 'package:reward_user_app/constants/app_strings.dart';

void main() {
  testWidgets('SafeDrive Rewards app smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const SafeDriveRewardsApp());

    // Verify that the app name appears
    expect(find.text(AppStrings.appName), findsOneWidget);
    
    // Verify that Login and New Register buttons are present
    expect(find.text(AppStrings.loginButton), findsOneWidget);
    expect(find.text(AppStrings.registerButton), findsOneWidget);
    
    // Verify Google Login button exists (by looking for the text)
    expect(find.text(AppStrings.googleLoginButton), findsOneWidget);
  });
}
