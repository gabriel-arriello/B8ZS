#include <esp_now.h>
#include <WiFi.h>

// =======================================================
// ESCOLHA O PAPEL DESTA PLACA ANTES DE GRAVAR:
// 0 = Master | 1 = Slave 1 | 2 = Slave 2
const int DEVICE_ROLE = 0; 
// =======================================================

uint8_t macMaster[] = {0xE0, 0x8C, 0xFE, 0xE6, 0x1C, 0x28};
uint8_t macSlave1[] = {0x70, 0x4B, 0xCA, 0x6F, 0x35, 0xB0};
uint8_t macSlave2[] = {0xE0, 0x8C, 0xFE, 0xE5, 0x83, 0x04};

esp_now_peer_info_t peerInfo;

// O callback OnDataSent foi removido pois não é utilizado e causava conflito de versão.

void OnDataRecv(const esp_now_recv_info *info, const uint8_t *incomingData, int len) {
  // Descobre quem enviou a mensagem analisando o MAC de origem
  uint8_t sender_id = 0;
  if (memcmp(info->src_addr, macSlave1, 6) == 0) sender_id = 1;
  else if (memcmp(info->src_addr, macSlave2, 6) == 0) sender_id = 2;
  else if (memcmp(info->src_addr, macMaster, 6) == 0) sender_id = 0;

  // Escreve para o Python: [ID do Remetente (1 byte)] + [Dados recebidos]
  Serial.write(sender_id);
  Serial.write(incomingData, len);
}

void add_peer(uint8_t* mac) {
  memcpy(peerInfo.peer_addr, mac, 6);
  peerInfo.channel = 0;  
  peerInfo.encrypt = false;
  esp_now_add_peer(&peerInfo);
}

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);

  if (esp_now_init() != ESP_OK) return;

  // Registra apenas o callback de recepção
  esp_now_register_recv_cb(OnDataRecv);

  // O Master conhece os Slaves. Os Slaves conhecem apenas o Master.
  if (DEVICE_ROLE == 0) {
    add_peer(macSlave1);
    add_peer(macSlave2);
  } else {
    add_peer(macMaster);
  }

  Serial.setTimeout(10); 
}

void loop() {
  // Apenas Slaves enviam dados para o ar. O Master apenas escuta.
  if (DEVICE_ROLE != 0 && Serial.available() >= 5) {
    
    // O Python manda o target_id como 0, lemos para remover do buffer
    uint8_t target_id = Serial.read(); 
    
    uint8_t len_buf[4];
    Serial.readBytes(len_buf, 4);
    uint32_t payload_len = (len_buf[0] << 24) | (len_buf[1] << 16) | (len_buf[2] << 8) | len_buf[3];

    // Limite de segurança para o pacote do ESP-NOW
    if (payload_len > 0 && payload_len <= 240) {
      uint8_t payload[240];
      int bytes_lidos = Serial.readBytes(payload, payload_len);
      
      if (bytes_lidos == payload_len) {
        uint8_t esp_buffer[244];
        memcpy(esp_buffer, len_buf, 4);
        memcpy(esp_buffer + 4, payload, payload_len);

        // Envio forçado: independente do que chegou do Python, o Slave manda para o Master
        esp_now_send(macMaster, esp_buffer, payload_len + 4);
      }
    }
  }
}