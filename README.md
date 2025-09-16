HackWesTX2025 — Physical Lichess Board
======================================
Project Showcase
https://youtu.be/vnubYaI1xLQ

======================================


Play on Lichess using a real 4×4 membrane keypad on an Arduino Uno R3.

A small Python program sends your keypad moves to Lichess (Board API),

draws a simple chessboard in the terminal, and drives four status LEDs.



IMPORTANT

---------

Upload and run the Arduino sketch first. Close the Arduino Serial Monitor

before starting the Python program.



WHAT’S INCLUDED

---------------

\- Arduino sketch: keypad scan + PWM LEDs + line-based serial commands

\- pyBridge.py: talks to Lichess, shows a terminal board, triggers LEDs



HARDWARE

--------

\- Arduino Uno R3

\- 4×4 membrane keypad (HX-543)

\- 4 LEDs with 220–1kΩ series resistors

\- Breadboard + jumpers



WIRING (UNO)

------------

LEDs on PWM pins for smooth brightness:

&nbsp; RED    -> D3   (lose)

&nbsp; YELLOW -> D5   (check)

&nbsp; BLUE   -> D6   (capture)

&nbsp; GREEN  -> D9   (win)



Keypad:

&nbsp; Rows: D2, D4, D7, D8

&nbsp; Cols: A0, A1, A2, A3   (A0–A3 used as digital inputs)



Avoid D0/D1 (USB serial).



KEYPAD ENTRY

------------

Enter four digits 1..8 for from/to squares, then press '#'.

Example: e2e4  ->  5 2 5 4 #

'\*' clears the input buffer.



RUN ORDER

---------

1\) Arduino

&nbsp;  - Open the sketch in mainArduinoCode/

&nbsp;  - Confirm pins:

&nbsp;      rowPins = {2, 4, 7, 8}

&nbsp;      colPins = {A0, A1, A2, A3}

&nbsp;  - Upload to the Uno.

&nbsp;  - Close the Serial Monitor.



2\) Python (Windows PowerShell)

&nbsp;  - Install deps:

&nbsp;      py -m pip install pyserial pyautogui berserk python-chess

&nbsp;  - Create a Lichess token with scope: board:play

&nbsp;  - Set the token in this terminal:

&nbsp;      $env:LICHESS\_TOKEN = "YOUR\_TOKEN"

&nbsp;  - (Optional) Better Unicode in console:

&nbsp;      chcp 65001

&nbsp;  - Run:

&nbsp;      py .\\pyBridge.py



&nbsp;  CMD equivalents:

&nbsp;      set LICHESS\_TOKEN=YOUR\_TOKEN

&nbsp;      py pyBridge.py



WHAT THE PYTHON BRIDGE DOES

---------------------------

\- Reads UCI moves from the Arduino (e.g., e2e4)

\- Validates against the current position, sends to Lichess via Board API

\- Renders a small Unicode board in the terminal

\- Listens to game events and sends LED commands over serial:

&nbsp;   CAP        -> blue pulse (capture)

&nbsp;   CHECK\_ON   -> yellow steady on

&nbsp;   CHECK\_OFF  -> yellow off

&nbsp;   WIN        -> green pulse (win)

&nbsp;   LOSE       -> red pulse (loss)



Arduino hotkeys for testing:

&nbsp; A = WIN,  B = LOSE,  C = CAP,  D = toggle CHECK



CONFIG SWITCHES (pyBridge.py)

-----------------------------

USE\_API\_SEND = True     # send moves via Lichess API (headless)

TYPE\_MODE    = False    # fallback: type moves into active window

ANY\_CHECK    = False    # yellow only when YOU are in check

&nbsp;                       # (set True to light yellow for either side)



TROUBLESHOOTING

---------------

\- Port busy / no serial: close the Arduino Serial Monitor; replug USB.

\- LED not changing: press D to toggle yellow (hardware check).

&nbsp; You should see lines like:

&nbsp;   \[SEND] -> CHECK\_ON

&nbsp;   Serial: RX: CHECK\_ON

\- Unicode board misaligned: use Cascadia Mono or Consolas; run chcp 65001.

\- API auth: ensure LICHESS\_TOKEN is set and includes board:play.

\- Line endings on Windows: repo includes .gitattributes to keep LF.



PROJECT LAYOUT (SUGGESTED)

--------------------------

HackWesTX2025/

&nbsp; mainArduinoCode/

&nbsp;   mainArduinoCode.ino

&nbsp; pyBridge.py

&nbsp; README.txt

&nbsp; .gitattributes



