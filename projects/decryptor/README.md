# Decryptor

A command-line decryption tool that reverses everything produced by the **Encryptor** app. Supports 7 encryption algorithms including industry-standard AES-256, modern ChaCha20, RSA asymmetric encryption, Fernet, and classic educational ciphers.

Built by **GhostWhoWalkz** — follow the journey from trailer park kid, to air force pilot, to burnt out trial attorney teaching herself to code.
- GitHub: https://www.github.com/GhostWhoWalkz67
- Blog: https://forgottenfieldnotes.blogspot.com/

---

## What It Does

- Automatically scans your Desktop for `.enc` files and presents them as a numbered list
- Supports password-based decryption (PBKDF2 key derivation) and key file-based decryption
- Shows a preview of the decrypted content in the terminal on success
- Saves decrypted output back to your Desktop
- Works as a companion to the **Encryptor** app — anything encrypted there can be decrypted here

---

## Supported Algorithms

| # | Algorithm | Key Method | Notes |
|---|-----------|------------|-------|
| 1 | AES-256-CBC | Password or key file | Industry standard block cipher |
| 2 | AES-256-GCM | Password or key file | AES with tamper detection |
| 3 | ChaCha20-Poly1305 | Password or key file | Modern stream cipher, used in TLS |
| 4 | Fernet | Password or key file | Simple symmetric encryption |
| 5 | RSA-2048 | Key file only (private key) | Asymmetric — requires private `.pem` key |
| 6 | XOR Cipher | Password | Classic educational cipher |
| 7 | Caesar Cipher | Shift number | Classic letter-shift cipher |

---

## macOS Terminal Setup

This app runs entirely in Terminal — no GUI required. Follow these steps to get everything working on macOS.

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

macOS comes with Python 2 which is outdated. Install Python 3 via Homebrew:

```bash
brew install python
```

Verify:
```bash
python3 --version
```

You should see Python 3.11 or higher.

### Step 3 — Install Required Python Libraries

The app depends on the `cryptography` library. Install it with pip:

```bash
pip3 install cryptography --break-system-packages
```

> **Note:** The `--break-system-packages` flag is required on macOS with newer versions of Python (3.11+). This is normal — it simply bypasses a warning and installs the package correctly.

Verify it installed:
```bash
pip3 show cryptography
```

### Step 4 — Set Up Your Project Folder

Create a dedicated folder for the app:

```bash
mkdir -p ~/Desktop/code/projects/decryptor
cd ~/Desktop/code/projects/decryptor
```

Place `main.py` inside that folder.

### Step 5 — Run the App

```bash
cd ~/Desktop/code/projects/decryptor
python3 main.py
```

---

## How to Use

### Basic Flow

1. Run `python3 main.py`
2. The app scans your Desktop and shows any `.enc` files as a numbered list
3. Select the file you want to decrypt
4. Select the algorithm that was used to encrypt it (must match what the Encryptor used)
5. Enter your password or key file name depending on how it was encrypted
6. The decrypted output is saved to your Desktop

### Password-Based Decryption

If the file was encrypted with a password, select option `1` when asked about the key method and type the same password used during encryption. The salt is embedded in the encrypted file automatically — you just need the password.

### Key File-Based Decryption

If the file was encrypted with a key file, select option `2` and enter the key file name. Key files are stored in:

```
~/Desktop/keys/
```

The default key file names follow this pattern:

| Algorithm | Default Key File Name |
|-----------|-----------------------|
| AES-256-CBC | `aes_256_cbc.key` |
| AES-256-GCM | `aes_256_gcm.key` |
| ChaCha20-Poly1305 | `chacha20_poly1305.key` |
| Fernet | `fernet.key` |

### RSA Decryption

RSA requires the **private key** `.pem` file that was generated during encryption. The private key is stored at:

```
~/Desktop/keys/<keyname>_private.pem
```

When prompted, enter the base name you used when encrypting (e.g. if you used `mykeys`, enter `mykeys`).

> **Warning:** If you lose the private key file, RSA-encrypted data cannot be recovered. There is no workaround.

---

## File & Folder Structure

```
~/Desktop/
    keys/                          ← key files live here
        aes_256_gcm.key
        chacha20_poly1305.key
        rsa_keys_private.pem
        rsa_keys_public.pem
        ...

~/Desktop/code/projects/
    encryptor/
        main.py                    ← creates encrypted files
    decryptor/
        main.py                    ← this app — reverses encryption
```

---

## Using Encryptor + Decryptor Together

These two apps are designed to work as a pair:

1. Open the **Encryptor** and encrypt a file or text
2. The encrypted `.enc` file is saved to your Desktop
3. Open the **Decryptor** — it will automatically find the `.enc` file
4. Select the same algorithm you used to encrypt
5. Enter the same password or key file name
6. Decrypted output is saved to your Desktop

---

## Troubleshooting

**"Wrong password or corrupted file"**
You entered the wrong password, or the encrypted file was modified after encryption. AES-GCM and ChaCha20 include tamper detection — even a single changed byte will cause decryption to fail.

**"Key file not found"**
The key file is missing from `~/Desktop/keys/`. Key files must be present to decrypt. If the key file is gone, the data cannot be recovered.

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

**App closes immediately or shows a traceback**
Make sure you are running Python 3.11 or higher:
```bash
python3 --version
```
If you see 3.9 or lower, upgrade with `brew upgrade python`.

---

## Dependencies Summary

| Dependency | Install Command | Purpose |
|------------|-----------------|---------|
| Homebrew | See Step 1 above | macOS package manager |
| Python 3.11+ | `brew install python` | Required to run the app |
| cryptography | `pip3 install cryptography --break-system-packages` | All encryption/decryption algorithms |

No other installs, brews, or dependencies are required.

---

## Security Notes

- Password-based keys are derived using **PBKDF2 with SHA-256 and 480,000 iterations** — this is intentionally slow to resist brute force attacks
- The salt and nonce are embedded in every encrypted file automatically — you only need the password or key file to decrypt
- AES-256-GCM and ChaCha20-Poly1305 include **authentication tags** that detect any tampering with the encrypted file
- XOR and Caesar ciphers are included for educational purposes only — do not use them for anything sensitive
- RSA private key files are stored unencrypted on disk — protect them accordingly
