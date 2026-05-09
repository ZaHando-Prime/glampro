/// Individual chat message bubble widget.
library;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart' hide TextDirection;
import '../models/chat_message.dart';

/// Renders a single [ChatMessage] as a styled speech bubble.
///
/// - User messages: right-aligned, deep rose gradient.
/// - Assistant messages: left-aligned, soft ivory with subtle shadow.
class ChatBubble extends StatelessWidget {
  final ChatMessage message;

  const ChatBubble({super.key, required this.message});

  // Design tokens
  static const Color _roseStart = Color(0xFFD4467B);
  static const Color _roseEnd = Color(0xFFE8306A);
  static const Color _assistantBg = Color(0xFFFFFFFF);
  static const Color _userTextColor = Colors.white;
  static const Color _assistantTextColor = Color(0xFF2D1B2E);
  static const Color _timestampColor = Color(0xFFB0A0B5);
  static const Color _shadowColor = Color(0xFFD4467B);

  @override
  Widget build(BuildContext context) {
    final isUser = message.isUser;
    final timeLabel = DateFormat('HH:mm').format(message.timestamp);

    return Padding(
      padding: EdgeInsetsDirectional.only(
        start: isUser ? 64.0 : 16.0,
        end: isUser ? 16.0 : 64.0,
        top: 4,
        bottom: 4,
      ),
      child: Column(
        crossAxisAlignment:
            isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          // ---- Bubble ----
          Container(
            decoration: BoxDecoration(
              gradient: isUser
                  ? const LinearGradient(
                      colors: [_roseStart, _roseEnd],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    )
                  : null,
              color: isUser ? null : _assistantBg,
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(18),
                topRight: const Radius.circular(18),
                bottomLeft:
                    isUser ? const Radius.circular(18) : const Radius.circular(4),
                bottomRight:
                    isUser ? const Radius.circular(4) : const Radius.circular(18),
              ),
              boxShadow: [
                BoxShadow(
                  color: isUser
                      ? _shadowColor.withOpacity(0.25)
                      : Colors.black.withOpacity(0.06),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: SelectableText(
              message.content,
              textDirection: Bidi.hasAnyRtl(message.content)
                  ? TextDirection.rtl
                  : TextDirection.ltr,
              style: TextStyle(
                color: isUser ? _userTextColor : _assistantTextColor,
                fontSize: 15,
                height: 1.5,
                fontFamily: 'Poppins',
              ),
            ),
          ),

          // ---- Timestamp ----
          const SizedBox(height: 4),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: Text(
              timeLabel,
              style: const TextStyle(
                color: _timestampColor,
                fontSize: 11,
                fontFamily: 'Poppins',
              ),
            ),
          ),
        ],
      ),
    );
  }
}
