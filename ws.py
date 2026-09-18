import socket
import gc
import json
from binascii import b2a_base64
from ws_connection import ClientClosedError
from ws_server import WebSocketServer, WebSocketClient
from debug import dprint

_TYPE_ANALOG = const(0)
_TYPE_SERIAL = const(3)
_TYPE_LOAD = const(4)
_TYPE_TEMP = const(5)


class RTUWebSocketClient(WebSocketClient):
    def __init__(self, conn):
        super().__init__(conn)

    def process(self):
        try:
            message = self.connection.read()
            
            # No data currently available.
            if message is None:
                return
            
            # Depending on the WebSocket implementation,
            # EOF may be returned as empty bytes.
            if message == b"" or message == "" or message == "disconnect":
                print("WebSocket client disconnected")
                self.connection.close()
                return

            # Process normal messages here.
            if isinstance(message, bytes):
                message = message.decode("utf-8")

            print("WebSocket message:", message)

        except ClientClosedError:
            print("WebSocket close frame received")
            self.connection.close()

        except OSError as error:
            print("WebSocket socket closed:", error)
            self.connection.close()
    
    def close(self):
        self.connection.close()
        self.connection = None

class RTUWebSocketServer(WebSocketServer):
    def __init__(self, ip):
        self._ip = ip
        super().__init__(None, 2)
        
    def _setup_conn(self, port, accept_handler):
        self._listen_s = socket.socket()
        self._listen_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listen_s.setblocking(False)

        ai = socket.getaddrinfo("0.0.0.0", port)
        addr = ai[0][4]

        self._listen_s.bind(addr)
        self._listen_s.listen(1)
        if accept_handler:
            self._listen_s.setsockopt(socket.SOL_SOCKET, 20, accept_handler)
        print("WebSocket started on ws://%s:%d" % (self._ip, port))
        
    
    def _broadcast_message(self, msg):
        for c in self._clients[:]:
            try:
                c.connection.write(json.dumps(msg))
            except (ClientClosedError ,OSError):
                c.close()
                self._clients.remove(c)
        
    def _make_client(self, conn):
        return RTUWebSocketClient(conn)

    def broadcast(self, device):   
        self._send_serial(device)
        self._send_loadcell(device)
        self._send_thermo_temp(device)
        
    def _send_serial(self, device):
        if device.serial is None:
            return
        serial_data = device.recv_uart_message()
        msg = {"type": _TYPE_SERIAL, "message": serial_data}
        self._broadcast_message(msg)
        
    def _send_loadcell(self, device):
        if not device.loadcell:
            return
        
        weight = device.get_loadcell_in_kg()
#         dprint("Weight:", weight)
        msg = {"type": _TYPE_LOAD, "weight": weight}
        self._broadcast_message(msg)
        
    def _send_thermo_temp(self, device):
        if not device.temp:
            return

        # Poll only: device.py associates each completed conversion with the
        # channel which produced it and starts the next one without waiting.
        temp_list = device.poll_temperatures()
        if temp_list is None:
            return
        msg = {"type": _TYPE_TEMP, "temperature": temp_list}
        self._broadcast_message(msg)

    def _serve_page(self, sock):
        # Ignore everything in 1
        sock.close()
        

