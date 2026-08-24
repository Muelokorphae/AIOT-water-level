#include <AccelStepper.h>

// ULN2003 Driver pin mapping for 28BYJ-48 in HALF-STEP mode (pins 8, 10, 9, 11)
#define HALFSTEP 8
#define motorPin1 8  // IN1
#define motorPin2 10 // IN2
#define motorPin3 9  // IN3
#define motorPin4 11 // IN4

AccelStepper waterStepper(HALFSTEP, motorPin1, motorPin2, motorPin3, motorPin4);

const int WATER_SENSOR_PIN = A0;
const int LED_PIN          = 7;

unsigned long lastReportTime = 0;
unsigned long startTriggerTime = 0; // Tracks when '1' was received
bool isRunning = false;
bool pendingStart = false;           // Tracks if waiting during the 3-second delay

// --- SPEED ADJUSTMENT PARAMETERS ---
const float TARGET_SPEED = 1000.0; // Speed target (steps/sec)
const float ACCELERATION = 500.0;  // Smooth acceleration rate to prevent stall

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // Configure high-speed acceleration parameters
  waterStepper.setMaxSpeed(TARGET_SPEED);
  waterStepper.setAcceleration(ACCELERATION);
}

void loop() {
  // 1. Read water sensor and report data every 3 seconds (3000 ms)
  int rawValue = analogRead(WATER_SENSOR_PIN);
  int waterPercent = map(rawValue, 0, 700, 0, 100); 
  waterPercent = constrain(waterPercent, 0, 100);

  if (millis() - lastReportTime >= 3000) {
    Serial.print("WATER_LEVEL:");
    Serial.println(waterPercent);
    lastReportTime = millis();
  }

  // 2. Read commands from Python ('1' = Run, '0' = Stop)
  while (Serial.available() > 0) {
    char cmd = Serial.read();
    
    if (cmd == '1') {
      digitalWrite(LED_PIN, HIGH);
      startTriggerTime = millis(); // Record timestamp when '1' is received
      pendingStart = true;         // Flag to start 3-second delay count
      isRunning = false;
    } else if (cmd == '0') {
      isRunning = false;
      pendingStart = false;        // Cancel any pending start
      digitalWrite(LED_PIN, LOW);
      
      waterStepper.stop(); // Decelerate to a complete stop
      
      // De-energize coils to prevent heat build-up
      digitalWrite(motorPin1, LOW);
      digitalWrite(motorPin2, LOW);
      digitalWrite(motorPin3, LOW);
      digitalWrite(motorPin4, LOW);
    }
  }

  // 3. Handle non-blocking 3-second delay before motor execution
  if (pendingStart && (millis() - startTriggerTime >= 3000)) {
    pendingStart = false;
    isRunning = true;
    waterStepper.moveTo(2000000000); 
  }

  // 4. Process acceleration-based stepping
  if (isRunning) {
    waterStepper.run(); // Computes acceleration profile dynamically
  }
}