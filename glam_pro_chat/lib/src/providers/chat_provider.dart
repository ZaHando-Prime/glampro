/// State management provider for the Glam Pro chat widget.
library;

import 'package:flutter/foundation.dart';
import '../models/chat_message.dart';
import '../services/api_service.dart';

/// The current initialisation state of the chat.
enum ChatInitState {
  /// Session creation is in progress.
  initialising,

  /// Ready to send and receive messages.
  ready,

  /// Session creation failed – network or server error.
  error,
}

/// ChangeNotifier that drives the entire chat UI.
///
/// Responsibilities:
/// - Creates a session with the backend on construction.
/// - Sends user messages and stores replies.
/// - Manages loading state for the typing indicator.
/// - Exposes error messages for the UI.
class ChatProvider extends ChangeNotifier {
  final GlamApiService _api;

  // -------------------------------------------------------------------------
  // State
  // -------------------------------------------------------------------------

  /// All messages in the current conversation (newest last).
  final List<ChatMessage> _messages = [];

  /// Whether the assistant is currently generating a reply.
  bool _isLoading = false;

  /// The active session ID (set after [_init] completes).
  String _sessionId = '';

  /// Current initialisation state.
  ChatInitState _initState = ChatInitState.initialising;

  /// Human-readable error message (non-empty when [_initState] == error or
  /// when an individual send fails).
  String _errorMessage = '';

  // -------------------------------------------------------------------------
  // Getters (read-only surface exposed to widgets)
  // -------------------------------------------------------------------------

  List<ChatMessage> get messages => List.unmodifiable(_messages);
  bool get isLoading => _isLoading;
  String get sessionId => _sessionId;
  ChatInitState get initState => _initState;
  String get errorMessage => _errorMessage;
  bool get isReady => _initState == ChatInitState.ready;

  // -------------------------------------------------------------------------
  // Constructor
  // -------------------------------------------------------------------------

  ChatProvider({required GlamApiService api}) : _api = api {
    _init();
  }

  // -------------------------------------------------------------------------
  // Initialisation
  // -------------------------------------------------------------------------

  Future<void> _init() async {
    _initState = ChatInitState.initialising;
    _errorMessage = '';
    notifyListeners();

    try {
      _sessionId = await _api.createSession();
      _initState = ChatInitState.ready;

      // Welcome message so the chat screen is never empty
      _messages.add(
        ChatMessage.assistant(
          '✨ Welcome to Glam Pro Beauty Assistant!\n\n'
          'I can help you find the perfect beauty products and answer any '
          'questions about the Glam Pro app. How can I help you today?',
        ),
      );
    } catch (e) {
      _initState = ChatInitState.error;
      _errorMessage =
          'Could not connect to the Glam Pro server. Please check your '
          'connection and try again.\n\nDetails: $e';
    }

    notifyListeners();
  }

  /// Retries session creation after a failure.
  Future<void> retry() => _init();

  // -------------------------------------------------------------------------
  // Sending messages
  // -------------------------------------------------------------------------

  /// Sends [text] to the backend and appends both the user message and the
  /// assistant's reply to [messages].
  ///
  /// No-ops when [isLoading] is true or the session is not ready.
  Future<void> sendMessage(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty || _isLoading || !isReady) return;

    // Immediately add the user message to the UI
    _messages.add(ChatMessage.user(trimmed));
    _isLoading = true;
    _errorMessage = '';
    notifyListeners();

    try {
      final result = await _api.sendMessage(_sessionId, trimmed);
      _messages.add(ChatMessage.assistant(result.reply));
    } on ApiException catch (e) {
      // Show error as an assistant bubble so the user sees it in context
      _messages.add(
        ChatMessage.assistant(
          '⚠️ ${e.message}',
        ),
      );
      _errorMessage = e.message;
    } catch (e) {
      _messages.add(
        ChatMessage.assistant(
          '⚠️ An unexpected error occurred. Please try again.',
        ),
      );
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // -------------------------------------------------------------------------
  // Cleanup
  // -------------------------------------------------------------------------

  @override
  void dispose() {
    _api.dispose();
    super.dispose();
  }
}
