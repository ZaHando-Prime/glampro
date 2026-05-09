/// Text input bar with send button for the Glam Pro chat widget.
library;

import 'package:flutter/material.dart';

/// A styled text field + send button anchored at the bottom of the chat screen.
///
/// Calls [onSend] with the trimmed text when the user taps send or presses
/// the keyboard's submit action. Disabled while [enabled] is false.
class ChatInput extends StatefulWidget {
  /// Called with the trimmed message text when the user submits.
  final ValueChanged<String> onSend;

  /// When false the input and send button are visually disabled (e.g. while
  /// the assistant is generating a reply).
  final bool enabled;

  /// Placeholder text shown inside the empty field.
  final String hintText;

  const ChatInput({
    super.key,
    required this.onSend,
    this.enabled = true,
    this.hintText = 'Ask me anything about beauty…',
  });

  @override
  State<ChatInput> createState() => _ChatInputState();
}

class _ChatInputState extends State<ChatInput> {
  final TextEditingController _controller = TextEditingController();
  bool _hasText = false;

  // Design tokens
  static const Color _rose = Color(0xFFD4467B);
  static const Color _gold = Color(0xFFC9A84C);
  static const Color _surfaceColor = Color(0xFFFFFFFF);
  static const Color _borderColor = Color(0xFFF0D6E4);
  static const Color _hintColor = Color(0xFFB0A0B5);
  static const Color _textColor = Color(0xFF2D1B2E);

  @override
  void initState() {
    super.initState();
    _controller.addListener(_onTextChanged);
  }

  void _onTextChanged() {
    final hasText = _controller.text.trim().isNotEmpty;
    if (hasText != _hasText) {
      setState(() => _hasText = hasText);
    }
  }

  void _submit() {
    final text = _controller.text.trim();
    if (text.isEmpty || !widget.enabled) return;
    _controller.clear();
    widget.onSend(text);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.only(
        left: 12,
        right: 12,
        top: 10,
        bottom: MediaQuery.of(context).viewInsets.bottom > 0 ? 10 : 18,
      ),
      decoration: BoxDecoration(
        color: _surfaceColor,
        boxShadow: [
          BoxShadow(
            color: _rose.withOpacity(0.08),
            blurRadius: 20,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            // ── Text field ──────────────────────────────────────────────
            Expanded(
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFF5F8),
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(
                    color: widget.enabled && _hasText ? _rose : _borderColor,
                    width: 1.5,
                  ),
                ),
                child: TextField(
                  controller: _controller,
                  enabled: widget.enabled,
                  minLines: 1,
                  maxLines: 5,
                  textInputAction: TextInputAction.send,
                  onSubmitted: (_) => _submit(),
                  style: const TextStyle(
                    color: _textColor,
                    fontSize: 15,
                    fontFamily: 'Poppins',
                  ),
                  decoration: InputDecoration(
                    hintText: widget.hintText,
                    hintStyle: const TextStyle(
                      color: _hintColor,
                      fontSize: 14,
                      fontFamily: 'Poppins',
                    ),
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 12,
                    ),
                  ),
                ),
              ),
            ),

            const SizedBox(width: 10),

            // ── Send button ─────────────────────────────────────────────
            AnimatedScale(
              scale: _hasText && widget.enabled ? 1.0 : 0.85,
              duration: const Duration(milliseconds: 200),
              curve: Curves.easeOut,
              child: GestureDetector(
                onTap: _submit,
                child: Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: _hasText && widget.enabled
                          ? [_rose, const Color(0xFFE8306A)]
                          : [_hintColor, _hintColor],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    shape: BoxShape.circle,
                    boxShadow: _hasText && widget.enabled
                        ? [
                            BoxShadow(
                              color: _rose.withOpacity(0.4),
                              blurRadius: 12,
                              offset: const Offset(0, 4),
                            ),
                          ]
                        : [],
                  ),
                  child: const Icon(
                    Icons.send_rounded,
                    color: Colors.white,
                    size: 22,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
