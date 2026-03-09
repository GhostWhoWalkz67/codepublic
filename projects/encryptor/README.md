# Encryptor
### By GhostWhoWalkz

Encrypts text, single files, or entire folders from your Desktop. Every encrypted output is saved as a **random 10-character hex filename with no extension** — the original name, file type, and folder structure are all bundled inside the encrypted blob and completely invisible externally. Nothing is stored outside the encrypted file.

---

## What It Can Encrypt

| Input Type | Description |
|-----------|-------------|
| Text | Type any string directly into the terminal |
| Single file | Any file type — images, videos, PDFs, code, archives, executables |
| Folder | Entire folder including all subfolders and their contents |

---

## Algorithms

### Standard Mode (files and folders under 250MB)

All 7 algorithms are available:

| # | Algorithm | Key Method | Notes |
|---|-----------|------------|-------|
| 1 | AES-256-CBC | Password or key file | Fast, universal, industry standard |
| 2 | AES-256-GCM | Password or key file | Authenticated — detects tampering |
| 3 | ChaCha20-Poly1305 | Password or key file | Modern, fast, used in TLS |
| 4 | Fernet | Password or key file | Simple symmetric encryption |
| 5 | RSA-2048 | Key file only | Asymmetric — best for short text only (190 byte limit) |
| 6 | XOR Cipher | Password only | Educational only — not secure for real use |
| 7 | Caesar Cipher | Shift number | Educational only — not secure for real use |

### Large File Mode (files and folders over 250MB)

Only streaming-capable algorithms are available:

| # | Algorithm | Notes |
|---|-----------|-------|
| 1 | AES-256-CBC | Fast, universal |
| 2 | AES-256-GCM | Authenticated per chunk |
| 3 | ChaCha20-Poly1305 | Fastest — recommended for large video files |

Large files are processed in 64KB chunks so memory usage stays flat regardless of file size. A 50GB video uses the same ~64KB of RAM as a 1MB photo.

---

## How Privacy Works

Everything about the original file is hidden inside the encrypted payload:

- The **output filename** is a random 10-character hex string (e.g. `a3f8c291b4`) with no extension
- The **original filename** is bundled into the plaintext *before* encryption — not stored as a header
- The **file type** is completely invisible — no `.enc`, no extension of any kind
- For **folders**, every subfolder name and every filename inside are encrypted along with the contents
- **Nothing is logged externally** — no database, no mapping file, no record of what was encrypted

Opening the output file in a hex editor shows pure noise from byte 1. There is no readable metadata anywhere.

---

## Key Methods

**Password** — you type a passphrase. The app derives a 256-bit key using PBKDF2 with 480,000 iterations of SHA-256 and a random 16-byte salt. The salt is embedded in the file so the same password always works on decryption.

**Key file** — the app generates a random 32-byte key file and saves it to `~/Desktop/keys/`. Faster than password-based decryption. Keep this file safe — it is the only way to decrypt.

**RSA key pair** — generates a `_private.pem` and `_public.pem` in `~/Desktop/keys/`. The public key encrypts, the private key decrypts. Hard limit of ~190 bytes of input data.

---

## Folder Encryption

When you choose **Folder**, the app:

1. Walks the entire folder tree and calculates the total uncompressed size
2. Bundles everything into a `.tar` archive (preserving all subfolder structure)
3. Checks total size against the 250MB threshold
4. Encrypts the archive as a single blob — one random-named output file
5. Cleans up the temporary archive automatically

The entire folder — every filename, every subfolder name, all file contents — is hidden inside the single encrypted output file.

---

## macOS Setup

```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python

# Install dependencies
pip3 install bcrypt passlib cryptography --break-system-packages
```

---

## Usage

```bash
cd ~/Desktop/code/projects/encryptor
python3 main.py
```

Then follow the prompts:

```
What would you like to encrypt?
  1. Text    (type it in)
  2. File    (single file from Desktop)
  3. Folder  (entire folder and all its contents)
```

---

## Output

Every encrypted file is saved to your Desktop as a random hex name with no extension:

```
~/Desktop/a3f8c291b4
~/Desktop/f7d2190c33
```

The success screen tells you the random name, the original name (which is now hidden inside), and the key info. Write down or copy the random filename if you need to find it again — nothing else on disk identifies it.

---

## Notes

- The `~/Desktop/keys/` folder holds all key files and RSA key pairs — back this up
- If you lose your password or key file, the encrypted data is unrecoverable
- Encrypting a file that is already encrypted works fine — you just need to decrypt twice
- macOS extended attributes (Finder tags, Spotlight comments) are not preserved — only file content is encrypted
- The 250MB threshold applies to the **total uncompressed size** for folders, not individual files inside

---

## Dependencies

```
pip3 install cryptography --break-system-packages
```

Python's built-in `tarfile`, `struct`, `os`, `secrets`, `hashlib` handle everything else.
