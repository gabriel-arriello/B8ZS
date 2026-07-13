# B8ZS Line Coding System

Sistema de transmissão digital que implementa a codificação de linha B8ZS (Bipolar with 8-Zero Substitution) com criptografia AES, utilizando um ESP32 como camada física de transmissão e uma interface gráfica em Python para controle e visualização.

## Sobre o projeto

O sistema permite que uma mensagem seja criptografada, codificada em B8ZS e transmitida através de um ESP32, simulando os princípios de transmissão digital em banda base. A interface gráfica (frontend) é responsável por enviar a mensagem, acompanhar o processo de codificação/decodificação e exibir o sinal resultante.

## Estrutura do projeto

```
.
├── backend
│   ├── b8zs.py            # Implementação da codificação/decodificação B8ZS
│   ├── crypto.py          # Criptografia e descriptografia AES da mensagem
│   └── rede.py            # Comunicação com o ESP32 (envio/recebimento de dados)
├── firmware_b8zs
│   └── firmware_b8zs.ino  # Firmware do ESP32 responsável pela transmissão do sinal
├── frontend
│   └── app.py             # Interface gráfica (Tkinter) para controle do sistema
├── README.md
└── requirements.txt
```

## Tecnologias utilizadas

- **Backend:** Python (codificação B8ZS, criptografia AES, comunicação serial/rede)
- **Firmware:** C++ (ESP32, Arduino IDE)
- **Frontend:** Python (Tkinter)
- **Criptografia:** AES

## Como executar

### Requisitos

```bash
pip install -r requirements.txt
```

### Firmware (ESP32)

1. Abra `firmware_b8zs/firmware_b8zs.ino` na Arduino IDE.
2. Selecione a placa ESP32 e a porta correspondente.
3. Faça o upload do firmware para o dispositivo.

### Backend

```bash
cd backend
python rede.py
```

### Frontend

```bash
cd frontend
python app.py
```

## Fluxo de funcionamento

1. O usuário digita a mensagem na interface gráfica (`app.py`).
2. A mensagem é criptografada com AES (`crypto.py`).
3. Os dados criptografados são codificados usando B8ZS (`b8zs.py`).
4. O sinal codificado é enviado ao ESP32 (`rede.py`), que realiza a transmissão física.
5. O processo inverso ocorre na recepção: decodificação B8ZS e descriptografia AES para recuperar a mensagem original.

## Equipe

- [Adicionar nomes dos integrantes]

## Disciplina

Projeto desenvolvido para a disciplina de Transmissão Digital — UTFPR.

## Licença

[Definir licença, ex: MIT]
