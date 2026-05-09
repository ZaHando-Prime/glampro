/// Glam Pro Chat – Public API
///
/// Import this file in your Flutter app:
/// ```dart
/// import 'package:glam_pro_chat/glam_pro_chat.dart';
/// ```
///
/// Then use the widget:
/// ```dart
/// GlamProChat(apiUrl: 'http://your-server:8000')
/// ```
library glam_pro_chat;

export 'src/models/chat_message.dart';
export 'src/providers/chat_provider.dart';
export 'src/services/api_service.dart';
export 'src/widgets/glam_chat_screen.dart';
