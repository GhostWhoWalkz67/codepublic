import os
import base64

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag

# =============================================================
#  PATHS
# =============================================================

DESKTOP  = os.path.expanduser("~/Desktop")
KEYS_DIR = os.path.join(DESKTOP, "keys")

# =============================================================
#  ALGORITHM REGISTRY
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

# =============================================================
#  DISPLAY
# =============================================================

def print_banner():
    print("\n" + "=" * 55)
    print("  DECRYPTOR")
    print("=" * 55)

def print_algorithms():
    print("\n" + "=" * 55)
    print("  SELECT ALGORITHM USED TO ENCRYPT")
    print("=" * 55 + "\n")
    for key, alg in ALGORITHMS.items():
        print(f"  {key}. {alg['name']}")
        print(f"     {alg['desc']}\n")

def print_success(filepath, algo_name, plaintext):
    print("\n" + "=" * 55)
    print("  DECRYPTION COMPLETE")
    print("=" * 55)
    print(f"\n  Algorithm  : {algo_name}")
    print(f"  Saved to   : {filepath}")
    try:
        preview = plaintext[:200].decode(errors="replace")
        print(f"\n  Preview    :\n\n  {preview}")
        if len(plaintext) > 200:
            print(f"\n  ... [{len(plaintext) - 200} more bytes]")
    except Exception:
        print(f"\n  [binary file — {len(plaintext)} bytes]")
    print("\n" + "=" * 55 + "\n")

# =============================================================
#  INPUT HELPERS
# =============================================================

def get_enc_file():
    """Show .enc files first, with option to browse all Desktop files."""
    all_files = sorted([
        f for f in os.listdir(DESKTOP)
        if os.path.isfile(os.path.join(DESKTOP, f)) and not f.startswith(".")
    ])
    enc_files = [f for f in all_files if f.endswith(".enc")]

    if enc_files:
        print(f"\n  Encrypted (.enc) files on Desktop:\n")
        for i, f in enumerate(enc_files, 1):
            print(f"  {i}. {f}")
        print(f"\n  {len(enc_files) + 1}. Browse all Desktop files instead")
        choice = input("\n  Select file number: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(enc_files):
                path = os.path.join(DESKTOP, enc_files[idx])
                with open(path, "rb") as f:
                    return f.read(), enc_files[idx]
            elif int(choice) == len(enc_files) + 1:
                return _pick_from_list(all_files)
        except (ValueError, IndexError):
            pass
    else:
        print("\n  No .enc files found on Desktop. Showing all files:\n")
        return _pick_from_list(all_files)

    print("  [!] Invalid selection.")
    return None, None

def _pick_from_list(files):
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f}")
    choice = input("\n  Select file number: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(files):
            path = os.path.join(DESKTOP, files[idx])
            with open(path, "rb") as f:
                return f.read(), files[idx]
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

def ask_output_name(input_label, algo_name):
    slug    = algo_name.lower().replace("-", "_").replace(" ", "_")
    base    = input_label.replace(f"_{slug}.enc", "").replace(".enc", "")
    default = f"{base}_decrypted"
    name    = input(f"\n  Output filename (default: {default}): ").strip()
    return name if name else default

# =============================================================
#  DECRYPTION FUNCTIONS
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
        print("  [!] Wrong password or key file?")
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
        print("  [!] You need the private key file to decrypt RSA.")
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
#  MAIN DECRYPTION FLOW
# =============================================================

def run_decryption(algo_choice, ciphertext, input_label):
    alg        = ALGORITHMS[algo_choice]
    key_method = ask_key_method(alg)

    password = keyfile = shift = None

    if key_method == "password":
        password = input("\n  Enter decryption password: ").strip()
        if not password:
            print("  [!] No password entered.")
            return

    elif key_method == "keyfile":
        default_name = f"{alg['name'].lower().replace('-','_').replace(' ','_')}.key"
        fname   = input(f"\n  Key file name (default: {default_name}): ").strip()
        keyfile = fname if fname else default_name

    elif key_method == "shift":
        try:
            shift = int(input("\n  Enter the Caesar shift number used to encrypt (1-25): ").strip())
        except ValueError:
            print("  [!] Invalid shift number.")
            return

    out_name = ask_output_name(input_label, alg["name"])

    # Dispatch to correct function
    plaintext = None
    if   algo_choice == "1": plaintext = decrypt_aes_cbc(ciphertext,  password=password, keyfile=keyfile)
    elif algo_choice == "2": plaintext = decrypt_aes_gcm(ciphertext,  password=password, keyfile=keyfile)
    elif algo_choice == "3": plaintext = decrypt_chacha20(ciphertext, password=password, keyfile=keyfile)
    elif algo_choice == "4": plaintext = decrypt_fernet(ciphertext,   password=password, keyfile=keyfile)
    elif algo_choice == "5":
        kb        = input("\n  Base name of RSA key pair used (e.g. 'mykeys'): ").strip() or "rsa_keys"
        plaintext = decrypt_rsa(ciphertext, kb)
    elif algo_choice == "6": plaintext = decrypt_xor(ciphertext,    password)
    elif algo_choice == "7": plaintext = decrypt_caesar(ciphertext, shift)

    if not plaintext:
        print("\n  [!] Decryption failed. Check your password or key file.\n")
        return

    filepath = save_output(plaintext, out_name)
    print_success(filepath, alg["name"], plaintext)

# =============================================================
#  MAIN
# =============================================================

def main():
    print_banner()

    while True:
        print("\n  Select the encrypted file to decrypt:")
        ciphertext, input_label = get_enc_file()

        if not ciphertext:
            continue

        print(f"\n  [+] Loaded : {input_label} ({len(ciphertext)} bytes)")

        print_algorithms()
        algo_choice = input("  Enter algorithm number (must match what was used to encrypt): ").strip()

        if algo_choice not in ALGORITHMS:
            print("  [!] Invalid algorithm.")
            continue

        run_decryption(algo_choice, ciphertext, input_label)

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