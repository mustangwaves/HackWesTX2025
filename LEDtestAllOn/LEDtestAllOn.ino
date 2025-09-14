// All-on LED test for A0..A3
const int LED_RED    = A0;
const int LED_YELLOW = A1;
const int LED_BLUE   = A2;
const int LED_GREEN  = A3;

void setup() {
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_BLUE, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);

  // turn all four on
  digitalWrite(LED_RED, HIGH);
  digitalWrite(LED_YELLOW, HIGH);
  digitalWrite(LED_BLUE, HIGH);
  digitalWrite(LED_GREEN, HIGH);
}

void loop() {
  // nothing — LEDs stay on
}
