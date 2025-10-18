#!/usr/bin/env python3

#!/usr/bin/env python3
import hashlib, requests, subprocess, os, queue, threading
import urwid

# ---------- Config ----------
API = "https://api.pwnedpasswords.com/range/{}"
UA  = "HIBP-KioskDemo/PCA"
HIBP_TIMEOUT_S = 8.0

BASH_CHECK = "./check_wordlist.sh"    # <-- set yours
WORDLIST   = "/usr/share/seclists/Passwords/Leaked-Databases/rockyou.txt"          # <-- set yours
WORDLIST_IGNORE_CASE = False
WORDLIST_TIMEOUT_S   = 15.0

# Centered panel size (tweak as you like)
PANEL_WIDTH  = 68
PANEL_HEIGHT = 16

PALETTE = [
    ("title", "light cyan,bold", ""), ("tip", "dark gray", ""),
    ("ok", "dark green,bold", ""), ("warn", "yellow,bold", ""),
    ("bad", "light red,bold", ""), ("dim", "light gray", ""),
    ("help", "light cyan", ""), ("err", "light red", ""),
]

# ---------- Checks ----------
def check_hibp(plaintext: str):
    sha1 = hashlib.sha1(plaintext.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    try:
        r = requests.get(
            API.format(prefix),
            headers={"User-Agent": UA, "Add-Padding": "true"},
            timeout=HIBP_TIMEOUT_S,
        )
    except requests.RequestException:
        return None, "network"
    if r.status_code != 200:
        return None, f"http-{r.status_code}"
    for line in r.text.splitlines():
        sfx, _, count = line.partition(":")
        if sfx == suffix:
            try: return int(count), None
            except ValueError: return None, "parse"
    return 0, None

def check_wordlist_bash(plaintext: str):
    script, wlist = BASH_CHECK, WORDLIST
    if not os.path.isfile(script):
        return None, "script-missing", script
    if not os.path.isfile(wlist):
        return None, "wordlist-missing", wlist
    args = ["bash", script, wlist]
    if WORDLIST_IGNORE_CASE: args.append("--ignore-case")
    try:
        cp = subprocess.run(
            args,
            input=(plaintext + "\n").encode("utf-8"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=WORDLIST_TIMEOUT_S,
            check=False,
            env=dict(os.environ, LC_ALL="C", LANG="C"),
        )
    except subprocess.TimeoutExpired as e:
        return None, "timeout", f"{e.timeout}s"
    except OSError as e:
        return None, "exec-error", str(e)
    if cp.returncode == 0: return True, None, None
    if cp.returncode == 1: return False, None, None
    return None, f"exit-{cp.returncode}", (cp.stderr or b"").decode("utf-8","ignore").strip() or None

# ---------- UI ----------
class App:
    def __init__(self):
        self.mask = True
        self.msg_q = queue.Queue()

        title = urwid.Text(("title", "Pensacola Cyber Army - Password Demo"), align="center")
        tip   = urwid.Text(("tip", "[!] Please don't enter a password you use for work. [!]"), align="center")

        self.edit = urwid.Edit(("dim", " Enter text: "), mask="•")
        self.hibp_line = urwid.Text(("dim", "HIBP: waiting"))
        self.wl_line   = urwid.Text(("dim", "Wordlist: waiting"))
        self.status    = urwid.Text(("help", "Enter: run both • F2: show/hide • F10: quit"), align="center")

        # Inner content laid out in a Pile
        content = urwid.Pile([
            title,
            tip,
            urwid.Divider(),
            urwid.AttrMap(self.edit, None),
            urwid.Divider(),
            urwid.Columns([
                urwid.LineBox(self.hibp_line, title="HIBP"),
                urwid.LineBox(self.wl_line,   title="Wordlist"),
            ], dividechars=1),
            urwid.Divider(),
            self.status,
        ])

        # Put content inside a centered LineBox
        panel = urwid.LineBox(content)

        # Overlay centers the panel both ways on a background fill
        background = urwid.SolidFill(" ")
        self.centered = urwid.Overlay(
            urwid.Filler(urwid.Padding(panel, align="center", width=PANEL_WIDTH),
                         valign="middle", height=PANEL_HEIGHT),
            background,
            align="center", width=("relative", 100),
            valign="middle", height=("relative", 100),
        )

        self.loop = urwid.MainLoop(self.centered, PALETTE, unhandled_input=self.on_key)
        self.loop.set_alarm_in(0.05, self._drain_queue)

    def on_key(self, key):
        if key == "f10": raise urwid.ExitMainLoop()
        if key == "f2":
            self.mask = not self.mask
            self.edit.set_mask(None if not self.mask else "•")
            self.status.set_text(("help", f"Input is {'visible' if not self.mask else 'hidden'} • Enter: run • F10: quit"))
        if key == "enter":
            text = self.edit.edit_text
            if not text.strip():
                self.status.set_text(("err","Please enter something non-empty."))
                return
            self.hibp_line.set_text(("dim","checking…"))
            self.wl_line.set_text(("dim","queued…"))
            self.status.set_text(("help","Working…"))
            threading.Thread(target=self._worker, args=(text,), daemon=True).start()

    def _worker(self, text):
        cnt, err = check_hibp(text)
        if err: self.msg_q.put(("hibp", ("warn", f"HIBP: error ({err})")))
        elif cnt == 0: self.msg_q.put(("hibp", ("ok", "HIBP: Not found.")))
        else: self.msg_q.put(("hibp", ("bad", f"HIBP: Found {cnt:,} times.")))
        found, werr, detail = check_wordlist_bash(text)
        if werr:
            extra = f" ({werr}{': ' + detail if detail else ''})"
            self.msg_q.put(("wl", ("warn", f"Wordlist: error{extra}")))
        elif found:
            extra = " (case-insensitive)" if WORDLIST_IGNORE_CASE else ""
            self.msg_q.put(("wl", ("bad", f"Wordlist: Present{extra}.")))
        else:
            self.msg_q.put(("wl", ("ok","Wordlist: Not found.")))
        self.msg_q.put(("done", None))

    def _drain_queue(self, *_):
        try:
            while True:
                tag, payload = self.msg_q.get_nowait()
                if tag == "hibp":
                    style, text = payload
                    self.hibp_line.set_text((style, text))
                elif tag == "wl":
                    style, text = payload
                    self.wl_line.set_text((style, text))
                elif tag == "done":
                    self.status.set_text(("help","Done. Enter: run again • F2: show/hide • F10: quit"))
        except queue.Empty:
            pass
        finally:
            self.loop.set_alarm_in(0.05, self._drain_queue)

    def run(self): self.loop.run()

if __name__ == "__main__":
    App().run()
