from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os

CHAVE = b'B8ZSprojetoUTFPR'  # 16 bytes = AES-128

def criptografar(mensagem: str) -> bytes:
    cipher = AES.new(CHAVE, AES.MODE_CBC)
    iv = cipher.iv
    msg_bytes = mensagem.encode('latin-1')
    msg_padded = pad(msg_bytes, AES.block_size)
    msg_criptografada = cipher.encrypt(msg_padded)
    return iv + msg_criptografada

def descriptografar(dados: bytes) -> str:
    iv = dados[:16]
    msg_criptografada = dados[16:]
    cipher = AES.new(CHAVE, AES.MODE_CBC, iv=iv)
    msg_padded = cipher.decrypt(msg_criptografada)
    msg_bytes = unpad(msg_padded, AES.block_size)
    return msg_bytes.decode('latin-1')

def bytes_para_binario(dados: bytes) -> str:
    return ''.join(format(byte, '08b') for byte in dados)

def binario_para_bytes(binario: str) -> bytes:
    grupos = [binario[i:i+8] for i in range(0, len(binario), 8)]
    return bytes(int(g, 2) for g in grupos)

def texto_para_binario(texto: str) -> str:
    return ''.join(format(ord(c), '08b') for c in texto)