import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:webview_flutter/webview_flutter.dart';

const Color kBoardBg = Color(0xFF10151B);
const Color kChalk = Color(0xFFEDF1F5);

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      statusBarBrightness: Brightness.dark,
      systemNavigationBarColor: kBoardBg,
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );
  runApp(const VolleyLabApp());
}

class VolleyLabApp extends StatelessWidget {
  const VolleyLabApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '排球研习',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: kBoardBg,
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFFF2A03C),
          surface: Color(0xFF1A212B),
        ),
        fontFamily: 'sans-serif',
      ),
      home: const BoardWebView(),
    );
  }
}

class BoardWebView extends StatefulWidget {
  const BoardWebView({super.key});

  @override
  State<BoardWebView> createState() => _BoardWebViewState();
}

class _BoardWebViewState extends State<BoardWebView> {
  late final WebViewController _controller;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(kBoardBg)
      ..enableZoom(false)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (_) => SystemChrome.setSystemUIOverlayStyle(
            const SystemUiOverlayStyle(
              statusBarColor: Colors.transparent,
              statusBarIconBrightness: Brightness.light,
              systemNavigationBarColor: kBoardBg,
              systemNavigationBarIconBrightness: Brightness.light,
            ),
          ),
          onWebResourceError: (error) {
            debugPrint('WebView error: ${error.description}');
          },
        ),
      )
      ..loadFlutterAsset('assets/www/index.html');
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        if (await _controller.canGoBack()) {
          await _controller.goBack();
        } else {
          await SystemNavigator.pop();
        }
      },
      child: Scaffold(
        backgroundColor: kBoardBg,
        body: SafeArea(
          top: true,
          bottom: true,
          minimum: const EdgeInsets.only(top: 10),
          child: WebViewWidget(controller: _controller),
        ),
      ),
    );
  }
}
