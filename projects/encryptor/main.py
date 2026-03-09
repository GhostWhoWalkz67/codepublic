import os
import base64
import struct
import sys
import secrets
import tarfile
import tempfile

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend

# =============================================================
#  PATHS & CONSTANTS
# =============================================================

DESKTOP              = os.path.expanduser("~/Desktop")
KEYS_DIR             = os.path.join(DESKTOP, "keys")
LARGE_FILE_THRESHOLD = 250 * 1024 * 1024   # 250 MB
CHUNK_SIZE           = 64 * 1024            # 64 KB streaming chunks

# =============================================================
#  ALGORITHM REGISTRIES
# =============================================================

ALGORITHMS = {
    "1": {"name": "AES-256-CBC",       "key_method": "password_or_file", "desc": "Industry standard block cipher. Fast and widely supported."},
    "2": {"name": "AES-256-GCM",       "key_method": "password_or_file", "desc": "AES with authentication tag. Detects tampering."},
    "3": {"name": "ChaCha20-Poly1305", "key_method": "password_or_file", "desc": "Modern stream cipher. Used in TLS and mobile apps."},
    "4": {"name": "Fernet",            "key_method": "password_or_file", "desc": "Simple and safe symmetric encryption."},
    "5": {"name": "RSA-2048",          "key_method": "keyfile_only",     "desc": "Asymmetric public/private key pair. Best for short text."},
    "6": {"name": "XOR Cipher",        "key_method": "password_only",    "desc": "Classic educational cipher. Not secure for real use."},
    "7": {"name": "Caesar Cipher",     "key_method": "shift_only",       "desc": "Classic letter-shift cipher. Educational only."},
}

LARGE_ALGORITHMS = {
    "1": {"name": "AES-256-CBC",       "key_method": "password_or_file", "desc": "Fast, universal. Recommended for large files."},
    "2": {"name": "AES-256-GCM",       "key_method": "password_or_file", "desc": "AES with per-chunk authentication. Detects tampering."},
    "3": {"name": "ChaCha20-Poly1305", "key_method": "password_or_file", "desc": "Fastest option. Excellent for large video files."},
}

# =============================================================
#  RANDOM FILENAME GENERATOR
# =============================================================

def generate_output_filename():
    """Generate a random 10-character hex filename with no extension."""
    return secrets.token_hex(5)   # 5 bytes = 10 hex chars

# =============================================================
#  FILENAME BUNDLING
#  The original filename is packed INTO the plaintext BEFORE
#  encryption so it is fully hidden inside the encrypted blob.
#  Format of plaintext passed to encrypt functions:
#    [4B: name length][name bytes][original file bytes]
#  Nothing readable exists outside the encrypted payload.
# =============================================================

def bundle_filename_with_plaintext(original_filename, plaintext):
    """Prepend filename into plaintext so it gets encrypted together."""
    name_bytes = original_filename.encode("utf-8")
    length     = struct.pack(">I", len(name_bytes))
    return length + name_bytes + plaintext

# =============================================================
#  UTILITIES
# =============================================================

def ensure_keys_dir():
    os.makedirs(KEYS_DIR, exist_ok=True)

def derive_key(password, salt, length=32):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=480000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def save_output(data, filename):
    filepath = os.path.join(DESKTOP, filename)
    with open(filepath, "wb") as f:
        f.write(data)
    return filepath

def _load_or_generate_keyfile(keyfile, length=32):
    ensure_keys_dir()
    path = os.path.join(KEYS_DIR, keyfile)
    if os.path.exists(path):
        print(f"\n  [+] Using existing key file: {path}")
        with open(path, "rb") as f:
            return f.read()[:length]
    else:
        key = os.urandom(length)
        with open(path, "wb") as f:
            f.write(key)
        print(f"\n  [+] New key file saved to: {path}")
        return key

def format_size(num_bytes):
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"

def progress_bar(current, total, width=40):
    pct    = current / total if total > 0 else 0
    filled = int(width * pct)
    bar    = "█" * filled + "░" * (width - filled)
    sys.stdout.write(f"\r  [{bar}] {pct*100:.1f}%  {format_size(current)} / {format_size(total)}")
    sys.stdout.flush()

# =============================================================
#  DISPLAY
# =============================================================

def print_banner():
    print("\n" + "=" * 55)
    print("  ENCRYPTOR")
    print("=" * 55)

def print_algorithms(large=False):
    algs  = LARGE_ALGORITHMS if large else ALGORITHMS
    label = "SELECT ALGORITHM  (Large File Mode)" if large else "SELECT ALGORITHM"
    print("\n" + "=" * 55)
    print(f"  {label}")
    print("=" * 55 + "\n")
    for key, alg in algs.items():
        print(f"  {key}. {alg['name']}")
        print(f"     {alg['desc']}\n")

def print_success(filepath, algo_name, key_hint, original_filename):
    print("\n" + "=" * 55)
    print("  ENCRYPTION COMPLETE")
    print("=" * 55)
    print(f"\n  Algorithm      : {algo_name}")
    print(f"  Original file  : {original_filename}  (embedded inside, invisible externally)")
    print(f"  Saved as       : {os.path.basename(filepath)}  (random name, no extension)")
    print(f"  Full path      : {filepath}")
    print(f"  File size      : {format_size(os.path.getsize(filepath))}")
    print(f"  Key info       : {key_hint}")
    print(f"\n  [!] Keep your key safe — without it decryption is impossible.")
    print(f"  [!] The original filename will be restored automatically on decryption.")
    print("=" * 55 + "\n")

# =============================================================
#  INPUT HELPERS
# =============================================================

def ask_input_type():
    print("\n  What would you like to encrypt?")
    print("  1. Text    (type it in)")
    print("  2. File    (single file from Desktop)")
    print("  3. Folder  (entire folder and all its contents)")
    return input("\n  Enter choice: ").strip()

def get_plaintext():
    text = input("\n  Enter text to encrypt: ").strip()
    if not text:
        print("  [!] No text entered.")
        return None, None
    return text.encode(), "text_input.txt"

def get_file_path():
    files = sorted([
        f for f in os.listdir(DESKTOP)
        if os.path.isfile(os.path.join(DESKTOP, f)) and not f.startswith(".")
    ])
    if not files:
        print("\n  [!] No files found on Desktop.")
        return None, None
    print(f"\n  Files on Desktop:\n")
    for i, f in enumerate(files, 1):
        size = format_size(os.path.getsize(os.path.join(DESKTOP, f)))
        print(f"  {i}. {f}  ({size})")
    choice = input("\n  Select file number: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(files):
            return os.path.join(DESKTOP, files[idx]), files[idx]
    except (ValueError, IndexError):
        pass
    print("  [!] Invalid selection.")
    return None, None

def ask_key_method(alg_info):
    method = alg_info["key_method"]
    if method == "password_only":  return "password"
    if method == "shift_only":     return "shift"
    if method == "keyfile_only":   return "keyfile"
    print("\n  How would you like to provide the encryption key?")
    print("  1. Password  (you type a passphrase)")
    print("  2. Key file  (app generates a reusable key file)")
    choice = input("\n  Enter choice: ").strip()
    return "password" if choice == "1" else "keyfile"

def gather_key_info(alg):
    key_method = ask_key_method(alg)
    password = keyfile = shift = None
    key_hint = ""

    if key_method == "password":
        password = input("\n  Enter encryption password: ").strip()
        if not password:
            print("  [!] No password entered.")
            return None, None, None, None
        key_hint = "Password-based (PBKDF2 derived key)"

    elif key_method == "keyfile":
        default_name = f"{alg['name'].lower().replace('-','_').replace(' ','_')}.key"
        fname   = input(f"\n  Key file name (default: {default_name}): ").strip()
        keyfile = fname if fname else default_name
        key_hint = f"Key file: ~/Desktop/keys/{keyfile}"

    elif key_method == "shift":
        try:
            shift = int(input("\n  Enter Caesar shift number (1-25): ").strip())
        except ValueError:
            print("  [!] Invalid shift number.")
            return None, None, None, None
        key_hint = f"Caesar shift: {shift}"

    return password, keyfile, shift, key_hint


# =============================================================
#  FOLDER HELPERS
# =============================================================

def get_folder_path():
    """List all folders on Desktop and let the user pick one."""
    folders = sorted([
        f for f in os.listdir(DESKTOP)
        if os.path.isdir(os.path.join(DESKTOP, f)) and not f.startswith(".")
        and f != "keys"
    ])
    if not folders:
        print("\n  [!] No folders found on Desktop.")
        return None, None
    print(f"\n  Folders on Desktop:\n")
    for i, f in enumerate(folders, 1):
        total = get_folder_size(os.path.join(DESKTOP, f))
        print(f"  {i}. {f}  ({format_size(total)})")
    choice = input("\n  Select folder number: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(folders):
            return os.path.join(DESKTOP, folders[idx]), folders[idx]
    except (ValueError, IndexError):
        pass
    print("  [!] Invalid selection.")
    return None, None

def get_folder_size(folder_path):
    """Calculate total uncompressed size of all files in a folder tree."""
    total = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total

def tar_folder(folder_path, folder_name):
    """
    Bundle an entire folder tree into a tar archive.
    Returns path to temp tar file — caller must delete it when done.
    Under 250MB: write to a temp file, return path.
    """
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".tar")
    tmp.close()
    print(f"\n  [+] Archiving folder contents...")
    with tarfile.open(tmp.name, "w") as tar:
        tar.add(folder_path, arcname=folder_name)
    print(f"  [+] Archive size: {format_size(os.path.getsize(tmp.name))}")
    return tmp.name

def print_folder_success(filepath, algo_name, key_hint, folder_name, file_count, total_size):
    print("\n" + "=" * 55)
    print("  ENCRYPTION COMPLETE")
    print("=" * 55)
    print(f"\n  Algorithm      : {algo_name}")
    print(f"  Folder         : {folder_name}  (embedded inside, invisible externally)")
    print(f"  Contents       : {file_count} files  ({format_size(total_size)} uncompressed)")
    print(f"  Saved as       : {os.path.basename(filepath)}  (random name, no extension)")
    print(f"  Full path      : {filepath}")
    print(f"  Encrypted size : {format_size(os.path.getsize(filepath))}")
    print(f"  Key info       : {key_hint}")
    print(f"\n  [!] Keep your key safe — without it decryption is impossible.")
    print(f"  [!] The original folder and all contents will be fully restored on decryption.")
    print("=" * 55 + "\n")

def count_files(folder_path):
    count = 0
    for _, _, files in os.walk(folder_path):
        count += len(files)
    return count

# =============================================================
#  STANDARD ENCRYPTION
# =============================================================

def encrypt_aes_cbc(plaintext, password=None, keyfile=None):
    salt = os.urandom(16)
    iv   = os.urandom(16)
    key  = _load_or_generate_keyfile(keyfile) if keyfile else derive_key(password, salt)
    pad_len   = 16 - (len(plaintext) % 16)
    plaintext += bytes([pad_len] * pad_len)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    enc = cipher.encryptor()
    return salt + iv + enc.update(plaintext) + enc.finalize()

def encrypt_aes_gcm(plaintext, password=None, keyfile=None):
    salt  = os.urandom(16)
    nonce = os.urandom(12)
    key   = _load_or_generate_keyfile(keyfile) if keyfile else derive_key(password, salt)
    return salt + nonce + AESGCM(key).encrypt(nonce, plaintext, None)

def encrypt_chacha20(plaintext, password=None, keyfile=None):
    salt  = os.urandom(16)
    nonce = os.urandom(12)
    key   = _load_or_generate_keyfile(keyfile) if keyfile else derive_key(password, salt)
    return salt + nonce + ChaCha20Poly1305(key).encrypt(nonce, plaintext, None)

def encrypt_fernet(plaintext, password=None, keyfile=None):
    if keyfile:
        ensure_keys_dir()
        fkey_path = os.path.join(KEYS_DIR, keyfile)
        if os.path.exists(fkey_path):
            with open(fkey_path, "rb") as f:
                fernet_key = f.read().strip()
        else:
            fernet_key = Fernet.generate_key()
            with open(fkey_path, "wb") as f:
                f.write(fernet_key)
            print(f"\n  [+] Fernet key saved to: {fkey_path}")
        return Fernet(fernet_key).encrypt(plaintext)
    else:
        salt = os.urandom(16)
        key  = derive_key(password, salt, length=32)
        fernet_key = base64.urlsafe_b64encode(key)
        token = Fernet(fernet_key).encrypt(plaintext)
        return b"SALTPFX:" + base64.urlsafe_b64encode(salt) + b":" + token

def encrypt_rsa(plaintext, keyfile_base):
    ensure_keys_dir()
    priv_path = os.path.join(KEYS_DIR, f"{keyfile_base}_private.pem")
    pub_path  = os.path.join(KEYS_DIR, f"{keyfile_base}_public.pem")
    if os.path.exists(pub_path):
        print(f"\n  [+] Using existing public key: {pub_path}")
        with open(pub_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
    else:
        print("\n  [+] Generating RSA-2048 key pair...")
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        public_key = private_key.public_key()
        with open(priv_path, "wb") as f:
            f.write(private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption()
            ))
        with open(pub_path, "wb") as f:
            f.write(public_key.public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        print(f"  [+] Private key → {priv_path}")
        print(f"  [+] Public  key → {pub_path}")
        print(f"\n  [!] Guard your private key — it is the ONLY way to decrypt.")
    if len(plaintext) > 190:
        print("\n  [!] RSA can only encrypt up to ~190 bytes of text directly.")
        print("  [!] For larger files use AES-256-GCM or ChaCha20 instead.\n")
        return None
    return public_key.encrypt(
        plaintext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

def encrypt_xor(plaintext, password):
    key = password.encode()
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(plaintext)])

def encrypt_caesar(plaintext, shift):
    result = []
    for char in plaintext.decode(errors="ignore"):
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            result.append(chr((ord(char) - base + shift) % 26 + base))
        else:
            result.append(char)
    return "".join(result).encode()

# =============================================================
#  LARGE FILE STREAMING ENCRYPTION
# =============================================================

def stream_encrypt_aes_cbc(in_path, out_path, original_filename, password=None, keyfile=None):
    salt      = os.urandom(16)
    key       = _load_or_generate_keyfile(keyfile) if keyfile else derive_key(password, salt)
    file_size = os.path.getsize(in_path)
    print(f"\n  [+] Encrypting {format_size(file_size)} with AES-256-CBC...\n")
    with open(in_path, "rb") as fin, open(out_path, "wb") as fout:
        # Write only the salt in plaintext — everything else is encrypted
        fout.write(salt)
        # Encrypt filename as the very first chunk — fully hidden
        name_chunk = bundle_filename_with_plaintext(original_filename, b"")
        pad_len = 16 - (len(name_chunk) % 16)
        name_chunk += bytes([pad_len] * pad_len)
        iv     = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        enc    = cipher.encryptor()
        ec     = enc.update(name_chunk) + enc.finalize()
        fout.write(b"NAMECHUNK")
        fout.write(iv)
        fout.write(struct.pack(">I", len(ec)))
        fout.write(ec)
        processed = 0
        while True:
            chunk = fin.read(CHUNK_SIZE)
            if not chunk:
                break
            pad_len = 16 - (len(chunk) % 16)
            chunk  += bytes([pad_len] * pad_len)
            iv      = os.urandom(16)
            cipher  = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            enc     = cipher.encryptor()
            ec      = enc.update(chunk) + enc.finalize()
            fout.write(b"DATACHUNK")
            fout.write(iv)
            fout.write(struct.pack(">I", len(ec)))
            fout.write(ec)
            processed += len(chunk)
            progress_bar(min(processed, file_size), file_size)
    print(f"\n  [+] Done!")

def stream_encrypt_aes_gcm(in_path, out_path, original_filename, password=None, keyfile=None):
    salt      = os.urandom(16)
    key       = _load_or_generate_keyfile(keyfile) if keyfile else derive_key(password, salt)
    file_size = os.path.getsize(in_path)
    aesgcm    = AESGCM(key)
    print(f"\n  [+] Encrypting {format_size(file_size)} with AES-256-GCM...\n")
    with open(in_path, "rb") as fin, open(out_path, "wb") as fout:
        fout.write(salt)
        # Encrypt filename as first chunk
        name_chunk = bundle_filename_with_plaintext(original_filename, b"")
        nonce = os.urandom(12)
        ec    = aesgcm.encrypt(nonce, name_chunk, None)
        fout.write(b"NAMECHUNK")
        fout.write(nonce)
        fout.write(struct.pack(">I", len(ec)))
        fout.write(ec)
        processed = 0
        while True:
            chunk = fin.read(CHUNK_SIZE)
            if not chunk:
                break
            nonce = os.urandom(12)
            ec    = aesgcm.encrypt(nonce, chunk, None)
            fout.write(b"DATACHUNK")
            fout.write(nonce)
            fout.write(struct.pack(">I", len(ec)))
            fout.write(ec)
            processed += len(chunk)
            progress_bar(min(processed, file_size), file_size)
    print(f"\n  [+] Done!")

def stream_encrypt_chacha20(in_path, out_path, original_filename, password=None, keyfile=None):
    salt      = os.urandom(16)
    key       = _load_or_generate_keyfile(keyfile) if keyfile else derive_key(password, salt)
    file_size = os.path.getsize(in_path)
    chacha    = ChaCha20Poly1305(key)
    print(f"\n  [+] Encrypting {format_size(file_size)} with ChaCha20-Poly1305...\n")
    with open(in_path, "rb") as fin, open(out_path, "wb") as fout:
        fout.write(salt)
        # Encrypt filename as first chunk
        name_chunk = bundle_filename_with_plaintext(original_filename, b"")
        nonce = os.urandom(12)
        ec    = chacha.encrypt(nonce, name_chunk, None)
        fout.write(b"NAMECHUNK")
        fout.write(nonce)
        fout.write(struct.pack(">I", len(ec)))
        fout.write(ec)
        processed = 0
        while True:
            chunk = fin.read(CHUNK_SIZE)
            if not chunk:
                break
            nonce = os.urandom(12)
            ec    = chacha.encrypt(nonce, chunk, None)
            fout.write(b"DATACHUNK")
            fout.write(nonce)
            fout.write(struct.pack(">I", len(ec)))
            fout.write(ec)
            processed += len(chunk)
            progress_bar(min(processed, file_size), file_size)
    print(f"\n  [+] Done!")

# =============================================================
#  MAIN ENCRYPTION FLOWS
# =============================================================

def run_standard_encryption(algo_choice, plaintext, original_filename):
    alg = ALGORITHMS[algo_choice]
    password, keyfile, shift, key_hint = gather_key_info(alg)
    if key_hint is None:
        return

    # Bundle filename INTO plaintext before encryption — fully hidden inside blob
    bundled = bundle_filename_with_plaintext(original_filename, plaintext)

    ciphertext = None
    if   algo_choice == "1": ciphertext = encrypt_aes_cbc(bundled,  password=password, keyfile=keyfile)
    elif algo_choice == "2": ciphertext = encrypt_aes_gcm(bundled,  password=password, keyfile=keyfile)
    elif algo_choice == "3": ciphertext = encrypt_chacha20(bundled, password=password, keyfile=keyfile)
    elif algo_choice == "4": ciphertext = encrypt_fernet(bundled,   password=password, keyfile=keyfile)
    elif algo_choice == "5":
        kb = input("\n  Base name for RSA key pair (e.g. 'mykeys'): ").strip() or "rsa_keys"
        ciphertext = encrypt_rsa(bundled, kb)
        key_hint = f"RSA key pair: ~/Desktop/keys/{kb}_private/public.pem"
    elif algo_choice == "6": ciphertext = encrypt_xor(bundled,    password)
    elif algo_choice == "7": ciphertext = encrypt_caesar(bundled, shift)

    if not ciphertext:
        print("\n  [!] Encryption failed.\n")
        return

    out_name = generate_output_filename()
    filepath = save_output(ciphertext, out_name)
    print_success(filepath, alg["name"], key_hint, original_filename)


def run_large_file_encryption(algo_choice, in_path, original_filename):
    alg = LARGE_ALGORITHMS[algo_choice]
    password, keyfile, shift, key_hint = gather_key_info(alg)
    if key_hint is None:
        return

    out_name = generate_output_filename()
    out_path = os.path.join(DESKTOP, out_name)

    if   algo_choice == "1": stream_encrypt_aes_cbc(in_path,    out_path, original_filename, password=password, keyfile=keyfile)
    elif algo_choice == "2": stream_encrypt_aes_gcm(in_path,    out_path, original_filename, password=password, keyfile=keyfile)
    elif algo_choice == "3": stream_encrypt_chacha20(in_path,   out_path, original_filename, password=password, keyfile=keyfile)

    print_success(out_path, alg["name"], key_hint, original_filename)


# =============================================================
#  FOLDER ENCRYPTION FLOW
# =============================================================

def run_folder_encryption(folder_path, folder_name):
    """Tar the folder, check size, then encrypt as a single blob."""
    total_size = get_folder_size(folder_path)
    file_count = count_files(folder_path)

    print(f"\n  [+] Folder   : {folder_name}")
    print(f"  [+] Files    : {file_count}")
    print(f"  [+] Total    : {format_size(total_size)}")

    # Tar the folder to a temp file regardless of size
    tar_path = tar_folder(folder_path, folder_name)

    try:
        tar_size = os.path.getsize(tar_path)

        if tar_size > LARGE_FILE_THRESHOLD:
            print(f"\n  [!] Large folder detected ({format_size(tar_size)} archived).")
            print(f"  [!] Folders over 250MB use streaming encryption mode.")
            print_algorithms(large=True)
            algo_choice = input("  Enter algorithm number: ").strip()
            if algo_choice not in LARGE_ALGORITHMS:
                print("  [!] Invalid algorithm.")
                return
            alg = LARGE_ALGORITHMS[algo_choice]
            password, keyfile, shift, key_hint = gather_key_info(alg)
            if key_hint is None:
                return
            # Use folder name as the embedded label so decryptor knows it's a folder
            label = f"FOLDER:{folder_name}"
            out_name = generate_output_filename()
            out_path = os.path.join(DESKTOP, out_name)
            if   algo_choice == "1": stream_encrypt_aes_cbc(tar_path,    out_path, label, password=password, keyfile=keyfile)
            elif algo_choice == "2": stream_encrypt_aes_gcm(tar_path,    out_path, label, password=password, keyfile=keyfile)
            elif algo_choice == "3": stream_encrypt_chacha20(tar_path,   out_path, label, password=password, keyfile=keyfile)
            print_folder_success(out_path, alg["name"], key_hint, folder_name, file_count, total_size)

        else:
            with open(tar_path, "rb") as f:
                tar_bytes = f.read()
            print_algorithms(large=False)
            algo_choice = input("  Enter algorithm number: ").strip()
            if algo_choice not in ALGORITHMS:
                print("  [!] Invalid algorithm.")
                return
            alg = ALGORITHMS[algo_choice]
            password, keyfile, shift, key_hint = gather_key_info(alg)
            if key_hint is None:
                return
            label   = f"FOLDER:{folder_name}"
            bundled = bundle_filename_with_plaintext(label, tar_bytes)
            ciphertext = None
            if   algo_choice == "1": ciphertext = encrypt_aes_cbc(bundled,  password=password, keyfile=keyfile)
            elif algo_choice == "2": ciphertext = encrypt_aes_gcm(bundled,  password=password, keyfile=keyfile)
            elif algo_choice == "3": ciphertext = encrypt_chacha20(bundled, password=password, keyfile=keyfile)
            elif algo_choice == "4": ciphertext = encrypt_fernet(bundled,   password=password, keyfile=keyfile)
            elif algo_choice == "5":
                kb = input("\n  Base name for RSA key pair (e.g. 'mykeys'): ").strip() or "rsa_keys"
                ciphertext = encrypt_rsa(bundled, kb)
                key_hint = f"RSA key pair: ~/Desktop/keys/{kb}_private/public.pem"
            elif algo_choice == "6": ciphertext = encrypt_xor(bundled,    password)
            elif algo_choice == "7": ciphertext = encrypt_caesar(bundled, shift)
            if not ciphertext:
                print("\n  [!] Encryption failed.\n")
                return
            out_name = generate_output_filename()
            filepath = save_output(ciphertext, out_name)
            print_folder_success(filepath, alg["name"], key_hint, folder_name, file_count, total_size)

    finally:
        # Always clean up temp tar file
        if os.path.exists(tar_path):
            os.remove(tar_path)

# =============================================================
#  MAIN
# =============================================================

def main():
    print_banner()

    while True:
        input_type = ask_input_type()

        if input_type == "1":
            plaintext, original_filename = get_plaintext()
            if not plaintext:
                continue
            print_algorithms(large=False)
            algo_choice = input("  Enter algorithm number: ").strip()
            if algo_choice not in ALGORITHMS:
                print("  [!] Invalid algorithm.")
                continue
            run_standard_encryption(algo_choice, plaintext, original_filename)

        elif input_type == "2":
            in_path, original_filename = get_file_path()
            if not in_path:
                continue
            file_size = os.path.getsize(in_path)

            if file_size > LARGE_FILE_THRESHOLD:
                print(f"\n  [!] Large file detected: {format_size(file_size)}")
                print(f"  [!] Files over 250MB use streaming encryption mode.")
                print_algorithms(large=True)
                algo_choice = input("  Enter algorithm number: ").strip()
                if algo_choice not in LARGE_ALGORITHMS:
                    print("  [!] Invalid algorithm.")
                    continue
                run_large_file_encryption(algo_choice, in_path, original_filename)
            else:
                with open(in_path, "rb") as f:
                    plaintext = f.read()
                print_algorithms(large=False)
                algo_choice = input("  Enter algorithm number: ").strip()
                if algo_choice not in ALGORITHMS:
                    print("  [!] Invalid algorithm.")
                    continue
                run_standard_encryption(algo_choice, plaintext, original_filename)

        elif input_type == "3":
            folder_path, folder_name = get_folder_path()
            if not folder_path:
                continue
            run_folder_encryption(folder_path, folder_name)

        else:
            print("  [!] Invalid choice.")
            continue

        again = input("  Encrypt something else? (y/n): ").strip().lower()
        if again != "y":
            print("\n  Goodbye!\n")
            break


if __name__ == "__main__":
    main()


#This product was coded by

  #  ________ .__                       __    __      __ .__              __      __         .__    __
  #/  _____/ |  |__    ____    _______/  |_ /  \    /  \|  |__    ____  /  \    /  \_____   |  |  |  | __________
 #/   \  ___ |  |  \  /  _ \  /  ___/\   __\\   \/\/   /|  |  \  /  _ \ \   \/\/   /\__  \  |  |  |  |/ /\___   /
#\    \_\  \|   Y  \(  <_> ) \___ \  |  |   \        / |   Y  \(  <_> ) \        /  / __ \_|  |__|    <  /    /
#  ______  /|___|  / \____/ /____  > |__|    \__/\  /  |___|  / \____/   \__/\  /  (____  /|____/|__|_ \/_____ \
##       \/      \/              \/               \/        \/                \/        \/            \/      \/

#Follow GhostWhoWalkz on her journey from trailer park kid, to air force pilot, to burnt out trial attorney who is now teaching herself how to code.
# https://www.github.com/GhostWhoWalkz67
# https://forgottenfieldnotes.blogspot.com/