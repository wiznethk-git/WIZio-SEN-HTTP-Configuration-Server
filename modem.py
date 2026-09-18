import time
import gc
from machine import Pin, UART
from debug import dprint

MODEM_UART_MAX_BUF = const(4096)

# Modem Defaults
_DEFAULT_BAUDRATE = const(115200)
_DEFAULT_BITS = (8)
_DEFAULT_PARIY = None
_DEFAULT_STOP = const(1)

# Modem mode
_MODEM_UNKNOWN = 0
_MODEM_BOOTING = 1
_MODEM_TRANSPARENT = 2
_MODEM_COMMAND = 3

# Modem transparent WORK mode
_WKMOD_OFF  = 0
_WKMOD_NET  = 1
_WKMOD_HTTP = 2
_WKMOD_MQTT = 3




class ModemManager:
    # Restart Commands
    RESTART_COMMANDS = (
        b'AT+S\r\n',
        b'AT+CLEAR\r\n',
        b'AT+Z\r\n'
    )
    
    def __init__(
        self,
        baudrate =  _DEFAULT_BAUDRATE,
        bits = _DEFAULT_BITS,
        parity = _DEFAULT_PARIY,
        stop = _DEFAULT_STOP
    ):
        # Defaults to Web Mode
        self.modem = None
        self.mode = _MODEM_UNKNOWN
        self.wkmod = _WKMOD_OFF
        self.power_pin = Pin('PB2', Pin.OUT)
        
        # Store state (Can be changed by modem)
        self.baudrate = baudrate
        self.bits = bits
        self.parity = parity
        self.stop = stop
        
        # Actual bus
        self.modem = UART(4, baudrate)
        self.modem.init(baudrate, bits, parity, stop, rxbuf = 8192, timeout = 500)
        
        # Changes
        self.uart_configs = (baudrate, bits, parity, stop)
        self.uart_flag = False
        
        
        self.flags = (self.uart_flag, )
        self.power_on()
        self._apply_restart_state()
#         self._apply_restart_wkmod()
   
    def power_on(self):
        self.power_pin.value(1)
        self.mode = _MODEM_TRANSPARENT # Transparent by default.
        
    def power_off(self):
        self.power_pin.value(0)
        self.mode = _MODEM_UNKNOWN
        
    def write(self, command):
        if not self.modem:
            return False
        if not isinstance(command, bytes):
            dprint("DTU write requires command to be in bytes")
            return False    
        command = command.replace(b'\n', b'\r\n')
        dprint(f'Command in device: {command}.')
        try:
            if self.mode == _MODEM_COMMAND:
                self.modem.write(command)
                if (command in self.RESTART_COMMANDS):  
                    self.mode = _MODEM_TRANSPARENT
            else:
                # Alter mode commands
                if (command == b'+++'):
                    # Enters Command Mode
                    time.sleep_ms(500)                    
                    self.modem.write(command)
                    time.sleep_ms(500)
                    
                    # Set modes
                    self.mode = _MODEM_COMMAND
                    self.wkmod = _WKMOD_OFF
                else:
                    self.modem.write(command)
            return True
        except:
            dprint("DTU write failed.")
            return False
        
    def read(self):
        if (self.mode == _MODEM_COMMAND):
            return self._read_uart()
        elif (self.mode == _MODEM_TRANSPARENT):
            return self._read_sock()
    
    def _read_uart(self):
        """
        Read up until max buffer for UART.
        """
        if not self.modem:
            return None
        
        # Return if no data in 4G bus.
        num_bytes_in_bus = min(self.modem.any(), MODEM_UART_MAX_BUF)
        if not num_bytes_in_bus:
            return None
        
        read_size = num_bytes_in_bus
        print("Read Size: ", read_size)
        buf = bytearray(read_size)
        mv = memoryview(buf)
        pos = 0
        
        while self.modem.any():
            num_bytes = self.modem.readinto(mv[pos:])
            if num_bytes == 0:
                break
            pos += num_bytes
            
        dprint(f"Pos: {pos} | Max: {read_size}")
        return buf
    
    def _read_sock(self):
        """
        Requires continous reading for sock.
        """
        if not self.modem:
            return None  

        if not self.modem.any():
            return
        # Return if no data in 4G bus.
        buf = bytearray(2048)
        mv = memoryview(buf)
        pos = 0
        peak_before_sleep = 0
        peak_after_sleep = 0
        while pos < len(buf):
            n = self.modem.readinto(mv[pos:])

            if not n:
                if not self.modem.any():
                    break
                continue

            pos += n

            queued = self.modem.any()
            peak_before_sleep = max(peak_before_sleep, queued)

            time.sleep_ms(1)

            queued = self.modem.any()
            peak_after_sleep = max(peak_after_sleep, queued)

        print("received:", pos)
        print("peak before sleep:", peak_before_sleep)
        print("peak after sleep:", peak_after_sleep)
        return buf[:pos + 1]
    
    def process_rx_data(self, buf):
        """
        Check received modem data and
        apply additional support to different commands/msg.
        
        Args:
            ws_data (bytes): UART Bytes received from Modem
        Returns:
            None
        """
        
        if self.mode == _MODEM_COMMAND:
            self._handle_command(buf)
        elif self.mode == _MODEM_TRANSPARENT:
            self._handle_transparent(buf)
        else:
            return
        
        

    # ============ Command ================
    def _handle_command(self, buf):
        # Only treat AT responses
        if not buf.startswith(b'AT'):
            return
        pass
#         lines = [line.strip() for line in buf.splitlines() if line is not b'']
#         cmd, status = buf.splitlines()[0]
#         
#         # Only do stuff when OK 
#         if status != b'OK':
#             return
#         
#         if cmd.startswith(b'AT+UART='):
#             return self._append_uart(cmd)
#         
#         # AT + Clear back to default
#         elif cmd.startswith(b'AT+CLEAR'):
#             return self._reset_modem_params(cmd)
    
    
    def _append_uart(self, cmd):
        ...
    
    # ============ Transparent ===============    
    def _handle_transparent(self, buf):
#         dprint('Handle transparent:', buf)
        status = buf.strip(b'\r\n')
        self._assign_wkmod(status)
    
    def _assign_wkmod(self, status):
        if status in (b"FS@TCP CONNECTED:1", b"NET"):
            self.wkmod = _WKMOD_NET
        
        elif status in (b"FS@HTTP OK:1", b"HTTP"):
            self.wkmod = _WKMOD_HTTP
        
        elif status in (b"FS@UDP OK:1", b"NET"):
            self.wkmod = _WKMOD_NET
        
        elif status in (b"FS@MQTT CONNECTED: 1", b"MQTT"):
            self.wkmod = _WKMOD_MQTT
        
        
    
    def _reset_modem_params(self, cmd):
        ...
        
    def _apply_restart_state(self):
        try:
            print("\n==== Modem initialize ====")
            # Clean data inside modem from previous iterations
            print('Cleaning old modem data')
            while True:
                buf = self.modem.read(1024)
                if buf is None:
                    break
                    
            time.sleep_ms(500)
            self.modem.write(b'+++')
            time.sleep_ms(500)
           
            g = self.modem.read(128)
        
            # Restart
            self.modem.write(b'AT+Z\r\n')

            restart = self.modem.read(128)
            
            fs_t1 = time.ticks_ms()
            fs = None
            while True:
                fs_t2 = time.ticks_ms()
                if time.ticks_diff(fs_t2, fs_t1) > 3000:
                    return
                fs = self.modem.read(128)
                if fs is not None:
                    break
      
            print('Setting WKMOD')
            wkmod_t1 = time.ticks_ms()
            wkmod = None
            while True:
                wkmod_t2 = time.ticks_ms()
                if time.ticks_diff(wkmod_t2, wkmod_t1) > 3000:
                    return
                wkmod = self.modem.read(128)
                if wkmod is not None:
                    break
 
            self._assign_wkmod(wkmod.strip(b'\r\n'))
            
        except Exception as e:
            raise(e)
            dprint("Failed Modem. Check UARTs")

        