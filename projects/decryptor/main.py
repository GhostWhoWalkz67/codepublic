import os
import base64
import struct
import sys
import tarfile
import tempfile

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag

# =============================================================
#  PATHS & CONSTANTS
# =============================================================

DESKTOP              = os.path.expanduser("~/Desktop")
KEYS_DIR             = os.path.join(DESKTOP, "keys")
LARGE_FILE_THRESHOLD = 250 * 1024 * 1024
CHUNK_SIZE           = 64 * 1024

# =============================================================
#  ALGORITHM REGISTRIES
# =============================================================

ALGORITHMS = {
    "1": {"name": "AES-256-CBC",       "key_method": "password_or_file", "desc": "Industry standard block cipher."},
    "2": {"name": "AES-256-GCM",       "key_method": "password_or_file", "desc": "AES with authentication tag."},
    "3": {"name": "ChaCha20-Poly1305", "key_method": "password_or_file", "desc": "Modern stream cipher."},
    "4": {"name": "Fernet",            "key_method": "password_or_file", "desc": "Simple symmetric encryption."},
    "5": {"name": "RSA-2048",          "key_method": "keyfile_only",     "desc": "Asymmetric public/private key pair."},
    "6": {"name": "XOR Cipher",        "key_method": "password_only",    "desc": "Classic XOR cipher."},
    "7": {"name": "Caesar Cipher",     "key_method": "shift_only",       "desc": "Classic letter-shift cipher."},
}

LARGE_ALGORITHMS = {
    "1": {"name": "AES-256-CBC",       "key_method": "password_or_file", "desc": "Fast, universal streaming decryption."},
    "2": {"name": "AES-256-GCM",       "key_method": "password_or_file", "desc": "AES with per-chunk authentication."},
    "3": {"name": "ChaCha20-Poly1305", "key_method": "password_or_file", "desc": "Fastest option for large video files."},
}

# =============================================================
#  FILENAME EXTRACTION
#  The filename is bundled INTO the plaintext before encryption.
#  After decryption we extract it from the front of the result.
#  Format: [4B: name length][name bytes][original file bytes]
# =============================================================

def extract_filename_from_plaintext(plaintext):
    """Extract original filename and file bytes from decrypted plaintext."""
    try:
        name_len = struct.unpack(">I", plaintext[:4])[0]
        if name_len > 512:
            return None, plaintext
        original_filename = plaintext[4:4 + name_len].decode("utf-8")
        file_bytes = plaintext[4 + name_len:]
        return original_filename, file_bytes
    except Exception:
        return None, plaintext


# =============================================================
#  FOLDER DETECTION & EXTRACTION
#  Encrypted folders are identified by the FOLDER: prefix on
#  the embedded label. On decryption the tar is extracted to
#  Desktop and the temp tar file is cleaned up automatically.
# =============================================================

def is_folder_payload(label):
    """Check if decrypted label indicates a folder archive."""
    return label and label.startswith("FOLDER:")

def get_folder_name_from_label(label):
    """Strip the FOLDER: prefix to get the original folder name."""
    return label[len("FOLDER:"):]

def extract_tar_to_desktop(tar_path, folder_name):
    """Extract tar archive to Desktop, handling name conflicts."""
    dest_path = os.path.join(DESKTOP, folder_name)

    if os.path.exists(dest_path):
        print(f"\n  [!] A folder named '{folder_name}' already exists on your Desktop.")
        print(f"  [!] What would you like to do?")
        print(f"  1. Overwrite it")
        print(f"  2. Rename the restored folder")
        print(f"  3. Cancel")
        choice = input("\n  Enter choice: ").strip()
        if choice == "1":
            import shutil
            shutil.rmtree(dest_path)
        elif choice == "2":
            new_name = input(f"  New folder name (default: {folder_name}_restored): ").strip()
            folder_name = new_name if new_name else f"{folder_name}_restored"
            dest_path   = os.path.join(DESKTOP, folder_name)
        else:
            print("  [!] Cancelled.")
            return None

    print(f"\n  [+] Extracting folder to Desktop...")
    with tarfile.open(tar_path, "r") as tar:
        # Security: strip any absolute paths or .. traversal
        members = []
        for m in tar.getmembers():
            if m.name.startswith("/") or ".." in m.name:
                continue
            members.append(m)
        tar.extractall(path=DESKTOP, members=members)

    return dest_path

def print_folder_success(folder_path, algo_name, folder_name, file_count):
    print("\n" + "=" * 55)
    print("  DECRYPTION COMPLETE")
    print("=" * 55)
    print(f"\n  Algorithm      : {algo_name}")
    print(f"  Folder restored: {folder_name}")
    print(f"  Location       : {folder_path}")
    print(f"  Files restored : {file_count}")
    print("\n" + "=" * 55 + "\n")

def count_restored_files(folder_path):
    count = 0
    for _, _, files in os.walk(folder_path):
        count += len(files)
    return count

# =============================================================
#  UTILITIES
# =============================================================

def derive_key(password, salt, length=32):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=480000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def load_keyfile(keyfile, length=32):
    path = os.path.join(KEYS_DIR, keyfile)
    if not os.path.exists(path):
        print(f"\n  [!] Key file not found: {path}")
        return None
    with open(path, "rb") as f:
        return f.read()[:length]

def save_output(data, filename):
    filepath = os.path.join(DESKTOP, filename)
    with open(filepath, "wb") as f:
        f.write(data)
    return filepath

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
    print("  DECRYPTOR")
    print("=" * 55)

def print_algorithms(large=False):
    algs  = LARGE_ALGORITHMS if large else ALGORITHMS
    label = "SELECT ALGORITHM  (Large File Mode)" if large else "SELECT ALGORITHM USED TO ENCRYPT"
    print("\n" + "=" * 55)
    print(f"  {label}")
    print("=" * 55 + "\n")
    for key, alg in algs.items():
        print(f"  {key}. {alg['name']}")
        print(f"     {alg['desc']}\n")

def print_success(filepath, algo_name, original_filename, plaintext=None):
    print("\n" + "=" * 55)
    print("  DECRYPTION COMPLETE")
    print("=" * 55)
    print(f"\n  Algorithm      : {algo_name}")
    print(f"  Original file  : {original_filename}")
    print(f"  Saved to       : {filepath}")
    print(f"  File size      : {format_size(os.path.getsize(filepath))}")

    if plaintext is not None:
        ext = os.path.splitext(filepath)[1].lower()
        text_exts = {".txt", ".md", ".csv", ".json", ".xml", ".html", ".py", ".js", ""}
        if ext in text_exts:
            try:
                preview = plaintext[:200].decode(errors="replace")
                print(f"\n  Preview    :\n\n  {preview}")
                if len(plaintext) > 200:
                    print(f"\n  ... [{len(plaintext) - 200} more bytes]")
            except Exception:
                pass
        else:
            print(f"\n  [Binary file — open normally to view]")

    print("\n" + "=" * 55 + "\n")

# =============================================================
#  INPUT HELPERS
# =============================================================

def get_encrypted_file():
    """
    List all files on Desktop that have no extension OR unknown extensions —
    i.e. the random-named encrypted files — plus any legacy .enc files.
    Shows file sizes to help identify large encrypted files.
    """
    all_files = sorted([
        f for f in os.listdir(DESKTOP)
        if os.path.isfile(os.path.join(DESKTOP, f)) and not f.startswith(".")
    ])

    if not all_files:
        print("\n  [!] No files found on Desktop.")
        return None, None

    print(f"\n  Files on Desktop:\n")
    for i, f in enumerate(all_files, 1):
        size = format_size(os.path.getsize(os.path.join(DESKTOP, f)))
        ext  = os.path.splitext(f)[1]
        tag  = "  ← likely encrypted" if not ext or ext == ".enc" else ""
        print(f"  {i}. {f}  ({size}){tag}")

    choice = input("\n  Select file number: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(all_files):
            chosen = all_files[idx]
            return os.path.join(DESKTOP, chosen), chosen
    except (ValueError, IndexError):
        pass
    print("  [!] Invalid selection.")
    return None, None

def ask_key_method(alg_info):
    method = alg_info["key_method"]
    if method == "password_only": return "password"
    if method == "shift_only":    return "shift"
    if method == "keyfile_only":  return "keyfile"
    print("\n  How was this file encrypted?")
    print("  1. Password  (a passphrase was used)")
    print("  2. Key file  (a key file was generated)")
    choice = input("\n  Enter choice: ").strip()
    return "password" if choice == "1" else "keyfile"

def gather_key_info(alg):
    key_method = ask_key_method(alg)
    password = keyfile = shift = None

    if key_method == "password":
        password = input("\n  Enter decryption password: ").strip()
        if not password:
            print("  [!] No password entered.")
            return None, None, None

    elif key_method == "keyfile":
        default_name = f"{alg['name'].lower().replace('-','_').replace(' ','_')}.key"
        fname   = input(f"\n  Key file name (default: {default_name}): ").strip()
        keyfile = fname if fname else default_name

    elif key_method == "shift":
        try:
            shift = int(input("\n  Enter the Caesar shift number used to encrypt (1-25): ").strip())
        except ValueError:
            print("  [!] Invalid shift number.")
            return None, None, None

    return password, keyfile, shift

def build_output_name(original_filename):
    """Restore the original filename exactly as it was before encryption."""
    default = original_filename if original_filename else "decrypted_output"
    name = input(f"\n  Output filename (default: {default}): ").strip()
    return name if name else default

# =============================================================
#  STANDARD DECRYPTION
# =============================================================

def decrypt_aes_cbc(ciphertext, password=None, keyfile=None):
    try:
        salt    = ciphertext[:16]
        iv      = ciphertext[16:32]
        data    = ciphertext[32:]
        key     = load_keyfile(keyfile) if keyfile else derive_key(password, salt)
        if key is None: return None
        cipher  = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        dec     = cipher.decryptor()
        padded  = dec.update(data) + dec.finalize()
        pad_len = padded[-1]
        return padded[:-pad_len]
    except Exception as e:
        print(f"\n  [!] AES-CBC decryption failed: {e}")
        return None

def decrypt_aes_gcm(ciphertext, password=None, keyfile=None):
    try:
        salt  = ciphertext[:16]
        nonce = ciphertext[16:28]
        data  = ciphertext[28:]
        key   = load_keyfile(keyfile) if keyfile else derive_key(password, salt)
        if key is None: return None
        return AESGCM(key).decrypt(nonce, data, None)
    except InvalidTag:
        print("\n  [!] Decryption failed — wrong password/key or file was tampered with.")
        return None
    except Exception as e:
        print(f"\n  [!] AES-GCM decryption failed: {e}")
        return None

def decrypt_chacha20(ciphertext, password=None, keyfile=None):
    try:
        salt  = ciphertext[:16]
        nonce = ciphertext[16:28]
        data  = ciphertext[28:]
        key   = load_keyfile(keyfile) if keyfile else derive_key(password, salt)
        if key is None: return None
        return ChaCha20Poly1305(key).decrypt(nonce, data, None)
    except InvalidTag:
        print("\n  [!] Decryption failed — wrong password/key or file was tampered with.")
        return None
    except Exception as e:
        print(f"\n  [!] ChaCha20 decryption failed: {e}")
        return None

def decrypt_fernet(ciphertext, password=None, keyfile=None):
    try:
        if keyfile:
            fkey_path = os.path.join(KEYS_DIR, keyfile)
            if not os.path.exists(fkey_path):
                print(f"\n  [!] Key file not found: {fkey_path}")
                return None
            with open(fkey_path, "rb") as f:
                fernet_key = f.read().strip()
            return Fernet(fernet_key).decrypt(ciphertext)
        else:
            if not ciphertext.startswith(b"SALTPFX:"):
                print("\n  [!] Missing salt prefix — was this encrypted with a password?")
                return None
            rest            = ciphertext[len(b"SALTPFX:"):]
            salt_b64, token = rest.split(b":", 1)
            salt            = base64.urlsafe_b64decode(salt_b64)
            key             = derive_key(password, salt, length=32)
            fernet_key      = base64.urlsafe_b64encode(key)
            return Fernet(fernet_key).decrypt(token)
    except InvalidToken:
        print("\n  [!] Decryption failed — wrong password or corrupted file.")
        return None
    except Exception as e:
        print(f"\n  [!] Fernet decryption failed: {e}")
        return None

def decrypt_rsa(ciphertext, keyfile_base):
    priv_path = os.path.join(KEYS_DIR, f"{keyfile_base}_private.pem")
    if not os.path.exists(priv_path):
        print(f"\n  [!] Private key not found: {priv_path}")
        return None
    try:
        with open(priv_path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        return private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    except Exception as e:
        print(f"\n  [!] RSA decryption failed: {e}")
        return None

def decrypt_xor(ciphertext, password):
    key = password.encode()
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(ciphertext)])

def decrypt_caesar(ciphertext, shift):
    result = []
    for char in ciphertext.decode(errors="ignore"):
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            result.append(chr((ord(char) - base - shift) % 26 + base))
        else:
            result.append(char)
    return "".join(result).encode()

# =============================================================
#  LARGE FILE STREAMING DECRYPTION
# =============================================================

def stream_decrypt_aes_cbc(in_path, out_path, password=None, keyfile=None):
    file_size = os.path.getsize(in_path)
    print(f"\n  [+] Decrypting {format_size(file_size)} with AES-256-CBC...\n")
    original_filename = None
    with open(in_path, "rb") as fin, open(out_path, "wb") as fout:
        salt = fin.read(16)
        key  = load_keyfile(keyfile) if keyfile else derive_key(password, salt)
        if key is None: return None, None
        processed = 0
        while True:
            tag = fin.read(9)
            if not tag: break
            iv_bytes  = fin.read(16)
            len_bytes = fin.read(4)
            if len(len_bytes) < 4: break
            chunk_len = struct.unpack(">I", len_bytes)[0]
            chunk     = fin.read(chunk_len)
            if not chunk: break
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv_bytes), backend=default_backend())
            dec    = cipher.decryptor()
            padded = dec.update(chunk) + dec.finalize()
            pad_len = padded[-1]
            decrypted_chunk = padded[:-pad_len]
            if tag == b"NAMECHUNK":
                # Extract filename from this chunk — don't write to output
                fn, _ = extract_filename_from_plaintext(decrypted_chunk)
                original_filename = fn
            else:
                fout.write(decrypted_chunk)
            processed += chunk_len
            progress_bar(min(processed, file_size), file_size)
    print(f"\n  [+] Done!")
    return out_path, original_filename

def stream_decrypt_aes_gcm(in_path, out_path, password=None, keyfile=None):
    file_size = os.path.getsize(in_path)
    print(f"\n  [+] Decrypting {format_size(file_size)} with AES-256-GCM...\n")
    original_filename = None
    with open(in_path, "rb") as fin, open(out_path, "wb") as fout:
        salt   = fin.read(16)
        key    = load_keyfile(keyfile) if keyfile else derive_key(password, salt)
        if key is None: return None, None
        aesgcm = AESGCM(key)
        processed = 0
        while True:
            tag = fin.read(9)
            if not tag: break
            nonce = fin.read(12)
            len_bytes = fin.read(4)
            if len(len_bytes) < 4: break
            chunk_len = struct.unpack(">I", len_bytes)[0]
            chunk     = fin.read(chunk_len)
            if not chunk: break
            try:
                decrypted_chunk = aesgcm.decrypt(nonce, chunk, None)
            except InvalidTag:
                print("\n\n  [!] Authentication failed — file may be corrupted or tampered with.")
                return None, None
            if tag == b"NAMECHUNK":
                fn, _ = extract_filename_from_plaintext(decrypted_chunk)
                original_filename = fn
            else:
                fout.write(decrypted_chunk)
            processed += chunk_len
            progress_bar(min(processed, file_size), file_size)
    print(f"\n  [+] Done!")
    return out_path, original_filename

def stream_decrypt_chacha20(in_path, out_path, password=None, keyfile=None):
    file_size = os.path.getsize(in_path)
    print(f"\n  [+] Decrypting {format_size(file_size)} with ChaCha20-Poly1305...\n")
    original_filename = None
    with open(in_path, "rb") as fin, open(out_path, "wb") as fout:
        salt   = fin.read(16)
        key    = load_keyfile(keyfile) if keyfile else derive_key(password, salt)
        if key is None: return None, None
        chacha = ChaCha20Poly1305(key)
        processed = 0
        while True:
            tag = fin.read(9)
            if not tag: break
            nonce = fin.read(12)
            len_bytes = fin.read(4)
            if len(len_bytes) < 4: break
            chunk_len = struct.unpack(">I", len_bytes)[0]
            chunk     = fin.read(chunk_len)
            if not chunk: break
            try:
                decrypted_chunk = chacha.decrypt(nonce, chunk, None)
            except InvalidTag:
                print("\n\n  [!] Authentication failed — file may be corrupted or tampered with.")
                return None, None
            if tag == b"NAMECHUNK":
                fn, _ = extract_filename_from_plaintext(decrypted_chunk)
                original_filename = fn
            else:
                fout.write(decrypted_chunk)
            processed += chunk_len
            progress_bar(min(processed, file_size), file_size)
    print(f"\n  [+] Done!")
    return out_path, original_filename


# =============================================================
#  MAIN DECRYPTION FLOWS
# =============================================================

def run_standard_decryption(algo_choice, raw_bytes):
    alg = ALGORITHMS[algo_choice]
    password, keyfile, shift = gather_key_info(alg)

    # Decrypt first — filename is hidden inside the encrypted blob
    decrypted = None
    if   algo_choice == "1": decrypted = decrypt_aes_cbc(raw_bytes,  password=password, keyfile=keyfile)
    elif algo_choice == "2": decrypted = decrypt_aes_gcm(raw_bytes,  password=password, keyfile=keyfile)
    elif algo_choice == "3": decrypted = decrypt_chacha20(raw_bytes, password=password, keyfile=keyfile)
    elif algo_choice == "4": decrypted = decrypt_fernet(raw_bytes,   password=password, keyfile=keyfile)
    elif algo_choice == "5":
        kb        = input("\n  Base name of RSA key pair used (e.g. 'mykeys'): ").strip() or "rsa_keys"
        decrypted = decrypt_rsa(raw_bytes, kb)
    elif algo_choice == "6": decrypted = decrypt_xor(raw_bytes,    password)
    elif algo_choice == "7": decrypted = decrypt_caesar(raw_bytes, shift)

    if not decrypted:
        print("\n  [!] Decryption failed. Check your password or key file.\n")
        return

    # Extract filename from inside the decrypted plaintext
    original_filename, file_bytes = extract_filename_from_plaintext(decrypted)

    if original_filename:
        print(f"\n  [+] Original file restored : {original_filename}")
    else:
        print(f"\n  [+] No filename found in payload (legacy file)")
        file_bytes = decrypted

    if is_folder_payload(original_filename):
        # It's an encrypted folder — write tar to temp, extract to Desktop
        folder_name = get_folder_name_from_label(original_filename)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".tar")
        tmp.write(file_bytes)
        tmp.close()
        try:
            dest = extract_tar_to_desktop(tmp.name, folder_name)
            if dest:
                file_count = count_restored_files(dest)
                print_folder_success(dest, alg["name"], folder_name, file_count)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)
    else:
        out_name = build_output_name(original_filename)
        filepath = save_output(file_bytes, out_name)
        print_success(filepath, alg["name"], original_filename, file_bytes)



def run_large_file_decryption(algo_choice, in_path):
    alg = LARGE_ALGORITHMS[algo_choice]
    password, keyfile, shift = gather_key_info(alg)

    temp_out = os.path.join(DESKTOP, "_decrypting_temp")
    out_path = original_filename = None

    if   algo_choice == "1": out_path, original_filename = stream_decrypt_aes_cbc(in_path,    temp_out, password=password, keyfile=keyfile)
    elif algo_choice == "2": out_path, original_filename = stream_decrypt_aes_gcm(in_path,    temp_out, password=password, keyfile=keyfile)
    elif algo_choice == "3": out_path, original_filename = stream_decrypt_chacha20(in_path,   temp_out, password=password, keyfile=keyfile)

    if not out_path:
        print("\n  [!] Decryption failed. Check your password or key file.\n")
        if os.path.exists(temp_out):
            os.remove(temp_out)
        return

    if is_folder_payload(original_filename):
        folder_name = get_folder_name_from_label(original_filename)
        try:
            dest = extract_tar_to_desktop(temp_out, folder_name)
            if dest:
                file_count = count_restored_files(dest)
                print_folder_success(dest, alg["name"], folder_name, file_count)
            else:
                if os.path.exists(temp_out):
                    os.remove(temp_out)
        except Exception as e:
            print(f"\n  [!] Folder extraction failed: {e}")
            if os.path.exists(temp_out):
                os.remove(temp_out)
    else:
        final_name = build_output_name(original_filename)
        final_path = os.path.join(DESKTOP, final_name)
        os.rename(temp_out, final_path)
        print_success(final_path, alg["name"], original_filename)

# =============================================================
#  MAIN
# =============================================================

def main():
    print_banner()

    while True:
        print("\n  Select the file to decrypt:")
        in_path, enc_label = get_encrypted_file()

        if not in_path:
            continue

        file_size = os.path.getsize(in_path)
        print(f"\n  [+] Loaded : {enc_label} ({format_size(file_size)})")

        if file_size > LARGE_FILE_THRESHOLD:
            print(f"\n  [!] Large file detected — using streaming decryption mode.")
            print_algorithms(large=True)
            algo_choice = input("  Enter algorithm number: ").strip()
            if algo_choice not in LARGE_ALGORITHMS:
                print("  [!] Invalid algorithm.")
                continue
            run_large_file_decryption(algo_choice, in_path)
        else:
            with open(in_path, "rb") as f:
                raw_bytes = f.read()
            print_algorithms(large=False)
            algo_choice = input("  Enter algorithm number (must match what was used to encrypt): ").strip()
            if algo_choice not in ALGORITHMS:
                print("  [!] Invalid algorithm.")
                continue
            run_standard_decryption(algo_choice, raw_bytes)

        again = input("  Decrypt another file? (y/n): ").strip().lower()
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