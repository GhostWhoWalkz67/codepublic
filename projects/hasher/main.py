import hashlib
import os
import bcrypt
from passlib.hash import sha512_crypt

# =============================================================
#  HASH TYPES
#  Matched to dehasher modes so both tools work together
# =============================================================

HASH_TYPES = {
    "1":  {"name": "MD5",          "mode": 0,     "algo": "md5"},
    "2":  {"name": "MD4",          "mode": 900,   "algo": "md4"},
    "3":  {"name": "SHA1",         "mode": 100,   "algo": "sha1"},
    "4":  {"name": "SHA-256",      "mode": 1400,  "algo": "sha256"},
    "5":  {"name": "SHA-384",      "mode": 10800, "algo": "sha384"},
    "6":  {"name": "SHA-512",      "mode": 1700,  "algo": "sha512"},
    "7":  {"name": "bcrypt",       "mode": 3200,  "algo": "bcrypt"},
    "8":  {"name": "SHA-512 crypt","mode": 1800,  "algo": "sha512crypt"},
    "9":  {"name": "NTLM",         "mode": 1000,  "algo": "ntlm"},
}

# =============================================================
#  HASHING FUNCTIONS
# =============================================================

def hash_md5(password):
    return hashlib.md5(password.encode()).hexdigest()

def hash_md4(password):
    try:
        return hashlib.new("md4", password.encode()).hexdigest()
    except ValueError:
        print("  [!] MD4 not supported on this system.")
        return None

def hash_sha1(password):
    return hashlib.sha1(password.encode()).hexdigest()

def hash_sha256(password):
    return hashlib.sha256(password.encode()).hexdigest()

def hash_sha384(password):
    return hashlib.sha384(password.encode()).hexdigest()

def hash_sha512(password):
    return hashlib.sha512(password.encode()).hexdigest()

def hash_bcrypt(password):
    try:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()
    except Exception as e:
        print(f"  [!] bcrypt error: {e}")
        print("  [!] Install it with: pip3 install bcrypt")
        return None

def hash_sha512crypt(password):
    try:
        return sha512_crypt.using(rounds=5000).hash(password)
    except Exception as e:
        print(f"  [!] SHA-512 crypt error: {e}")
        return None

def hash_ntlm(password):
    import binascii
    return binascii.hexlify(
        hashlib.new("md4", password.encode("utf-16-le")).digest()
    ).decode()

def compute_hash(password, algo):
    dispatch = {
        "md5":        hash_md5,
        "md4":        hash_md4,
        "sha1":       hash_sha1,
        "sha256":     hash_sha256,
        "sha384":     hash_sha384,
        "sha512":     hash_sha512,
        "bcrypt":     hash_bcrypt,
        "sha512crypt":hash_sha512crypt,
        "ntlm":       hash_ntlm,
    }
    fn = dispatch.get(algo)
    if fn:
        return fn(password)
    return None

# =============================================================
#  DISPLAY
# =============================================================

def print_hash_menu():
    print("\n" + "=" * 55)
    print("  SELECT HASH TYPE")
    print("=" * 55 + "\n")
    for key, ht in HASH_TYPES.items():
        print(f"  {key:>2}. {ht['name']:<20} (hashcat -m {ht['mode']})")
    print()

def print_result(password, hashed, hash_type, filepath):
    ht = HASH_TYPES[hash_type]
    print("\n" + "=" * 55)
    print("  RESULT")
    print("=" * 55)
    print(f"\n  Password   : {password}")
    print(f"  Hash Type  : {ht['name']}")
    print(f"  Hash       : {hashed}")
    print(f"  Saved to   : {filepath}")
    print(f"\n  Crack it   : hashcat -m {ht['mode']} {filepath} ~/wordlists/rockyou.txt")
    print("=" * 55 + "\n")

# =============================================================
#  MAIN
# =============================================================

def main():
    print("\n" + "=" * 55)
    print("  PASSWORD HASHER")
    print("=" * 55)

    while True:
        password = input("\n  Enter password to hash (or 'q' to quit): ").strip()
        if password.lower() == "q":
            print("\n  Goodbye!\n")
            break
        if not password:
            print("  [!] No password entered.")
            continue

        print_hash_menu()
        choice = input("  Enter choice: ").strip()

        if choice not in HASH_TYPES:
            print("  [!] Invalid selection.")
            continue

        ht = HASH_TYPES[choice]
        hashed = compute_hash(password, ht["algo"])

        if not hashed:
            print("  [!] Hashing failed. See error above.")
            continue

        filename = input("\n  Name your output file (no extension): ").strip()
        if not filename:
            filename = "output"

        filepath = os.path.expanduser(f"~/Desktop/{filename}.txt")

        with open(filepath, "w") as f:
            f.write(hashed + "\n")

        print_result(password, hashed, choice, filepath)

        again = input("  Hash another password? (y/n): ").strip().lower()
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