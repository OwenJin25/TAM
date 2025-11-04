# 🚨 Radar DIY - Sistema de Monitoramento

Sistema completo de radar DIY usando Arduino, ESP8266, PostgreSQL e Flask.

## 📋 Componentes Necessários

### Hardware:
- Arduino Uno/Nano
- Módulo WiFi ESP8266 (ESP-01S)
- Servo Motor SG90
- Sensor Ultrassônico HC-SR04
- Protoboard
- Fios jumper
- Fonte de alimentação 5V

### Software:
- Arduino IDE
- Python 3.8+
- PostgreSQL
- Conta Vercel (deploy)

## 🔌 Esquema de Ligação

### Arduino + ESP8266:
ESP8266 Arduino
VCC → 3.3V
GND → GND
TX → Pino 2 (RX)
RX → Pino 3 (TX)
CH_PD → 3.3V

### Servo SG90:
Servo Arduino
Vermelho → 5V
Marrom → GND
Laranja → Pino 9

### Sensor HC-SR04:
Sensor Arduino
VCC → 5V
GND → GND
Trig → Pino 10
Echo → Pino 11

### LED RGB (Anodo Comum):
LED RGB Arduino
Vermelho → Pino 5
Verde → Pino 6
Azul → Pino 7
Ânodo → 5V

## ⚙️ Configuração

### 1. Arduino:
- Abra `arduino/radar_diy.ino` no Arduino IDE
- Altere `SSID` e `PASSWORD` para suas credenciais WiFi
- Altere `HOST` para a URL do seu app Vercel após deploy
- Faça upload para o Arduino

### 2. Configuração WiFi no Arduino:
```cpp
// ALTERE ESTAS LINHAS NO CÓDIGO:
const char* SSID = "NOME_REDE";
const char* PASSWORD = "PASSWORD_REDE";
const char* HOST = "LINK_VERCEL";
