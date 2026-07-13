import threading
import struct
import serial

BAUDRATE = 115200
TIMEOUT = 10

def niveis_para_bytes(niveis: list[int]) -> bytes:
    """ Comprime 4 níveis B8ZS (-1, 0, 1) em 1 único byte para otimizar ESP-NOW """
    mapped = [n + 1 for n in niveis] # Mapeia -1, 0, 1 para 0, 1, 2
    packed = bytearray()
    
    for i in range(0, len(mapped), 4):
        chunk = mapped[i:i+4]
        while len(chunk) < 4:
            chunk.append(1) # Preenche com zeros (mapeado para 1)
            
        b = (chunk[0] << 6) | (chunk[1] << 4) | (chunk[2] << 2) | chunk[3]
        packed.append(b)
        
    return struct.pack(">H", len(niveis)) + bytes(packed)

def bytes_para_niveis(dados: bytes) -> list[int]:
    """ Descomprime o byte empacotado de volta para os níveis B8ZS """
    if len(dados) < 2: return []
    num_levels = struct.unpack(">H", dados[:2])[0]
    packed = dados[2:]
    
    niveis = []
    for b in packed:
        niveis.append(((b >> 6) & 0x03) - 1)
        niveis.append(((b >> 4) & 0x03) - 1)
        niveis.append(((b >> 2) & 0x03) - 1)
        niveis.append((b & 0x03) - 1)
        
    return niveis[:num_levels]

def _enviar_frame(conn: serial.Serial, id_dest: int, dados: bytes) -> None:
    tamanho = struct.pack(">I", len(dados))
    conn.write(bytes([id_dest]) + tamanho + dados)
    conn.flush()

def _receber_frame(conn: serial.Serial) -> tuple[int, bytes]:
    cabecalho = b""
    while len(cabecalho) < 5: # 1 byte ID_Origem + 4 bytes Tamanho
        chunk = conn.read(5 - len(cabecalho))
        if not chunk:
            return -1, b""
        cabecalho += chunk

    id_origem = cabecalho[0]
    tamanho = struct.unpack(">I", cabecalho[1:5])[0]

    corpo = b""
    while len(corpo) < tamanho:
        chunk = conn.read(tamanho - len(corpo))
        if not chunk:
            break
        corpo += chunk

    return id_origem, corpo

class Servidor:
    def __init__(self, porta_com: str, callback=None):
        self.porta_com = porta_com
        self.callback = callback
        self._parar = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self.serial_conn = None

    def iniciar(self):
        self._parar.clear()
        self._thread.start()

    def parar(self):
        self._parar.set()
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

    def _loop(self):
        try:
            self.serial_conn = serial.Serial(self.porta_com, BAUDRATE, timeout=1.0)
        except Exception as e:
            if self.callback:
                self.callback(-1, None, self.porta_com, str(e))
            return

        while not self._parar.is_set():
            try:
                if self.serial_conn.in_waiting >= 5:
                    id_origem, dados = _receber_frame(self.serial_conn)
                    if dados:
                        niveis = bytes_para_niveis(dados)
                        if self.callback:
                            self.callback(id_origem, niveis, self.porta_com)
            except Exception as e:
                if self.callback:
                    self.callback(-1, None, self.porta_com, str(e))
                break

        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

def enviar_niveis(porta_com: str, id_dest: int, niveis: list[int]) -> None:
    with serial.Serial(porta_com, BAUDRATE, timeout=TIMEOUT) as conn:
        _enviar_frame(conn, id_dest, niveis_para_bytes(niveis))
