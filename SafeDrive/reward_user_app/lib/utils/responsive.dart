import 'package:flutter/material.dart';

class Responsive {
  static late MediaQueryData _mediaQueryData;
  static late double screenWidth;
  static late double screenHeight;
  static late double _safeAreaHorizontal;
  static late double _safeAreaVertical;

  void init(BuildContext context) {
    _mediaQueryData = MediaQuery.of(context);
    screenWidth = _mediaQueryData.size.width;
    screenHeight = _mediaQueryData.size.height;
    _safeAreaHorizontal = _mediaQueryData.padding.left + _mediaQueryData.padding.right;
    _safeAreaVertical = _mediaQueryData.padding.top + _mediaQueryData.padding.bottom;
  }

  static double width(double percent) {
    return (screenWidth) * (percent / 100);
  }

  static double height(double percent) {
    return (screenHeight) * (percent / 100);
  }

  static double sp(double size) {
    return width(size * 0.25); // Scaling factor for font sizes
  }
}
