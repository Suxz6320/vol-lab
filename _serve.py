import http.server, socketserver, threading, webbrowser, os
PORT = 8765
ROOT = r"c:\Users\33685\Desktop\val\volleylab_app\assets\www"
os.chdir(ROOT)
Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    url = f"http://127.0.0.1:{PORT}/skill-spike.html"
    print(f"Serving {ROOT}")
    print(f"URL: {url}")
    webbrowser.open(url)
    httpd.serve_forever()
