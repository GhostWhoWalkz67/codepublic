# Hasher

A command-line password hashing tool that generates cryptographic hashes from any input string across 9 industry-standard algorithms. Designed to pair directly with the **Dehasher** app — every hash it creates can be dropped straight into Dehasher and cracked.

Built by **GhostWhoWalkz** — follow the journey from trailer park kid, to air force pilot, to burnt out trial attorney teaching herself to code.
- GitHub: https://www.github.com/GhostWhoWalkz67
- Blog: https://forgottenfieldnotes.blogspot.com/

---

## What It Does

- Hashes any password or string using your choice of 9 algorithms
- Saves the resulting hash as a `.txt` file to your Desktop
- Prints the exact `hashcat` command needed to crack the hash with Dehasher
- Loops so you can hash multiple passwords in one session without restarting
- Every hash type matches a hashcat `-m` mode used in the Dehasher app

---

## Supported Hash Types

| # | Algorithm | Hashcat Mode | Notes |
|---|-----------|-------------|-------|
| 1 | MD5 | -m 0 | Most common — web apps, Linux |
| 2 | MD4 | -m 900 | Older format, sometimes seen in CTFs |
| 3 | SHA1 | -m 100 | Common in older systems |
| 4 | SHA-256 | -m 1400 | Modern standard |
| 5 | SHA-384 | -m 10800 | Less common |
| 6 | SHA-512 | -m 1700 | Strong general purpose |
| 7 | bcrypt | -m 3200 | Intentionally slow — best for real passwords |
| 8 | SHA-512 crypt | -m 1800 | Linux `/etc/shadow` format |
| 9 | NTLM | -m 1000 | Windows password format |

---

## macOS Terminal Setup

This app runs entirely in Terminal. Follow these steps from scratch on macOS.

### Step 1 — Install Homebrew

Homebrew is the package manager for macOS. If you don't have it yet:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Verify it installed:
```bash
brew --version
```

### Step 2 — Install Python 3

macOS ships with an outdated Python 2. Install Python 3 via Homebrew:

```bash
brew install python
```

Verify:
```bash
python3 --version
```

You should see Python 3.11 or higher.

### Step 3 — Install Required Python Libraries

The app requires two pip packages — `bcrypt` for bcrypt hashing and `passlib` for SHA-512 crypt support.

```bash
pip3 install bcrypt passlib --break-system-packages
```

> **Note:** The `--break-system-packages` flag is required on macOS with Python 3.11+. This is normal behavior — it bypasses a warning and installs the packages correctly.

Verify both installed:
```bash
pip3 show bcrypt
pip3 show passlib
```

### Step 4 — Set Up Your Project Folder

```bash
mkdir -p ~/Desktop/code/projects/hasher
cd ~/Desktop/code/projects/hasher
```

Place `main.py` inside that folder.

### Step 5 — Run the App

```bash
cd ~/Desktop/code/projects/hasher
python3 main.py
```

---

## How to Use

### Basic Flow

1. Run `python3 main.py`
2. Enter the password or string you want to hash
3. Select a hash algorithm from the menu
4. Name your output file (saved to Desktop as `.txt`)
5. The hash is displayed in the terminal and saved to Desktop
6. The app prints the exact hashcat command to crack it
7. Choose to hash another password or quit

### Example Session

```
=======================================================
  PASSWORD HASHER
=======================================================

  Enter password to hash (or 'q' to quit): sunshine

  Select hash type:
   1. MD5                   (hashcat -m 0)
   2. MD4                   (hashcat -m 900)
   3. SHA1                  (hashcat -m 100)
   ...

  Enter choice: 1

  Name your output file (no extension): test1

=======================================================
  RESULT
=======================================================

  Password   : sunshine
  Hash Type  : MD5
  Hash       : 0c08a4d4f4d4b2d4e4d4c4d4e4d4b2d4
  Saved to   : /Users/yourname/Desktop/test1.txt

  Crack it   : hashcat -m 0 /Users/yourname/Desktop/test1.txt ~/wordlists/rockyou.txt
=======================================================

  Hash another password? (y/n):
```

### Using Hasher + Dehasher Together

These two apps are built to work as a pair for learning and practice:

1. Open **Hasher** — hash a known password with any algorithm
2. The hash is saved to Desktop as a `.txt` file
3. Open **Dehasher** — paste the hash and let it identify the type automatically
4. Run a cracking attack and verify it recovers the original password
5. Experiment with different algorithms to understand why bcrypt takes longer than MD5

This workflow is ideal for TryHackMe practice — you can generate your own hashes, crack them, and understand exactly what is happening at each step.

---

## Algorithm Notes

**MD5, MD4, SHA1**
These are fast algorithms never designed for password storage. At millions of hashes per second on modern hardware, they are cracked almost instantly from any common wordlist. Use these to understand why fast hashes are dangerous.

**SHA-256, SHA-384, SHA-512**
Cryptographically strong but still fast when used for passwords without a salt or stretching. Appear in many CTF challenges.

**bcrypt**
The correct choice for real password storage. The cost factor (set to 12 in this app) makes it intentionally slow — roughly 25 hashes per second on Apple M1 compared to millions per second for MD5. Note that bcrypt hashes include a random salt, so the same password hashed twice will produce two different hash strings — both are valid.

**SHA-512 crypt**
The format used in modern Linux `/etc/shadow` files. Includes a salt and multiple rounds of hashing. Slower than plain SHA-512 but faster than bcrypt.

**NTLM**
The format Windows uses internally for storing account passwords. Common in Active Directory environments and frequently seen in CTF challenges involving Windows targets.

---

## Output Files

Every hash is saved to your Desktop as a plain `.txt` file containing just the hash string on a single line. This format is exactly what hashcat expects as input — you can drop it directly into Dehasher or use it with hashcat manually.

Example file contents (`test1.txt`):
```
0c08a4d4f4d4b2d4e4d4c4d4e4d4b2d4
```

---

## Troubleshooting

**"No module named bcrypt"**
Run:
```bash
pip3 install bcrypt --break-system-packages
```

**"No module named passlib"**
Run:
```bash
pip3 install passlib --break-system-packages
```

**"MD4 not supported on this system"**
Some macOS OpenSSL builds disable MD4. This is a known macOS limitation. All other hash types will still work normally.

**"python3: command not found"**
Python 3 is not installed. Run:
```bash
brew install python
```

**App closes immediately**
Make sure you are running Python 3.11 or higher:
```bash
python3 --version
```
If you see 3.9 or lower, upgrade with:
```bash
brew upgrade python
```

---

## Dependencies Summary

| Dependency | Install Command | Purpose |
|------------|-----------------|---------|
| Homebrew | See Step 1 | macOS package manager |
| Python 3.11+ | `brew install python` | Runs the app |
| bcrypt | `pip3 install bcrypt --break-system-packages` | bcrypt hashing support |
| passlib | `pip3 install passlib --break-system-packages` | SHA-512 crypt support |

All other hash algorithms (MD5, SHA1, SHA-256, SHA-384, SHA-512, NTLM) use Python's built-in `hashlib` module — no additional installs required for those.

---

## The Full Toolkit

```
~/Desktop/code/projects/
    hasher/        → creates hashes (this app)
    dehasher/      → identifies and cracks hashes
    encryptor/     → encrypts text and files
    decryptor/     → decrypts anything the encryptor creates
```
