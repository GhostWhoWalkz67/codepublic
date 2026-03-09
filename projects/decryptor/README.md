# Decryptor
### By GhostWhoWalkz

Decrypts files and folders that were encrypted with the Encryptor app. Automatically detects whether the encrypted file contains a single file or an entire folder, and restores everything — original filename, file type, and full folder structure — exactly as it was before encryption.

---

## What It Can Decrypt

| Encrypted Content | What Gets Restored |
|------------------|--------------------|
| Encrypted text | `.txt` file on Desktop with original content |
| Encrypted single file | Original file with original filename and extension |
| Encrypted folder | Full folder tree restored to Desktop |

---

## How to Find Encrypted Files

Encrypted files have **random 10-character hex names and no extension** (e.g. `a3f8c291b4`). The app lists all files on your Desktop and marks likely encrypted ones:

```
  Files on Desktop:

  1. a3f8c291b4   (1.2 MB)    ← likely encrypted
  2. f7d2190c33   (847.3 MB)  ← likely encrypted
  3. notes.txt    (4.1 KB)
  4. photo.jpg    (3.8 MB)
```

You pick the file, select the algorithm that was used to encrypt it, enter your password or key file, and the app does the rest.

---

## Algorithms

### Standard Mode (encrypted files under 250MB)

| # | Algorithm | Key Method |
|---|-----------|------------|
| 1 | AES-256-CBC | Password or key file |
| 2 | AES-256-GCM | Password or key file |
| 3 | ChaCha20-Poly1305 | Password or key file |
| 4 | Fernet | Password or key file |
| 5 | RSA-2048 | Key file only |
| 6 | XOR Cipher | Password only |
| 7 | Caesar Cipher | Shift number |

### Large File Mode (encrypted files over 250MB)

Automatically used for large files — processes in 64KB chunks:

| # | Algorithm |
|---|-----------|
| 1 | AES-256-CBC |
| 2 | AES-256-GCM |
| 3 | ChaCha20-Poly1305 |

---

## Folder Decryption

When the encrypted file contains a folder, the app automatically detects it after decryption and extracts the full folder tree to your Desktop.

If a folder with the same name already exists on your Desktop, it asks what you want to do:

```
  [!] A folder named 'my_project' already exists on your Desktop.
  [!] What would you like to do?
  1. Overwrite it
  2. Rename the restored folder
  3. Cancel
```

---

## Output Filenames

The original filename is embedded inside the encrypted file and restored automatically on decryption. No `_decrypted` suffix is added — `vacation.jpg` comes back as `vacation.jpg`, `project_files/` comes back as `project_files/`.

You can override the output name at the prompt if you want to save it under a different name.

---

## Key Methods

**Password** — enter the same passphrase used during encryption. The salt embedded in the file handles the rest automatically.

**Key file** — enter the name of the key file in `~/Desktop/keys/`. The default name is based on the algorithm (e.g. `aes_256_gcm.key`).

**RSA private key** — enter the base name of the key pair. The app looks for `{name}_private.pem` in `~/Desktop/keys/`.

---

## macOS Setup

```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python

# Install dependencies
pip3 install cryptography --break-system-packages
```

---

## Usage

```bash
cd ~/Desktop/code/projects/decryptor
python3 main.py
```

Then follow the prompts:

```
  Files on Desktop:

  1. a3f8c291b4   (1.2 MB)   ← likely encrypted
  2. f7d2190c33   (412.0 KB) ← likely encrypted

  Select file number: 1

  SELECT ALGORITHM USED TO ENCRYPT
  1. AES-256-CBC ...
  ...

  Enter algorithm number: 2
  How was this file encrypted?
  1. Password
  2. Key file

  Enter decryption password: ••••••••

  [+] Original file restored: vacation.jpg
  Output filename (default: vacation.jpg):
```

---

## Troubleshooting

**"Decryption failed — wrong password/key or file was tampered with"**
The password or key file doesn't match what was used to encrypt. Double-check the password and make sure you're selecting the correct algorithm.

**"Key file not found"**
The key file is missing from `~/Desktop/keys/`. If it was deleted, the file cannot be decrypted.

**"Authentication failed on a chunk"** (large files)
The file may have been partially corrupted or modified after encryption. GCM and ChaCha20 detect any tampering down to the byte.

**Output file has no extension**
This can happen with legacy files that were encrypted before the filename-embedding feature. Rename the output file manually with the correct extension.

**Folder not restored correctly**
Make sure you have write permissions to your Desktop and enough free disk space for the uncompressed folder contents.

---

## Notes

- Always select the **same algorithm** that was used during encryption — there is no auto-detection
- The `~/Desktop/keys/` folder must be intact for key-file-based decryption
- AES-256-GCM and ChaCha20-Poly1305 will refuse to decrypt if the file has been tampered with — this is a security feature, not a bug
- Large file mode automatically engages based on the encrypted file size (over 250MB)

---

## Dependencies

```
pip3 install cryptography --break-system-packages
```

Python's built-in `tarfile`, `struct`, `os`, `tempfile` handle everything else.
