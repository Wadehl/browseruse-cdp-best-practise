"""
简单的 HTTP API 服务器

用于测试网络数据捕获功能
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import os


class APIHandler(BaseHTTPRequestHandler):
    """API 请求处理器"""

    def do_GET(self):
        """处理 GET 请求"""
        # 路由处理
        if self.path == '/test_page.html' or self.path == '/':
            # 提供测试页面
            html_file = os.path.join(os.path.dirname(__file__), 'test_page.html')
            if os.path.exists(html_file):
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                with open(html_file, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'404 - test_page.html not found')

        elif self.path == '/api/user/data':
            # 用户数据 API
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

            data = {
                "username": "李四",
                "points": 2500,
                "level": 8,
                "lastLogin": datetime.now().isoformat(),
                "vip": True,
                "achievements": ["新手上路", "活跃用户", "贡献者"]
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

        elif self.path == '/api/product/list':
            # 产品列表 API
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

            data = {
                "products": [
                    {"id": 1, "name": "商品A", "price": 99.9},
                    {"id": 2, "name": "商品B", "price": 199.9},
                    {"id": 3, "name": "商品C", "price": 299.9}
                ],
                "total": 3
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

        else:
            # 404
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            data = {"error": "Not Found", "path": self.path}
            self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        """处理 OPTIONS 请求（CORS 预检）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[API] {self.address_string()} - {format % args}")


def run_server(port=8890):
    """运行 API 服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, APIHandler)

    print(f"🚀 API 服务器启动在 http://localhost:{port}")
    print(f"📄 测试页面: http://localhost:{port}/test_page.html")
    print(f"📡 API 端点:")
    print(f"   - http://localhost:{port}/api/user/data")
    print(f"   - http://localhost:{port}/api/product/list")
    print("\n按 Ctrl+C 停止服务器\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ 服务器已停止")
        httpd.shutdown()


if __name__ == '__main__':
    run_server()