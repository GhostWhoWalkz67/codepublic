# Encryptor

A command-line encryption tool that protects text and files using 7 industry-standard and classic encryption algorithms. Supports both password-based and key file-based encryption, and saves all encrypted output directly to your Desktop. Designed to pair with the **Decryptor** app — anything encrypted here can be fully reversed there.

Built by **GhostWhoWalkz** — follow the journey from trailer park kid, to air force pilot, to burnt out trial attorney teaching herself to code.
- GitHub: https://www.github.com/GhostWhoWalkz67
- Blog: https://forgottenfieldnotes.blogspot.com/

---

## What It Does

- Encrypts plain text you type directly into the terminal
- Encrypts any file on your Desktop (any file type — documents, images, code, etc.)
- Supports password-based encryption (you remember a passphrase) and key file-based encryption (app generates a reusable key file)
- Saves all encrypted output to Desktop as `.enc` files
- Saves all generated key files to `~/Desktop/keys/` automatically
- RSA key pair generation — creates a public and private `.pem` key pair on first use
- Loops so you can encrypt multiple items in one session

---

## Supported Algorithms

| # | Algorithm | Type | Key Method | Best For |
|---|-----------|------|------------|----------|
| 1 | AES-256-CBC | Symmetric | Password or key file | General purpose encryption |
| 2 | AES-256-GCM | Symmetric | Password or key file | When tamper detection matters |
| 3 | ChaCha20-Poly1305 | Symmetric | Password or key file | Modern fast encryption |
| 4 | Fernet | Symmetric | Password or key file | Simple beginner-friendly encryption |
| 5 | RSA-2048 | Asymmetric | Key file only (public/private pair) | Short text, key exchange |
| 6 | XOR Cipher | Symmetric | Password | Educational — not secure |
| 7 | Caesar Cipher | Symmetric | Shift number | Educational — not secure |

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

### Step 3 — Install Required Python Library

The app requires the `cryptography` library which provides all encryption algorithms:

```bash
pip3 install cryptography --break-system-packages
```

> **Note:** The `--break-system-packages` flag is required on macOS with Python 3.11+. This is normal — it bypasses a warning and installs the package correctly.

Verify it installed:
```bash
pip3 show cryptography
```

### Step 4 — Set Up Your Project Folder

```bash
mkdir -p ~/Desktop/code/projects/encryptor
cd ~/Desktop/code/projects/encryptor
```

Place `main.py` inside that folder.

### Step 5 — Run the App

```bash
cd ~/Desktop/code/projects/encryptor
python3 main.py
```

---

## How to Use

### Basic Flow

1. Run `python3 main.py`
2. Choose whether to encrypt text or a file
3. Select an encryption algorithm
4. Choose your key method — password or key file
5. Enter your password, or name your key file
6. Name your output file (saved to Desktop as `.enc`)
7. Encryption runs and the result is saved
8. Choose to encrypt something else or quit

### Encrypting Text

Select option `1` at the first prompt and type your text directly into the terminal. The text is encrypted and saved as a `.enc` file on your Desktop.

### Encrypting a File

Select option `2` and the app scans your Desktop and presents a numbered list of all files. Select the number of the file you want to encrypt. Any file type is supported — documents, images, PDFs, code files, etc.

### Password-Based Encryption

When you choose password as the key method, type any passphrase you will remember. The app derives a strong 256-bit encryption key from your password using PBKDF2 with SHA-256 and 480,000 iterations. The salt is automatically embedded in the output file — you only need your password to decrypt later.

### Key File-Based Encryption

When you choose key file, the app generates a random 256-bit key and saves it to `~/Desktop/keys/`. You will be prompted for a key file name — a default is suggested based on the algorithm. On future runs, if the same key file name exists it will be reused automatically.

> **Warning:** Key files must be kept safe. If the key file is deleted or lost, the encrypted data cannot be recovered.

### RSA Encryption

RSA generates a public/private key pair on first use and saves both to `~/Desktop/keys/`. The public key encrypts the data and the private key is required to decrypt it.

> **Important:** RSA can only encrypt up to approximately 190 bytes of text directly. For larger content, use AES-256-GCM or ChaCha20-Poly1305 instead. The app will warn you if your input exceeds this limit.

---

## Key Files

All generated key files are stored in:

```
~/Desktop/keys/
```

Default key file names by algorithm:

| Algorithm | Default Key File |
|-----------|-----------------|
| AES-256-CBC | `aes_256_cbc.key` |
| AES-256-GCM | `aes_256_gcm.key` |
| ChaCha20-Poly1305 | `chacha20_poly1305.key` |
| Fernet | `fernet.key` |
| RSA-2048 | `<yourname>_private.pem` and `<yourname>_public.pem` |

You can use a custom name for any key file — just remember the name when decrypting.

---

## Output Files

Encrypted files are saved to your Desktop with the `.enc` extension. The default naming pattern is:

```
<original_name>_<algorithm>.enc
```

For example, encrypting `notes.txt` with AES-256-GCM produces:
```
notes_aes_256_gcm.enc
```

The Decryptor app automatically detects `.enc` files on your Desktop and presents them as a list — no need to type file paths manually.

---

## Algorithm Notes

**AES-256-CBC**
The most widely deployed encryption standard in the world. Used in VPNs, HTTPS, file encryption tools, and secure messaging. Fast and extremely well tested. Does not include authentication — a tampered file will decrypt to garbage rather than raising an error.

**AES-256-GCM**
AES with an authentication tag (GCM mode). If the encrypted file is modified in any way after encryption, decryption will fail with a tamper warning instead of producing corrupted output. This is the recommended choice for most use cases.

**ChaCha20-Poly1305**
A modern stream cipher used in TLS 1.3, WireGuard VPN, and Signal. Faster than AES on devices without hardware AES acceleration. Also includes authentication — tampered files are detected. Excellent choice for any platform.

**Fernet**
A high-level symmetric encryption format from the Python `cryptography` library. Handles key generation, IV, and authentication automatically. Easiest to use but output is slightly larger than raw AES. Good for learning and simple projects.

**RSA-2048**
Unlike the other algorithms, RSA is asymmetric — data encrypted with the public key can only be decrypted with the private key. This is the foundation of public key infrastructure (PKI), SSH, and TLS certificates. Limited to short text in this app due to RSA's block size constraints.

**XOR Cipher**
A simple bitwise operation cipher included for educational purposes. Not cryptographically secure — given enough ciphertext the key can be recovered. Useful for understanding how basic encryption works at the bit level.

**Caesar Cipher**
The oldest known substitution cipher, dating to ancient Rome. Shifts every letter by a fixed number of positions. Trivially broken. Included purely for historical and educational context.

---

## Using Encryptor + Decryptor Together

These two apps are built as a pair:

1. Open **Encryptor** and encrypt a file or text
2. The `.enc` file is saved to your Desktop
3. Open **Decryptor** — it automatically finds the `.enc` file
4. Select the same algorithm used to encrypt
5. Enter the same password or key file name
6. The original content is restored and saved to Desktop

This is also a great way to learn what each algorithm does — encrypt the same text with different algorithms and compare the output sizes, formats, and decryption behavior.

---

## Troubleshooting

**"No module named cryptography"**
Run:
```bash
pip3 install cryptography --break-system-packages
```

**"python3: command not found"**
Python 3 is not installed. Run:
```bash
brew install python
```

**RSA encryption failed — input too large**
RSA in this app is limited to ~190 bytes of text. For anything larger use AES-256-GCM or ChaCha20-Poly1305 instead.

**No files showing in Desktop scan**
Make sure the file you want to encrypt is saved directly to your Desktop (not in a subfolder). The app only scans the top level of `~/Desktop/`.

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
| cryptography | `pip3 install cryptography --break-system-packages` | All encryption algorithms |

That's it — one pip package covers everything.

---

## The Full Toolkit

```
~/Desktop/code/projects/
    hasher/        → creates cryptographic hashes
    dehasher/      → identifies and cracks hashes
    encryptor/     → encrypts text and files (this app)
    decryptor/     → decrypts anything the encryptor creates
```

---

## Security Notes

- Password-derived keys use **PBKDF2 with SHA-256 and 480,000 iterations** — intentionally slow to resist brute force attacks against the password
- The salt and nonce/IV are embedded in every `.enc` file automatically — the Decryptor recovers them without any extra input from you
- AES-256-GCM and ChaCha20-Poly1305 include **authentication tags** — any modification to the encrypted file will cause decryption to fail with a clear error
- XOR and Caesar ciphers are included for learning only — do not use them to protect anything sensitive
- RSA private key files are stored as unencrypted `.pem` files — treat them like passwords and back them up securely
