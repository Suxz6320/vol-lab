import http.server, socketserver, os
PORT = 8765
ROOT = r"c:\Users\33685\Desktop\val\volleylab_app\assets\www"
os.chdir(ROOT)
Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    print(f"Serving {ROOT} on port {PORT}")
    httpd.serve_forever()
