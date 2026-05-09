/// Animated typing indicator – three bouncing dots shown while the assistant
/// is generating a reply.
library;

import 'package:flutter/material.dart';

/// A row of three dots that animate in sequence to indicate the assistant
/// is typing. Automatically starts/stops the animation based on [visible].
class TypingIndicator extends StatefulWidget {
  /// Whether the indicator is currently visible and animating.
  final bool visible;

  const TypingIndicator({super.key, required this.visible});

  @override
  State<TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<TypingIndicator>
    with TickerProviderStateMixin {
  static const int _dotCount = 3;
  static const Duration _interval = Duration(milliseconds: 250);
  static const Duration _dotDuration = Duration(milliseconds: 500);

  final List<AnimationController> _controllers = [];
  final List<Animation<double>> _animations = [];

  @override
  void initState() {
    super.initState();
    for (int i = 0; i < _dotCount; i++) {
      final ctrl = AnimationController(vsync: this, duration: _dotDuration);
      ctrl.addStatusListener((status) {
        if (status == AnimationStatus.completed) ctrl.reverse();
      });

      _controllers.add(ctrl);
      _animations.add(
        Tween<double>(begin: 0.0, end: -6.0).animate(
          CurvedAnimation(parent: ctrl, curve: Curves.easeInOut),
        ),
      );
    }
    if (widget.visible) _startAnimation();
  }

  @override
  void didUpdateWidget(TypingIndicator oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.visible && !oldWidget.visible) {
      _startAnimation();
    } else if (!widget.visible && oldWidget.visible) {
      _stopAnimation();
    }
  }

  void _startAnimation() {
    for (int i = 0; i < _dotCount; i++) {
      Future.delayed(_interval * i, () {
        if (mounted && _controllers[i].status == AnimationStatus.dismissed) {
          _controllers[i].repeat(reverse: true);
        }
      });
    }
  }

  void _stopAnimation() {
    for (final ctrl in _controllers) {
      ctrl.stop();
      ctrl.reset();
    }
  }

  @override
  void dispose() {
    for (final ctrl in _controllers) {
      ctrl.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.visible) return const SizedBox.shrink();

    return Align(
      alignment: AlignmentDirectional.centerStart,
      child: Container(
        margin: const EdgeInsetsDirectional.only(start: 16, bottom: 8, end: 80),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(18),
            topRight: Radius.circular(18),
            bottomLeft: Radius.circular(4),
            bottomRight: Radius.circular(18),
          ),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFFD4467B).withOpacity(0.08),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(_dotCount, (i) {
            return AnimatedBuilder(
              animation: _animations[i],
              builder: (_, __) => Transform.translate(
                offset: Offset(0, _animations[i].value),
                child: Container(
                  width: 8,
                  height: 8,
                  margin: const EdgeInsets.symmetric(horizontal: 3),
                  decoration: const BoxDecoration(
                    color: Color(0xFFD4467B),
                    shape: BoxShape.circle,
                  ),
                ),
              ),
            );
          }),
        ),
      ),
    );
  }
}
