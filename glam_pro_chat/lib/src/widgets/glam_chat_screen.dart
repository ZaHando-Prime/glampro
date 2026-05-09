/// Full-screen Glam Pro chat experience.
///
/// This is the primary public widget of the package. Drop it into any
/// Flutter Scaffold body (or use it standalone) to embed the beauty
/// assistant chat.
library;

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../models/chat_message.dart';
import '../providers/chat_provider.dart';
import '../services/api_service.dart';
import 'chat_bubble.dart';
import 'chat_input.dart';
import 'typing_indicator.dart';

// ──────────────────────────────────────────────────────────────────────────────
// Glam Pro design tokens
// ──────────────────────────────────────────────────────────────────────────────

class _GlamTheme {
  static const Color rose = Color(0xFFD4467B);
  static const Color roseDeep = Color(0xFFB8375F);
  static const Color gold = Color(0xFFC9A84C);
  static const Color blushWhite = Color(0xFFFFF5F8);
  static const Color darkPlum = Color(0xFF2D1B2E);
  static const Color softLilac = Color(0xFFF3E6EE);

  static LinearGradient get appBarGradient => const LinearGradient(
        colors: [Color(0xFFD4467B), Color(0xFF9B2456)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      );

  static TextStyle get titleStyle => GoogleFonts.poppins(
        color: Colors.white,
        fontSize: 18,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.3,
      );
}

// ──────────────────────────────────────────────────────────────────────────────
// Public widget
// ──────────────────────────────────────────────────────────────────────────────

/// The Glam Pro Beauty Assistant chat widget.
///
/// ```dart
/// // Minimal usage:
/// GlamProChat(apiUrl: 'http://192.168.1.10:8000')
///
/// // With custom title:
/// GlamProChat(
///   apiUrl: 'http://192.168.1.10:8000',
///   appBarTitle: 'Beauty Expert',
/// )
/// ```
class GlamProChat extends StatelessWidget {
  /// Base URL of the Glam Pro backend API (no trailing slash).
  /// Example: `'http://192.168.1.10:8000'`
  final String apiUrl;

  /// Title shown in the app bar. Defaults to `'Glam Pro Assistant'`.
  final String appBarTitle;

  /// Hint text displayed inside the message input field.
  final String inputHint;

  const GlamProChat({
    super.key,
    required this.apiUrl,
    this.appBarTitle = 'Glam Pro Assistant',
    this.inputHint = 'Ask me anything about beauty…',
  });

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => ChatProvider(
        api: GlamApiService(baseUrl: apiUrl),
      ),
      child: _GlamChatScreen(
        appBarTitle: appBarTitle,
        inputHint: inputHint,
      ),
    );
  }
}

// ──────────────────────────────────────────────────────────────────────────────
// Internal screen
// ──────────────────────────────────────────────────────────────────────────────

class _GlamChatScreen extends StatefulWidget {
  final String appBarTitle;
  final String inputHint;

  const _GlamChatScreen({
    required this.appBarTitle,
    required this.inputHint,
  });

  @override
  State<_GlamChatScreen> createState() => _GlamChatScreenState();
}

class _GlamChatScreenState extends State<_GlamChatScreen> {
  final ScrollController _scrollController = ScrollController();

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    // Determine text direction from device locale for RTL Arabic support
    final isRtl = Directionality.of(context) == TextDirection.rtl;

    return Consumer<ChatProvider>(
      builder: (context, provider, _) {
        // Auto-scroll when new messages arrive or loading state changes
        if (provider.messages.isNotEmpty || provider.isLoading) {
          _scrollToBottom();
        }

        return Scaffold(
          backgroundColor: _GlamTheme.blushWhite,
          appBar: _buildAppBar(context, provider, isRtl),
          body: Column(
            children: [
              // ── Message list ───────────────────────────────────────────
              Expanded(
                child: _buildBody(provider),
              ),

              // ── Typing indicator ───────────────────────────────────────
              TypingIndicator(visible: provider.isLoading),

              // ── Divider accent ─────────────────────────────────────────
              Container(
                height: 1,
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Color(0xFFD4467B), Color(0xFFC9A84C)],
                  ),
                ),
              ),

              // ── Input bar ──────────────────────────────────────────────
              ChatInput(
                enabled: provider.isReady && !provider.isLoading,
                hintText: widget.inputHint,
                onSend: provider.sendMessage,
              ),
            ],
          ),
        );
      },
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // App bar
  // ──────────────────────────────────────────────────────────────────────────

  PreferredSizeWidget _buildAppBar(
    BuildContext context,
    ChatProvider provider,
    bool isRtl,
  ) {
    return PreferredSize(
      preferredSize: const Size.fromHeight(64),
      child: Container(
        decoration: BoxDecoration(
          gradient: _GlamTheme.appBarGradient,
          boxShadow: [
            BoxShadow(
              color: _GlamTheme.rose.withOpacity(0.35),
              blurRadius: 16,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: SafeArea(
          bottom: false,
          child: Padding(
            padding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              children: [
                // Avatar
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: Colors.white.withOpacity(0.5),
                      width: 1.5,
                    ),
                  ),
                  child: const Icon(
                    Icons.auto_awesome,
                    color: Colors.white,
                    size: 22,
                  ),
                ),

                const SizedBox(width: 12),

                // Title + status
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(widget.appBarTitle, style: _GlamTheme.titleStyle),
                      const SizedBox(height: 2),
                      _buildStatusRow(provider),
                    ],
                  ),
                ),

                // Gold sparkle icon
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: _GlamTheme.gold.withOpacity(0.25),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.spa_rounded,
                    color: Colors.white,
                    size: 18,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStatusRow(ChatProvider provider) {
    final String label;
    final Color dotColor;

    switch (provider.initState) {
      case ChatInitState.initialising:
        label = 'Connecting…';
        dotColor = Colors.amberAccent;
      case ChatInitState.ready:
        label = provider.isLoading ? 'Typing…' : 'Online';
        dotColor = Colors.greenAccent;
      case ChatInitState.error:
        label = 'Offline';
        dotColor = Colors.redAccent;
    }

    return Row(
      children: [
        Container(
          width: 7,
          height: 7,
          decoration: BoxDecoration(color: dotColor, shape: BoxShape.circle),
        ),
        const SizedBox(width: 5),
        Text(
          label,
          style: GoogleFonts.poppins(
            color: Colors.white.withOpacity(0.85),
            fontSize: 11,
          ),
        ),
      ],
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Body states
  // ──────────────────────────────────────────────────────────────────────────

  Widget _buildBody(ChatProvider provider) {
    // Initialising spinner
    if (provider.initState == ChatInitState.initialising) {
      return _buildCentredState(
        icon: Icons.auto_awesome,
        title: 'Starting your beauty session…',
        subtitle: 'Warming up the assistant, just a moment.',
        showSpinner: true,
      );
    }

    // Connection error
    if (provider.initState == ChatInitState.error) {
      return _buildCentredState(
        icon: Icons.wifi_off_rounded,
        title: 'Could not connect',
        subtitle: provider.errorMessage,
        actionLabel: 'Retry',
        onAction: provider.retry,
      );
    }

    // Chat messages
    if (provider.messages.isEmpty) {
      return _buildCentredState(
        icon: Icons.spa_rounded,
        title: 'Your Beauty Expert',
        subtitle: 'Ask me about skincare, makeup, haircare\nor how to use the Glam Pro app.',
      );
    }

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(vertical: 12),
      itemCount: provider.messages.length,
      itemBuilder: (_, index) {
        return AnimatedOpacity(
          opacity: 1,
          duration: const Duration(milliseconds: 300),
          child: ChatBubble(message: provider.messages[index]),
        );
      },
    );
  }

  Widget _buildCentredState({
    required IconData icon,
    required String title,
    required String subtitle,
    bool showSpinner = false,
    String? actionLabel,
    VoidCallback? onAction,
  }) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Icon in a rose circle
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    _GlamTheme.rose.withOpacity(0.15),
                    _GlamTheme.gold.withOpacity(0.1),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: _GlamTheme.rose, size: 36),
            ),
            const SizedBox(height: 20),

            if (showSpinner) ...[
              const SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(
                  color: _GlamTheme.rose,
                  strokeWidth: 2.5,
                ),
              ),
              const SizedBox(height: 16),
            ],

            Text(
              title,
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(
                color: _GlamTheme.darkPlum,
                fontSize: 17,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              subtitle,
              textAlign: TextAlign.center,
              style: GoogleFonts.poppins(
                color: const Color(0xFF8C7A94),
                fontSize: 13,
                height: 1.6,
              ),
            ),

            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: onAction,
                style: ElevatedButton.styleFrom(
                  backgroundColor: _GlamTheme.rose,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 32,
                    vertical: 14,
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(24),
                  ),
                  elevation: 4,
                  shadowColor: _GlamTheme.rose.withOpacity(0.4),
                ),
                child: Text(
                  actionLabel,
                  style: GoogleFonts.poppins(
                    fontWeight: FontWeight.w600,
                    fontSize: 14,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
