#include <SoftwareSerial.h>
#include <Servo.h>

// Configurações do ESP8266
SoftwareSerial esp8266(2, 3); // RX, TX

// Servo Motor
Servo radarServo;
int servoPin = 9;

// Sensor Ultrassônico
const int trigPin = 10;
const int echoPin = 11;

// Variáveis
long duration;
int distance;
int angle = 0;
int increment = 5;
bool movingForward = true;

// Configurações WiFi 
const char* SSID = "iPhone de Owen";
const char* PASSWORD = "1234567890";
const char* HOST = "https://vercel.com/owens-projects-0be75bfe/tam"; 

void setup() {
  Serial.begin(9600);
  esp8266.begin(9600);
  
  // Configurar servo
  radarServo.attach(servoPin);
  
  // Configurar sensor ultrassônico
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  
  // Inicializar WiFi
  delay(2000);
  connectWiFi();
  
  Serial.println("Sistema Radar DIY iniciado!");
}

void connectWiFi() {
  Serial.println("Conectando ao WiFi...");
  
  // Reset do ESP
  sendCommand("AT+RST", 2000);
  delay(2000);
  
  // Configurar como station
  sendCommand("AT+CWMODE=1", 2000);
  
  // Conectar à rede WiFi
  String connectCmd = "AT+CWJAP=\"" + String(SSID) + "\",\"" + String(PASSWORD) + "\"";
  sendCommand(connectCmd, 10000);
  
  // Verificar IP
  sendCommand("AT+CIFSR", 2000);
  
  // Configurar conexão única
  sendCommand("AT+CIPMUX=0", 2000);
}

String sendCommand(String command, int delayTime) {
  Serial.println("Comando: " + command);
  esp8266.println(command);
  delay(delayTime);
  
  String response = "";
  while(esp8266.available()) {
    response += esp8266.readString();
  }
  
  Serial.println("Resposta: " + response);
  return response;
}

void measureDistance() {
  // Limpar o trigPin
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  
  // Setar trigPin HIGH por 10 microsegundos
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  // Ler echoPin
  duration = pulseIn(echoPin, HIGH);
  
  // Calcular distância
  distance = duration * 0.034 / 2;
}

void sendToAPI(int angle, int distance) {
  if (distance > 2 && distance < 400) { // Filtro para valores válidos
    
    // Criar JSON com dados
    String jsonData = "{\"angle\":" + String(angle) + 
                     ",\"distance\":" + String(distance) + 
                     ",\"timestamp\":" + String(millis()) + "}";
    
    // Preparar comando HTTP
    String httpCmd = "AT+CIPSTART=\"TCP\",\"" + String(HOST) + "\",80";
    if (sendCommand(httpCmd, 3000).indexOf("OK") != -1) {
      
      String postRequest = "POST /api/radar/data HTTP/1.1\r\n";
      postRequest += "Host: " + String(HOST) + "\r\n";
      postRequest += "Content-Type: application/json\r\n";
      postRequest += "Content-Length: " + String(jsonData.length()) + "\r\n";
      postRequest += "Connection: close\r\n\r\n";
      postRequest += jsonData;
      
      // Enviar dados
      String sendCmd = "AT+CIPSEND=" + String(postRequest.length());
      if (sendCommand(sendCmd, 2000).indexOf(">") != -1) {
        sendCommand(postRequest, 2000);
      }
      
      // Fechar conexão
      sendCommand("AT+CIPCLOSE", 1000);
    }
  }
}

void loop() {
  // Mover servo
  radarServo.write(angle);
  delay(50);
  
  // Medir distância
  measureDistance();
  
  // Enviar dados para API
  sendToAPI(angle, distance);
  
  // Exibir no monitor serial
  Serial.print("Ângulo: ");
  Serial.print(angle);
  Serial.print("° - Distância: ");
  Serial.print(distance);
  Serial.println(" cm");
  
  // Atualizar ângulo
  if (movingForward) {
    angle += increment;
    if (angle >= 180) {
      movingForward = false;
    }
  } else {
    angle -= increment;
    if (angle <= 0) {
      movingForward = true;
    }
  }
  
  delay(300); // Ajuste este delay para velocidade do radar
}
