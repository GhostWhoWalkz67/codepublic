# Dehasher

A command-line hash identification and cracking tool powered by **hashcat**. Automatically identifies the type of hash you paste in, lets you filter wordlists by password length, and offers 10 targeted cracking methods — plus a dedicated WiFi WPA2 attack mode with automatic capture file conversion.

Built by **GhostWhoWalkz** — follow the journey from trailer park kid, to air force pilot, to burnt out trial attorney teaching herself to code.
- GitHub: https://www.github.com/GhostWhoWalkz67
- Blog: https://forgottenfieldnotes.blogspot.com/

---

## What It Does

- Automatically identifies hash types from a pasted hash string (MD5, SHA1, bcrypt, NTLM, and more)
- Handles ambiguous 32-character hashes (MD5 / MD4 / NTLM) with manual selection or full Auto mode
- Filters rockyou.txt wordlist to short passwords for faster attacks on slow hash types like bcrypt
- 10 cracking methods ranging from plain dictionary to rules-based mutation, hybrid, and combinator attacks
- **WiFi WPA2 mode** — scans Desktop for `.hc22000` or raw `.pcap/.pcapng` files, converts captures automatically, and launches a dedicated WPA2 attack menu
- Saves every hash to Desktop as a `.txt` file before cracking
- Designed to pair with **TryHackMe** CTF challenges and personal WiFi security testing

---

## Supported Hash Types

| Hash | Hashcat Mode | Notes |
|------|-------------|-------|
| MD5 | -m 0 | Most common — web apps, Linux |
| MD4 | -m 900 | Older, sometimes used in CTFs |
| SHA1 | -m 100 | Common in older systems |
| SHA-256 | -m 1400 | Modern standard |
| SHA-384 | -m 10800 | Less common |
| SHA-512 | -m 1700 | Strong general purpose |
| bcrypt | -m 3200 | Very slow — use short password filter |
| MD5 crypt | -m 500 | Linux `/etc/shadow` |
| SHA-512 crypt | -m 1800 | Linux `/etc/shadow` |
| NTLM | -m 1000 | Windows passwords |
| WPA2 (WiFi) | -m 22000 | Requires `.hc22000` capture file |

---

## Cracking Methods

| # | Method | Type | Best For |
|---|--------|------|----------|
| 1 | Dictionary + Best66 Rules | Wordlist + Rules | First attempt on any hash |
| 2 | Dictionary + Dive Rules | Wordlist + Rules | Aggressive — catches more variations |
| 3 | Dictionary + Toggle Rules | Wordlist + Rules | CamelCase passwords like PassWord1 |
| 4 | Dictionary + Leetspeak Rules | Wordlist + Rules | p@ssw0rd style substitutions |
| 5 | Dictionary + RockYou-30000 Rules | Wordlist + Rules | Most exhaustive wordlist+rules combo |
| 6 | Bigger Wordlist + Best66 Rules | Wordlist + Rules | When rockyou fails |
| 7 | WiFi-Specific Wordlist | Wordlist | WPA2 attacks only |
| 8 | Combinator Attack | Combinator | sunshinebutterfly style passwords |
| 9 | Hybrid Attack (Word + 4 digits) | Hybrid | sunshine2024 style passwords |
| 10 | TryHackMe Mode — Plain RockYou | Wordlist | CTF/THM simple passwords |

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

```bash
brew install python
```

Verify:
```bash
python3 --version
```

You should see Python 3.11 or higher.

### Step 3 — Install hashcat

hashcat is the core cracking engine the app runs under the hood:

```bash
brew install hashcat
```

Verify:
```bash
hashcat --version
```

You should see hashcat v6.x or v7.x.

### Step 4 — Install hcxtools (WiFi mode only)

hcxtools is required to convert raw Flipper Zero or Wireshark captures (`.pcap` / `.pcapng`) into the `.hc22000` format hashcat needs for WPA2 attacks. Skip this if you don't plan to use WiFi mode.

```bash
brew install hcxtools
```

Verify:
```bash
hcxpcapngtool --version
```

### Step 5 — Set Up Wordlists

The app expects wordlists in `~/wordlists/`. Create the folder and download the required files:

```bash
mkdir -p ~/wordlists
```

**rockyou.txt** — the primary wordlist used by most methods:

```bash
curl -L -o ~/wordlists/rockyou.txt.gz https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt
gunzip ~/wordlists/rockyou.txt.gz
```

**SecLists** — extended wordlists including the WiFi-specific WPA list:

```bash
git clone https://github.com/danielmiessler/SecLists.git ~/wordlists/SecLists
```

> **Note:** SecLists is a large repository (~1GB). The clone may take a few minutes depending on your connection.

Verify the key files exist after cloning:
```bash
ls ~/wordlists/rockyou.txt
ls ~/wordlists/SecLists/Passwords/WiFi-WPA/probable-v2-wpa-top4800.txt
ls ~/wordlists/SecLists/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt
```

### Step 6 — Set Up Your Project Folder

```bash
mkdir -p ~/Desktop/code/projects/dehasher
cd ~/Desktop/code/projects/dehasher
```

Place `main.py` inside that folder.

### Step 7 — Run the App

```bash
cd ~/Desktop/code/projects/dehasher
python3 main.py
```

---

## How to Use

### Cracking a Hash

1. Run `python3 main.py`
2. Select `1. Crack a hash`
3. Paste your hash string at the prompt — no quotes needed
4. The app identifies the hash type and shows the hashcat mode
5. For ambiguous 32-character hashes, choose MD5, MD4, NTLM, or Auto (tries all three)
6. Choose whether to save the hash to Desktop (required to run the attack)
7. Optionally filter the wordlist to short passwords (strongly recommended for bcrypt)
8. Select a cracking method and let hashcat run

### Short Password Filter

For slow hash types like bcrypt (`-m 3200`), filtering rockyou.txt to short passwords is strongly recommended. The app generates a filtered wordlist automatically and reuses it on future runs:

| Filter | Passwords | Best For |
|--------|-----------|----------|
| 4 chars | ~31,000 | Fastest — simple CTF hashes |
| 6 chars | ~43,000 | Recommended for bcrypt |
| 8 chars | ~55,000 | Broader coverage |
| Custom | Your choice | Any specific range |

Filtered wordlists are saved to `~/wordlists/rockyou_Nchar.txt` and reused automatically.

### Auto Mode (Ambiguous 32-char Hashes)

When the hash is 32 hex characters, it could be MD5, MD4, or NTLM — they are visually identical. Select `Auto` to try all three in sequence automatically with a single method choice.

### Hashcat Controls (While Running)

| Key | Action |
|-----|--------|
| `s` | Show current status and time estimate |
| `p` | Pause the attack |
| `c` | Checkpoint — save progress and stop cleanly |
| `f` | Finish current wordlist position then stop |
| `q` | Quit immediately |

### Resuming an Interrupted Attack

If an attack is stopped at a checkpoint or interrupted, resume it exactly where it left off:

```bash
hashcat --restore
```

### Checking the Potfile (Already Cracked Hashes)

hashcat caches every cracked hash in a potfile. To check if a hash was already cracked:

```bash
hashcat --show -m 0 ~/Desktop/yourhash.txt
```

Replace `-m 0` with the correct mode for your hash type.

> **Note:** The Dehasher app uses `--potfile-disable` by default so it always runs fresh attacks rather than skipping hashes that are already in the potfile.

---

## WiFi WPA2 Mode

### Requirements

- A WiFi capture file — either already converted `.hc22000` or a raw `.pcap` / `.pcapng` from a Flipper Zero or Wireshark
- hcxtools installed (see Step 4 above)
- The capture must contain a valid EAPOL handshake

### How to Use WiFi Mode

1. Run `python3 main.py`
2. Select `2. WiFi WPA2 attack`
3. Choose whether you have an `.hc22000` file already or a raw capture
4. If raw capture — the app scans your Desktop, lets you pick the file, and converts it automatically
5. Optionally filter the wordlist (WPA2 requires minimum 8 character passwords)
6. Select from the WiFi-specific attack methods
7. hashcat runs with `-m 22000` automatically

### WiFi Attack Methods

| # | Method | Notes |
|---|--------|-------|
| 1 | WiFi Wordlist (~4800 passwords) | Try this first — fast |
| 2 | RockYou Plain | Fast first pass |
| 3 | RockYou + Best66 Rules | Catches Password1! and similar |
| 4 | RockYou + Toggle Rules | CamelCase WiFi passwords |
| 5 | Hybrid — Word + 4 digits | sunshine2024 style |
| 6 | Combinator — Two words joined | sunshinebutterfly style |
| 7 | RockYou + Dive Rules | Most aggressive — very slow |

### Capture File Conversion (Flipper Zero Workflow)

1. Use WiFi Marauder on your Flipper Zero to capture EAPOL handshake packets
2. Export the capture as `.pcap` or `.pcapng` and save to Desktop
3. Run Dehasher → WiFi mode → select raw capture
4. The app converts it automatically using `hcxpcapngtool` and saves the `.hc22000` to Desktop

---

## Speed Reference (Apple M1 Pro via OpenCL)

These are approximate speeds on Apple Silicon. Speed varies by hardware.

| Hash Type | Speed | Time for rockyou (14M passwords) |
|-----------|-------|-----------------------------------|
| MD5 | ~5,700 MH/s | < 1 second |
| SHA1 | ~2,300 MH/s | < 1 second |
| SHA-256 | ~900 MH/s | < 1 second |
| NTLM | ~9,000 MH/s | < 1 second |
| WPA2 | ~96,000 H/s | ~2.5 minutes |
| bcrypt (cost 12) | ~25 H/s | ~6.5 days |

> **bcrypt tip:** Always use the short password filter. At 25 H/s, a 4-character filtered list (~31,000 passwords) takes about 20 minutes. The full rockyou.txt would take over a week.

---

## Troubleshooting

**"hashcat: command not found"**
hashcat is not installed or not in your PATH. Run:
```bash
brew install hashcat
```

**"hcxpcapngtool not found"**
hcxtools is not installed. Run:
```bash
brew install hcxtools
```

**"rockyou.txt not found"**
The wordlist is missing. Follow Step 5 above to download it.

**Hash identified as Unknown**
The app couldn't identify the hash format. Try pasting the hash into https://hashes.com for manual identification, then run hashcat directly with the correct `-m` mode.

**"All hashes found in potfile"**
hashcat already cracked this hash in a previous session. The app uses `--potfile-disable` to prevent this, but if running hashcat manually you can add `--potfile-disable` to your command or check the result with `--show`.

**Conversion produced an empty file (WiFi mode)**
The capture file didn't contain a complete EAPOL handshake. You need to recapture — both the client and the access point must exchange the full 4-way handshake during the capture.

**Metal API skipped (Apple Silicon)**
This is normal. hashcat skips the Metal API on Apple Silicon and falls back to OpenCL, which works correctly.

---

## Dependencies Summary

| Dependency | Install Command | Purpose |
|------------|-----------------|---------|
| Homebrew | See Step 1 | macOS package manager |
| Python 3.11+ | `brew install python` | Runs the app |
| hashcat | `brew install hashcat` | Core cracking engine |
| hcxtools | `brew install hcxtools` | WiFi capture conversion (optional) |
| rockyou.txt | See Step 5 | Primary wordlist |
| SecLists | `git clone` (see Step 5) | Extended wordlists + WiFi list |

No pip packages required — the app uses only Python standard library modules.

---

## Ethical Use

This tool is intended for:
- **CTF competitions** (TryHackMe, HackTheBox, etc.)
- **Testing your own passwords and hashes**
- **Testing your own WiFi network security**
- **Learning how password cracking works**

Do not use this tool against systems, accounts, or networks you do not own or have explicit written permission to test. Unauthorized access is illegal.
