#include <Keypad.h>

/* ====================== PWM LED MODULE ====================== */
// LED pins on PWM-capable pins
const int LED_RED    = 3;  // lose  (PWM)
const int LED_YELLOW = 5;  // check (PWM)
const int LED_BLUE   = 6;  // capture (PWM)
const int LED_GREEN  = 9;  // win (PWM)

// Brightness (0..255)
const uint8_t BR_RED_LOSE   = 200;
const uint8_t BR_BLUE_CAP   = 50;
const uint8_t BR_GREEN_WIN  = 140;
const uint8_t BR_YELL_CHECK = 255;

// Timers (millis, 0 = inactive)
unsigned long offAtRed   = 0;
unsigned long offAtBlue  = 0;
unsigned long offAtGreen = 0;
bool yellowOn = false;

static inline void pwmOff(int pin){ analogWrite(pin, 0); }
static inline void pwmOn (int pin, uint8_t v){ analogWrite(pin, v); }

void ledsSetup() {
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_BLUE, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pwmOff(LED_RED);
  pwmOff(LED_YELLOW);
  pwmOff(LED_BLUE);
  pwmOff(LED_GREEN);
}

void startPulse(int pin, uint8_t brightness, unsigned long ms) {
  pwmOn(pin, brightness);
  unsigned long now = millis();
  if (pin == LED_RED)   offAtRed   = now + ms;
  if (pin == LED_BLUE)  offAtBlue  = now + ms;
  if (pin == LED_GREEN) offAtGreen = now + ms;
}

void ledsTick() {
  unsigned long now = millis();
  if (offAtRed   && now >= offAtRed)   { pwmOff(LED_RED);   offAtRed   = 0; }
  if (offAtBlue  && now >= offAtBlue)  { pwmOff(LED_BLUE);  offAtBlue  = 0; }
  if (offAtGreen && now >= offAtGreen) { pwmOff(LED_GREEN); offAtGreen = 0; }

  // Steady CHECK indicator (PWM)
  if (yellowOn) pwmOn(LED_YELLOW, BR_YELL_CHECK);
  else          pwmOff(LED_YELLOW);
}

void handleLedCommand(const String& s) {
  String t = s; t.trim();
  if (t == "WIN")            { startPulse(LED_GREEN, BR_GREEN_WIN, 10000); Serial.println("RX: WIN"); }
  else if (t == "LOSE")      { startPulse(LED_RED,   BR_RED_LOSE,  10000); Serial.println("RX: LOSE"); }
  else if (t == "CAP")       { startPulse(LED_BLUE,  BR_BLUE_CAP,   5000); Serial.println("RX: CAP"); }
  else if (t == "CHECK_ON")  { yellowOn = true;  Serial.println("RX: CHECK_ON"); }
  else if (t == "CHECK_OFF") { yellowOn = false; Serial.println("RX: CHECK_OFF"); }
}

// Read line-based commands from Serial (non-blocking)
void ledsPollSerial() {
  static String line = "";
  while (Serial.available()) {
    char c = char(Serial.read());
    if (c == '\n' || c == '\r') {
      if (line.length()) { handleLedCommand(line); line = ""; }
    } else {
      line += c;
      if (line.length() > 48) line = ""; // overflow guard
    }
  }
}
/* ==================== END LED MODULE ==================== */


/* ===================== KEYPAD MODULE ==================== */
// 4x4 keypad, remapped to keep PWM pins free
const byte ROWS = 4, COLS = 4;
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};

// Use non-PWM digital pins for rows, and A0..A3 as digital for columns
byte rowPins[ROWS] = {2, 4, 7, 8};          // <— CHANGED
byte colPins[COLS] = {A0, A1, A2, A3};      // <— CHANGED (A0..A3 as digital inputs)

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

String buf = "";

char fileNumToLetter(char n) {  // '1'..'8' -> 'a'..'h'
  if (n < '1' || n > '8') return '?';
  return 'a' + (n - '1');
}
void resetBuffer() { buf = ""; }
/* =================== END KEYPAD MODULE =================== */


void setup() {
  Serial.begin(115200);
  delay(300);
  ledsSetup();

  Serial.println("READY (PWM LEDs on 3/5/6/9)");
  Serial.println("Press 4 digits (1..8) then #   (* = clear)");
}

void loop() {
  ledsPollSerial();
  ledsTick();

  char k = keypad.getKey();
  if (!k) return;

  Serial.print("KEY: "); Serial.println(k);

  // Demo hotkeys (same as before)
  if (k == 'A') { startPulse(LED_GREEN, BR_GREEN_WIN, 10000); Serial.println("LED: WIN"); return; }
  if (k == 'B') { startPulse(LED_RED,   BR_RED_LOSE,  10000); Serial.println("LED: LOSE"); return; }
  if (k == 'C') { startPulse(LED_BLUE,  BR_BLUE_CAP,   5000); Serial.println("LED: CAP"); return; }
  if (k == 'D') { yellowOn = !yellowOn; Serial.println(yellowOn ? "LED: CHECK_ON" : "LED: CHECK_OFF"); return; }

  if (k == '*') { resetBuffer(); Serial.println("CLEARED"); return; }

  if (k == '#') {
    if (buf.length() == 4) {
      char fFile = fileNumToLetter(buf[0]);
      char fRank = buf[1];
      char tFile = fileNumToLetter(buf[2]);
      char tRank = buf[3];
      if (fFile!='?' && tFile!='?' && fRank>='1' && fRank<='8' && tRank>='1' && tRank<='8') {
        Serial.print(fFile); Serial.print(fRank); Serial.print(tFile); Serial.println(tRank);
      } else {
        Serial.println("ERR");
      }
    } else {
      Serial.println("ERR");
    }
    resetBuffer(); return;
  }

  if (k >= '1' && k <= '8') {
    if (buf.length() < 4) buf += k;
    Serial.print("BUF: "); Serial.println(buf);
  }
}
