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

// LED RGB
const int redPin = 5;    
const int greenPin = 6;  
const int bluePin = 7;

// Variáveis
long duration;
int distance;
int angle = 0;
int increment = 5;
bool movingForward = true;
bool wifiConnected = false;

// Configurações WiFi - ALTERE AQUI!
const char* SSID = "iPhone de Owen";
const char* PASSWORD = "1234567890";
const char* HOST = "https://tam-two.vercel.app/";

void setup() {
  Serial.begin(9600);
  esp8266.begin(9600);
  
  // Configurar servo
  radarServo.attach(servoPin);
  
  // Configurar sensor
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  
  // Configurar LED RGB
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
  
  // LED azul (inicializando)
  setColor(0, 0, 255);
  
  // Conectar WiFi
  delay(2000);
  connectWiFi();
  
  Serial.println("Sistema Radar DIY iniciado!");
}

void setColor(int red, int green, int blue) {
  analogWrite(redPin, red);
  analogWrite(greenPin, green); 
  analogWrite(bluePin, blue);
}

void connectWiFi() {
  Serial.println("Conectando ao WiFi...");
  setColor(255, 255, 0); // Amarelo (conectando)
  
  sendCommand("AT+RST", 2000);
  delay(2000);
  
  sendCommand("AT+CWMODE=1", 2000);
  
  String connectCmd = "AT+CWJAP=\"" + String(SSID) + "\",\"" + String(PASSWORD) + "\"";
  String response = sendCommand(connectCmd, 10000);
  
  if (response.indexOf("OK") != -1) {
    wifiConnected = true;
    setColor(0, 255, 0); // Verde (conectado)
    Serial.println("✅ WiFi conectado!");
    
    sendCommand("AT+CIFSR", 2000);
    sendCommand("AT+CIPMUX=0", 2000);
  } else {
    wifiConnected = false;
    setColor(255, 0, 0); // Vermelho (erro)
    Serial.println("❌ Falha na conexão WiFi");
  }
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
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  duration = pulseIn(echoPin, HIGH);
  distance = duration * 0.034 / 2;
}

void updateLED(int distance) {
  // 2 cores: Vermelho/Verde
  if (distance < 30 && distance > 2) {
    setColor(255, 0, 0); // Vermelho - Objeto detectado
  } else {
    setColor(0, 255, 0); // Verde - Área livre
  }
}

void sendToAPI(int angle, int distance) {
  if (distance > 2 && distance < 400 && wifiConnected) {
    
    String jsonData = "{\"angle\":" + String(angle) + 
                     ",\"distance\":" + String(distance) + 
                     ",\"timestamp\":" + String(millis()) + "}";
    
    String httpCmd = "AT+CIPSTART=\"TCP\",\"" + String(HOST) + "\",80";
    if (sendCommand(httpCmd, 3000).indexOf("OK") != -1) {
      
      String postRequest = "POST /api/radar/data HTTP/1.1\r\n";
      postRequest += "Host: " + String(HOST) + "\r\n";
      postRequest += "Content-Type: application/json\r\n";
      postRequest += "Content-Length: " + String(jsonData.length()) + "\r\n";
      postRequest += "Connection: close\r\n\r\n";
      postRequest += jsonData;
      
      String sendCmd = "AT+CIPSEND=" + String(postRequest.length());
      if (sendCommand(sendCmd, 2000).indexOf(">") != -1) {
        sendCommand(postRequest, 2000);
        Serial.println("✅ Dados enviados!");
      }
      
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
  
  // Atualizar LED
  updateLED(distance);
  
  // Enviar dados
  sendToAPI(angle, distance);
  
  // Serial monitor
  Serial.print("Ângulo: ");
  Serial.print(angle);
  Serial.print("° - Distância: ");
  Serial.print(distance);
  Serial.println(" cm");
  
  // Atualizar ângulo
  if (movingForward) {
    angle += increment;
    if (angle >= 180) movingForward = false;
  } else {
    angle -= increment;
    if (angle <= 0) movingForward = true;
  }
  
  delay(300);
}
