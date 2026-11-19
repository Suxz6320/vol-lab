"""本地静态服务器（端口 8000）— 用于调试 file:// 协议下的 Three.js 加载问题"""
import http.server
import socketserver
import threading
import webbrowser
import os

PORT = 8000
ROOT = r"c:\Users\33685\Desktop\val\volleylab_app\assets\www"
os.chdir(ROOT)

Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    url = f"http://127.0.0.1:{PORT}/skill-spike.html"
    print(f"Serving: {ROOT}")
    print(f"URL: {url}")
    print("Press Ctrl+C to stop")
    threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
    httpd.serve_forever()
