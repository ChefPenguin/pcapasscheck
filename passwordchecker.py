#!/usr/bin/env python3
import curses, hashlib, requests, textwrap, os, subprocess

API = "https://api.pwnedpasswords.com/range/{}"
UA  = "HIBP-KioskDemo/PCA"
list = "~/Downloads/rockyou.txt"

#check if it's in HIBP's database using the first few 5 characters of the SHA1 hash. It then returns the last 5 characters, and it's compared. If it matches, it spits out the number of matches, if not, it's not in the database.
def check_pwned(plaintext: str) -> int | None:
    sha1 = hashlib.sha1(plaintext.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    try:
        r = requests.get(
            API.format(prefix),
            headers={"User-Agent": UA, "Add-Padding": "true"},
            timeout=8,
        )
        if r.status_code != 200:
            return None
        # Lines are "HASH_SUFFIX:COUNT"
        for line in r.text.splitlines():
            sfx, _, count = line.partition(":")
            if sfx == suffix:
                return int(count)
        return 0
    except requests.RequestException:
        return None

#Figure out why newlines aren't respect. Kids these days smh
BANNER = (
    "PCA Password Checker"
    "\n[!] FOR DEMO PURPOSES ONLY [!]"
    "\nPowered by HaveIBeenPwned"
)

def draw(stdscr):
    curses.curs_set(1)
    stdscr.nodelay(False)
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    def msg(y, text):
        for i, line in enumerate(textwrap.wrap(text, w-2)):
            stdscr.addstr(y+i, 1, line)

    input_buf = []
    show = False
    while True:
        stdscr.clear()
        msg(1, BANNER)
        stdscr.hline(2, 0, curses.ACS_HLINE, w)
        stdscr.addstr(4, 10, "Enter text to check (F2: toggle show/hide, Enter: check)")
        display = "".join(input_buf)
        masked  = display if show else "•" * len(display)
        stdscr.addstr(6, 1, f"> {masked}")
        stdscr.refresh()

        ch = stdscr.get_wch()
        if isinstance(ch, str) and ch.isprintable():
            input_buf.append(ch)
        elif ch in (curses.KEY_BACKSPACE, "\b", "\x7f"):
            if input_buf: input_buf.pop()
        elif ch == "\n":
            query = "".join(input_buf)
            input_buf.clear()
            stdscr.addstr(8, 1, "Checking…")
            stdscr.refresh()
            count = check_pwned(query)
            stdscr.move(8,1); stdscr.clrtoeol()
            if count is None:
                stdscr.addstr(8, 1, "Network error or service unavailable. Please try again.")
            elif count == 0:
                stdscr.addstr(8, 1, "Not found in HIBP's database.")
            else:
                stdscr.addstr(8, 1, f"Found {count:,} times in breaches.")
            stdscr.addstr(10, 1, "Press any key to continue…")
            stdscr.get_wch()
        elif ch == curses.KEY_F2:
            show = not show
        elif ch == curses.KEY_F10:
            break

def main():
    curses.wrapper(draw)

if __name__ == "__main__":
    main()
