from http.server import BaseHTTPRequestHandler, HTTPServer

# This class handles incoming requests from the ESP32.
class SensorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("Received:", self.path)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

# Start the server on port 8000.
server = HTTPServer(("0.0.0.0", 8000), SensorHandler)
print("Server is running on port 8000...")
server.serve_forever()
