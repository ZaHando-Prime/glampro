/// Glam Pro Chat – Example App
///
/// Demonstrates the minimal code needed to integrate the GlamProChat widget.
///
/// Before running:
///   1. Start the Python backend: `uvicorn main:app --host 0.0.0.0 --port 8000`
///   2. Replace [_apiUrl] below with your server's IP address.
///   3. `flutter run` in this directory.

import 'package:flutter/material.dart';
import 'package:glam_pro_chat/glam_pro_chat.dart';

import 'package:flutter/foundation.dart';

/// Replace with your backend server address.
/// - Android emulator → use 10.0.2.2 instead of localhost
/// - iOS simulator    → use localhost or 127.0.0.1
/// - Physical device  → use your machine's LAN IP (e.g. 192.168.1.10)
/// - Web browser      → use localhost or 127.0.0.1
const String _apiUrl = kIsWeb ? 'http://127.0.0.1:8000' : 'http://10.0.2.2:8000';

void main() {
  runApp(const GlamProExampleApp());
}

class GlamProExampleApp extends StatelessWidget {
  const GlamProExampleApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Glam Pro Chat Demo',
      debugShowCheckedModeBanner: false,
      // The app supports both LTR (English) and RTL (Arabic).
      // Flutter automatically picks up the device locale; you can also force
      // a direction by wrapping with Directionality(textDirection: ...).
      supportedLocales: const [
        Locale('en'),
        Locale('ar'),
      ],
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFD4467B),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
      ),
      home: const _HomeScreen(),
    );
  }
}

class _HomeScreen extends StatelessWidget {
  const _HomeScreen();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // ── Option A: Full-screen chat ────────────────────────────────────
      // Simply place GlamProChat as the body for a full-screen experience.
      body: GlamProChat(
        apiUrl: _apiUrl,
        appBarTitle: 'Glam Pro Assistant',
        inputHint: 'Ask me about skincare, makeup, or the app…',
      ),

      // ── Option B: Push to a dedicated chat page ───────────────────────
      // Uncomment and use a button or nav item to push _ChatPage instead.
      //
      // body: Center(
      //   child: ElevatedButton(
      //     child: const Text('Open Beauty Assistant'),
      //     onPressed: () => Navigator.push(
      //       context,
      //       MaterialPageRoute(builder: (_) => const _ChatPage()),
      //     ),
      //   ),
      // ),
    );
  }
}

// Uncomment for Option B
// class _ChatPage extends StatelessWidget {
//   const _ChatPage();
//
//   @override
//   Widget build(BuildContext context) {
//     return GlamProChat(
//       apiUrl: _apiUrl,
//       appBarTitle: 'Beauty Expert',
//     );
//   }
// }
