#include <Keypad.h>

// Adjust for your wiring
const byte ROWS = 4; 
const byte COLS = 4;

// Layout of a standard 4x4 HX-543 membrane keypad
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};

// Change these to the actual Arduino pins you used
// Example: pins 2–9 (do NOT use pin 0/1 because they’re Serial RX/TX)
byte rowPins[ROWS] = {2, 3, 4, 5}; 
byte colPins[COLS] = {6, 7, 8, 9}; 

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

void setup() {
  Serial.begin(9600);
  Serial.println("Keypad test: press a key...");
}

void loop() {
  char key = keypad.getKey();
  if (key) { // if a key is pressed
    Serial.print("Key pressed: ");
    Serial.println(key);
  }
}
