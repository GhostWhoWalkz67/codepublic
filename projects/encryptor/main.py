import os
import base64

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend

# =============================================================
#  PATHS
# =============================================================

DESKTOP  = os.path.expanduser("~/Desktop")
KEYS_DIR = os.path.join(DESKTOP, "keys")

# =============================================================
#  ALGORITHM REGISTRY
# =============================================================

ALGORITHMS = {
    "1": {"name": "AES-256-CBC",       "key_method": "password_or_file", "desc": "Industry standard block cipher. Fast and widely supported."},
    "2": {"name": "AES-256-GCM",       "key_method": "password_or_file", "desc": "AES with authentication tag. Detects tampering."},
    "3": {"name": "ChaCha20-Poly1305", "key_method": "password_or_file", "desc": "Modern stream cipher. Used in TLS and mobile apps."},
    "4": {"name": "Fernet",            "key_method": "password_or_file", "desc": "Simple and safe symmetric encryption. Great for beginners."},
    "5": {"name": "RSA-2048",          "key_method": "keyfile_only",     "desc": "Asymmetric public/private key pair. Best for short text."},
    "6": {"name": "XOR Cipher",        "key_method": "password_only",    "desc": "Classic educational cipher. Not secure for real use."},
    "7": {"name": "Caesar Cipher",     "key_method": "shift_only",       "desc": "Classic letter-shift cipher. Educational only."},
}

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

# =============================================================
#  DISPLAY
# =============================================================

def print_banner():
    print("\n" + "=" * 55)
    print("  ENCRYPTOR")
    print("=" * 55)

def print_algorithms():
    print("\n" + "=" * 55)
    print("  SELECT ALGORITHM")
    print("=" * 55 + "\n")
    for key, alg in ALGORITHMS.items():
        print(f"  {key}. {alg['name']}")
        print(f"     {alg['desc']}\n")

def print_success(filepath, algo_name, key_hint):
    print("\n" + "=" * 55)
    print("  ENCRYPTION COMPLETE")
    print("=" * 55)
    print(f"\n  Algorithm  : {algo_name}")
    print(f"  Saved to   : {filepath}")
    print(f"  Key info   : {key_hint}")
    print(f"\n  [!] Keep your key safe — without it decryption is impossible.")
    print("=" * 55 + "\n")

# =============================================================
#  INPUT HELPERS
# =============================================================

def ask_input_type():
    print("\n  What would you like to encrypt?")
    print("  1. Text  (type it in)")
    print("  2. File  (choose from Desktop)")
    return input("\n  Enter choice: ").strip()

def get_plaintext():
    text = input("\n  Enter text to encrypt: ").strip()
    if not text:
        print("  [!] No text entered.")
        return None, None
    return text.encode(), "text"

def get_file_bytes():
    files = sorted([
        f for f in os.listdir(DESKTOP)
        if os.path.isfile(os.path.join(DESKTOP, f)) and not f.startswith(".")
    ])
    if not files:
        print("\n  [!] No files found on Desktop.")
        return None, None
    print(f"\n  Files on Desktop:\n")
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
    if method == "password_only":  return "password"
    if method == "shift_only":     return "shift"
    if method == "keyfile_only":   return "keyfile"
    print("\n  How would you like to provide the encryption key?")
    print("  1. Password  (you type a passphrase)")
    print("  2. Key file  (app generates a reusable key file)")
    choice = input("\n  Enter choice: ").strip()
    return "password" if choice == "1" else "keyfile"

def ask_output_name(input_label, algo_name):
    safe   = os.path.splitext(input_label)[0] if "." in input_label else input_label
    slug   = algo_name.lower().replace("-", "_").replace(" ", "_")
    default = f"{safe}_{slug}.enc"
    name   = input(f"\n  Output filename (default: {default}): ").strip()
    return name if name else default

# =============================================================
#  ENCRYPTION FUNCTIONS
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
        # Prepend salt so decryptor can re-derive the key
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
#  MAIN ENCRYPTION FLOW
# =============================================================

def run_encryption(algo_choice, plaintext, input_label):
    alg        = ALGORITHMS[algo_choice]
    key_method = ask_key_method(alg)

    password = keyfile = shift = None
    key_hint = ""

    if key_method == "password":
        password = input("\n  Enter encryption password: ").strip()
        if not password:
            print("  [!] No password entered.")
            return
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
            return
        key_hint = f"Caesar shift: {shift}"

    out_name = ask_output_name(input_label, alg["name"])

    # Dispatch to correct function
    ciphertext = None
    if   algo_choice == "1": ciphertext = encrypt_aes_cbc(plaintext,  password=password, keyfile=keyfile)
    elif algo_choice == "2": ciphertext = encrypt_aes_gcm(plaintext,  password=password, keyfile=keyfile)
    elif algo_choice == "3": ciphertext = encrypt_chacha20(plaintext, password=password, keyfile=keyfile)
    elif algo_choice == "4": ciphertext = encrypt_fernet(plaintext,   password=password, keyfile=keyfile)
    elif algo_choice == "5":
        kb = input("\n  Base name for RSA key pair (e.g. 'mykeys'): ").strip() or "rsa_keys"
        ciphertext = encrypt_rsa(plaintext, kb)
        key_hint = f"RSA key pair: ~/Desktop/keys/{kb}_private/public.pem"
    elif algo_choice == "6": ciphertext = encrypt_xor(plaintext,    password)
    elif algo_choice == "7": ciphertext = encrypt_caesar(plaintext, shift)

    if not ciphertext:
        print("\n  [!] Encryption failed.\n")
        return

    filepath = save_output(ciphertext, out_name)
    print_success(filepath, alg["name"], key_hint)

# =============================================================
#  MAIN
# =============================================================

def main():
    print_banner()

    while True:
        input_type = ask_input_type()

        if input_type == "1":
            plaintext, input_label = get_plaintext()
        elif input_type == "2":
            plaintext, input_label = get_file_bytes()
        else:
            print("  [!] Invalid choice.")
            continue

        if not plaintext:
            continue

        print_algorithms()
        algo_choice = input("  Enter algorithm number: ").strip()

        if algo_choice not in ALGORITHMS:
            print("  [!] Invalid algorithm.")
            continue

        run_encryption(algo_choice, plaintext, input_label)

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