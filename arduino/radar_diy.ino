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
unsigned long lastDataSent = 0;

// Configurações WiFi - ALTERE AQUI!
const char* SSID = "iPhone de Owen";
const char* PASSWORD = "1234567890";
const char* HOST = "tam-owens-projects-0be75bfe.vercel.app";

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
  delay(1000);
  
  // Conectar WiFi
  Serial.println("Iniciando Sistema Radar DIY...");
  connectWiFi();
}

void setColor(int red, int green, int blue) {
  analogWrite(redPin, red);
  analogWrite(greenPin, green); 
  analogWrite(bluePin, blue);
}

void connectWiFi() {
  Serial.println("Conectando ao WiFi...");
  setColor(255, 255, 0); // Amarelo (conectando)
  
  // Aguardar ESP8266 inicializar
  delay(3000);
  
  // Testar comunicação
  sendCommand("AT", 2000);
  
  // Configurar como station
  sendCommand("AT+CWMODE=1", 2000);
  
  // Conectar à rede WiFi
  String connectCmd = "AT+CWJAP=\"" + String(SSID) + "\",\"" + String(PASSWORD) + "\"";
  String response = sendCommand(connectCmd, 15000);
  
  if (response.indexOf("OK") != -1 || response.indexOf("GOT IP") != -1) {
    wifiConnected = true;
    setColor(0, 255, 0); // Verde (conectado)
    Serial.println("✅ WiFi conectado!");
    
    // Verificar IP
    sendCommand("AT+CIFSR", 2000);
    
    // Configurar conexão única
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
  
  // Mostrar apenas parte da resposta para não poluir o serial
  if (response.length() > 200) {
    Serial.println("Resposta: [MUITO LONGA]");
  } else {
    Serial.println("Resposta: " + response);
  }
  
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
  
  // Calcular distância em cm
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

void indicateActivity() {
  // Piscar branco rapidamente para indicar envio
  setColor(255, 255, 255);
  delay(50);
  // A cor normal será restaurada na próxima leitura
}

void sendToAPI(int angle, int distance) {
  if (distance > 2 && distance < 400) { // Filtro para valores válidos
    
    if (!wifiConnected) {
      // Tentar reconectar se WiFi caiu
      connectWiFi();
      if (!wifiConnected) {
        return;
      }
    }
    
    // Criar JSON com dados
    String jsonData = "{\"angle\":" + String(angle) + 
                     ",\"distance\":" + String(distance) + 
                     ",\"timestamp\":" + String(millis()) + "}";
    
    // Preparar comando HTTP
    String httpCmd = "AT+CIPSTART=\"TCP\",\"" + String(HOST) + "\",80";
    String response = sendCommand(httpCmd, 5000);
    
    if (response.indexOf("OK") != -1 || response.indexOf("CONNECT") != -1) {
      
      String postRequest = "POST /api/radar/data HTTP/1.1\r\n";
      postRequest += "Host: " + String(HOST) + "\r\n";
      postRequest += "Content-Type: application/json\r\n";
      postRequest += "Content-Length: " + String(jsonData.length()) + "\r\n";
      postRequest += "Connection: close\r\n\r\n";
      postRequest += jsonData;
      
      // Enviar dados
      String sendCmd = "AT+CIPSEND=" + String(postRequest.length());
      response = sendCommand(sendCmd, 3000);
      
      if (response.indexOf(">") != -1 || response.indexOf("SEND") != -1) {
        sendCommand(postRequest, 3000);
        lastDataSent = millis();
        indicateActivity(); // Piscar LED para indicar envio
        Serial.println("✅ Dados enviados para API!");
      } else {
        Serial.println("❌ Falha no envio");
      }
      
      // Fechar conexão
      sendCommand("AT+CIPCLOSE", 1000);
    } else {
      Serial.println("❌ Falha na conexão com API");
      wifiConnected = false;
      setColor(255, 0, 0); // Vermelho (erro)
    }
  }
}

void checkStatus() {
  // Verificar se há muito tempo sem enviar dados
  if (wifiConnected && (millis() - lastDataSent > 30000)) {
    // Mais de 30 segundos sem enviar - possivel problema
    setColor(255, 165, 0); // Laranja (alerta)
  }
}

void loop() {
  // Mover servo
  radarServo.write(angle);
  delay(50);
  
  // Medir distância
  measureDistance();
  
  // Indicar distância no LED RGB
  updateLED(distance);
  
  // Enviar dados para API
  sendToAPI(angle, distance);
  
  // Verificar status do sistema
  checkStatus();
  
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
  
  delay(500); // Ajuste este delay para velocidade do radar
}
