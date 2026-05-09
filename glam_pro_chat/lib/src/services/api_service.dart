/// HTTP service layer for communicating with the Glam Pro backend API.
library;

import 'dart:convert';
import 'package:http/http.dart' as http;

/// Structured result from a chat API call.
class ChatResult {
  /// The assistant's reply text.
  final String reply;

  /// The session ID echoed back by the server.
  final String sessionId;

  const ChatResult({required this.reply, required this.sessionId});
}

/// Exception thrown when the API returns an unexpected response.
class ApiException implements Exception {
  final String message;
  final int? statusCode;

  const ApiException(this.message, {this.statusCode});

  @override
  String toString() =>
      'ApiException(${statusCode != null ? "$statusCode: " : ""}$message)';
}

/// Service class that wraps all Glam Pro backend REST calls.
///
/// Example:
/// ```dart
/// final service = GlamApiService(baseUrl: 'http://192.168.1.10:8000');
/// final sessionId = await service.createSession();
/// final result = await service.sendMessage(sessionId, 'Hello!');
/// print(result.reply);
/// ```
class GlamApiService {
  /// Base URL of the Glam Pro backend (no trailing slash).
  final String baseUrl;

  /// HTTP client – injectable for testing.
  final http.Client _client;

  /// Request/response timeout duration.
  static const Duration _timeout = Duration(seconds: 90);

  GlamApiService({required this.baseUrl, http.Client? client})
      : _client = client ?? http.Client();

  // -------------------------------------------------------------------------
  // Session
  // -------------------------------------------------------------------------

  /// Creates a new conversation session on the server.
  ///
  /// Returns the UUID session ID.
  /// Throws [ApiException] on error.
  Future<String> createSession() async {
    final uri = Uri.parse('$baseUrl/session/new');
    final http.Response response;

    try {
      response = await _client.get(uri).timeout(_timeout);
    } catch (e) {
      throw ApiException('Network error: $e');
    }

    if (response.statusCode == 200) {
      final data = json.decode(response.body) as Map<String, dynamic>;
      return data['session_id'] as String;
    }

    throw ApiException(
      'Failed to create session (${response.statusCode}): ${response.body}',
      statusCode: response.statusCode,
    );
  }

  // -------------------------------------------------------------------------
  // Chat
  // -------------------------------------------------------------------------

  /// Sends [message] to the server in the context of [sessionId].
  ///
  /// Returns a [ChatResult] containing the assistant's reply.
  /// Throws [ApiException] on error.
  Future<ChatResult> sendMessage(String sessionId, String message) async {
    final uri = Uri.parse('$baseUrl/chat');
    final http.Response response;

    try {
      response = await _client
          .post(
            uri,
            headers: {'Content-Type': 'application/json; charset=utf-8'},
            body: json.encode({
              'session_id': sessionId,
              'message': message,
            }),
          )
          .timeout(_timeout);
    } catch (e) {
      throw ApiException('Network error: $e');
    }

    if (response.statusCode == 200) {
      final data =
          json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      return ChatResult(
        reply: data['reply'] as String,
        sessionId: data['session_id'] as String,
      );
    }

    // 503 = LLM not loaded yet
    if (response.statusCode == 503) {
      throw const ApiException(
        'The AI model is still loading. Please try again in a moment.',
        statusCode: 503,
      );
    }

    throw ApiException(
      'Chat request failed (${response.statusCode}): ${response.body}',
      statusCode: response.statusCode,
    );
  }

  // -------------------------------------------------------------------------
  // Health (optional – useful for connection checking)
  // -------------------------------------------------------------------------

  /// Checks if the backend is reachable and returns the health data map.
  Future<Map<String, dynamic>> health() async {
    final uri = Uri.parse('$baseUrl/health');
    try {
      final response =
          await _client.get(uri).timeout(const Duration(seconds: 10));
      if (response.statusCode == 200) {
        return json.decode(response.body) as Map<String, dynamic>;
      }
    } catch (_) {}
    return {'status': 'unreachable'};
  }

  /// Disposes the underlying HTTP client.
  void dispose() => _client.close();
}
