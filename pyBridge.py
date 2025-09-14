# pyBridge.py — Headless API sender + terminal board + LEDs (safe token, strict UCI)
import os, sys, time, threading
import serial, serial.tools.list_ports
import pyautogui

import berserk            # pip install berserk
import chess              # pip install python-chess
from dataclasses import dataclass
from typing import Optional

BAUD = 115200
PORT = None                 # set "COM7" to force; else auto-detect
USE_API_SEND = True         # True: send moves via Lichess Board API
TYPE_MODE    = False        # True: type into browser as fallback
ANY_CHECK    = False        # True: yellow if EITHER side in check; False: only when YOU are in check

# ---------- serial helpers ----------
def pick_port():
    if PORT:
        return PORT
    candidates = []
    for p in serial.tools.list_ports.comports():
        desc = (p.description or "").lower()
        hwid = (p.hwid or "").lower()
        if any(t in desc for t in ["arduino","uno","ch340","sparkfun","wchusbserial"]):
            candidates.append(p.device)
        elif any(v in hwid for v in ["2341:", "2a03:", "1a86:7523", "10c4:ea60"]):
            candidates.append(p.device)
    if candidates: return candidates[0]
    ports = [p.device for p in serial.tools.list_ports.comports()]
    if len(ports) == 1: return ports[0]
    raise RuntimeError("No Arduino port found. Set PORT='COM7' or plug the board in.")

# ---------- UCI validator ----------
def is_uci_move(s: str) -> bool:
    if len(s) == 4:
        f1,r1,f2,r2 = s
        return (f1 in "abcdefgh" and r1 in "12345678" and
                f2 in "abcdefgh" and r2 in "12345678")
    if len(s) == 5:
        return is_uci_move(s[:4]) and s[4] in "qrbn"
    return False

# ---------- terminal board ----------
PIECES = {'P':'♙','N':'♘','B':'♗','R':'♖','Q':'♕','K':'♔',
          'p':'♟','n':'♞','b':'♝','r':'♜','q':'♛','k':'♚'}
FILES = "abcdefgh"
INV = "\x1b[7m"; RST = "\x1b[0m"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def render_board(board: chess.Board, orient_white: bool, last_uci: Optional[str], my_color: Optional[chess.Color]):
    ranks = range(7, -1, -1) if orient_white else range(0, 8)
    files = range(0, 8)      if orient_white else range(7, -1, -1)
    last_from = last_to = None
    if last_uci:
        try:
            mv = chess.Move.from_uci(last_uci)
            last_from, last_to = mv.from_square, mv.to_square
        except Exception:
            pass
    lines = []
    for r in ranks:
        row = []
        for f in files:
            sq = chess.square(f, r)
            piece = board.piece_at(sq)
            glyph = PIECES.get(piece.symbol(), '·') if piece else '·'
            cell = f" {glyph} "
            if sq in (last_from, last_to):
                cell = f"{INV}{cell}{RST}"
            row.append(cell)
        lines.append(f"{r+1} " + "".join(row))
    footer = "   " + "".join([f" {FILES[i]} " for i in files])
    clear_screen()
    print("Lichess Physical Board — terminal view")
    print("---------------------------------------")
    turn = "White" if board.turn == chess.WHITE else "Black"
    you  = "  (YOU)" if (my_color is not None and board.turn == my_color) else ""
    print(f"Turn: {turn}{you}")
    if board.is_check():
        who = "YOU" if (my_color is not None and board.turn == my_color) else "OPPONENT"
        print(f"⚠️  CHECK! ({who})")
    print()
    print("\n".join(lines))
    print(footer)
    print()

# ---------- shared live state ----------
@dataclass
class LiveState:
    game_id: Optional[str] = None
    board:   Optional[chess.Board] = None
    my_color: Optional[chess.Color] = None
    last_uci: Optional[str] = None

state = LiveState()
state_lock = threading.Lock()

# ---------- Lichess watcher (events -> LEDs + board print) ----------
def lichess_watcher(ser, client: Optional[berserk.Client]):
    if not client:
        print("No LICHESS_TOKEN set — skipping Lichess watcher.")
        return
    try:
        me = client.account.get()
        my_id = (me.get('id') or "").lower()
        print("Logged in as:", me.get("username"))
    except Exception as e:
        print("[Lichess] account.get failed:", e); return

    def led(cmd: str):
        try:
            ser.write((cmd + "\n").encode("utf-8"))
            print(f"[SEND] -> {cmd}")
        except Exception as e:
            print("LED write failed:", e)

    def watch_game(gid: str):
        board = chess.Board()
        my_color = None
        moves_seen = 0
        last_uci = None
        last_check = None  # track last LED state to avoid spam
        print(f"[Lichess] Watching game {gid}")

        def update_check_led():
            nonlocal last_check
            you_in_check = (my_color is not None and board.turn == my_color and board.is_check())
            target = board.is_check() if ANY_CHECK else you_in_check
            if target != last_check:
                led("CHECK_ON" if target else "CHECK_OFF")
                print(f"[LED] {'CHECK_ON' if target else 'CHECK_OFF'} (any={board.is_check()}, you={you_in_check})")
                last_check = target

        for ev in client.board.stream_game_state(gid):
            t = ev.get('type')

            if t == 'gameFull':
                white_id = (ev.get('white', {}).get('id') or "").lower()
                black_id = (ev.get('black', {}).get('id') or "").lower()
                my_color = chess.WHITE if white_id == my_id else chess.BLACK
                mv_str = ev.get('state', {}).get('moves', "")
                for u in mv_str.split():
                    board.push(chess.Move.from_uci(u))
                moves_seen = len(board.move_stack)
                with state_lock:
                    state.game_id, state.board, state.my_color, state.last_uci = gid, board.copy(), my_color, None
                render_board(board, orient_white=(my_color==chess.WHITE), last_uci=None, my_color=my_color)
                update_check_led()

            elif t == 'gameState':
                mv_str = ev.get('moves', "")
                seq = mv_str.split()
                if len(seq) > moves_seen:
                    for u in seq[moves_seen:]:
                        move = chess.Move.from_uci(u)
                        if board.is_capture(move): led("CAP")
                        board.push(move)
                        last_uci = u
                    moves_seen = len(seq)
                    with state_lock:
                        state.board = board.copy(); state.last_uci = last_uci
                    render_board(board, orient_white=(my_color==chess.WHITE), last_uci=last_uci, my_color=my_color)
                    update_check_led()

                status = ev.get('status')
                winner = (ev.get('winner') or "").lower()
                if status in ("mate","resign","outoftime","stalemate","draw","aborted"):
                    if winner:
                        i_won = (winner == ("white" if my_color==chess.WHITE else "black"))
                        led("WIN" if i_won else "LOSE")
                        print(f"\nResult: {'YOU WIN' if i_won else 'YOU LOSE'} ({status})")
                    else:
                        print(f"\nResult: {status.upper()}")
                    break

        with state_lock:
            state.game_id = None; state.board = None; state.my_color = None; state.last_uci = None

    try:
        ongoing = client.games.get_ongoing() or []
        if ongoing: watch_game(ongoing[0]["gameId"])
    except Exception as e:
        print("[Lichess] get_ongoing failed:", e)

    try:
        for ev in client.board.stream_incoming_events():
            if ev.get('type') == 'gameStart':
                watch_game(ev['game']['id'])
    except Exception as e:
        print("[Lichess] incoming events stream ended:", e)

# ---------- API move sender ----------
def try_send_api_move(client: Optional[berserk.Client], uci: str) -> bool:
    if not client:
        print("No API client; set LICHESS_TOKEN or set USE_API_SEND=False.")
        return False
    with state_lock:
        gid   = state.game_id
        board = state.board.copy() if state.board else None
        mine  = state.my_color
    if not gid or not board or mine is None:
        print("No active game yet."); return False
    if board.turn != mine:
        print("Not your turn."); return False
    try:
        mv = chess.Move.from_uci(uci)
    except Exception:
        print("Bad UCI:", uci); return False
    if mv not in board.legal_moves:
        print("Illegal (local):", uci); return False
    try:
        client.board.make_move(gid, uci)   # or: client.board.make_move(game_id=gid, move=uci)
        print("API move sent:", uci)
        return True
    except Exception as e:
        print("API send failed:", e)
        return False

# ---------- main ----------
def main():
    # serial
    port = pick_port()
    print(f"Connecting to {port} @ {BAUD}...")
    ser = serial.Serial(port, BAUD, timeout=0.1)

    # lichess client (SAFE TOKEN)
    token = os.environ.get("LICHESS_TOKEN")
    client = berserk.Client(session=berserk.TokenSession(token)) if token else None

    # start watcher (updates state + LEDs + terminal board)
    threading.Thread(target=lichess_watcher, args=(ser, client), daemon=True).start()

    print("Connected. (If TYPE_MODE=True, click your Lichess board once.)")
    time.sleep(1.2)

    try:
        while True:
            line = ser.readline().strip()
            if not line:
                continue
            try:
                msg = line.decode("utf-8").strip()
            except UnicodeDecodeError:
                continue

            # only send true UCI
            if is_uci_move(msg):
                print("Move:", msg)
                sent = False
                if USE_API_SEND:
                    sent = try_send_api_move(client, msg)
                if (not sent) and TYPE_MODE:
                    pyautogui.typewrite(msg); pyautogui.press("enter"); sent = True
                if not sent:
                    print("Move not sent (see message above).")
            else:
                print("Serial:", msg)
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()

if __name__ == "__main__":
    main()
