
# PCA Password Checker

This is a Python script intended for kiosk use. It utilizes HaveIBeenPwned's (HIBP) API to check user-input strings against their vast database of password breaches and a helper script to grep through rockyou.txt.




## Installation

Clone the repo and initialize a venv.

``` bash
    git clone https://github.com/ChefPenguin/pcapasscheck.git
    python -m venv pcapasscheck
    cd pcapasscheck
    bin/pip install -r requirements.txt
    chmod +x ./check_wordlist.sh
```




## Usage

Run using:

``` bash
    bin/python passwordchecker.py
```


>[!NOTE] This assumes that your seclists is installed in the default place, `/usr/share/seclists/Password/Leaked-Databases/rockyou.txt`, and you leave `check_wordlist.sh` in the same directory as the python script. If not, please edit `CHECK_BASH` with the appropriate path for check_wordlist.sh and `WORDLIST` with the appropriate path for rockyou.txt, in `passwordcheckerv5.py`.



## To-Dos


### DONE Improve the UI DONE

Right now it uses `curses` which...I just don't care for, I'm planning on switching it over to `urwid`


### DONE Add capability to grep through wordlists DONE

Python isn't the fastest at parsing through MBs worth of wordlists.
Add in an OS hook to \`grep\` through seclist's Leaked-Databases section. On my computer I could probably grep through all of seclists in a second or two, but on a kiosk, maybe reign in the scope a bit. 


### TODO Calculate the approximate difficulty of cracking

I remember there's an XKCD comic about how adding units of entropy (increasing the length of the password) adds a calculable amount of time to cracking the password, it'd be neat to find that algorithm and add it on there.

