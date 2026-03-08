import hashlib
import os

def hash_password(password, hash_type):
    if hash_type == "1":
        hashed = hashlib.md5(password.encode()).hexdigest()
        extension = ".txt"
        return hashed, extension
    else:
        print("Invalid selection.")
        return None, None

def main():
    print("\n=== PASSWORD HASHER ===\n")

    password = input("Enter password to hash: ").strip()
    if not password:
        print("No password entered. Exiting.")
        return

    print("\nSelect hash type:")
    print("  1. MD5")
    choice = input("\nEnter choice: ").strip()

    hashed, extension = hash_password(password, choice)
    if not hashed:
        return

    filename = input("\nName your output file (no extension): ").strip()
    if not filename:
        filename = "output"

    filepath = os.path.expanduser(f"~/Desktop/{filename}{extension}")

    with open(filepath, "w") as f:
        f.write(hashed + "\n")

    print(f"\n  Password  : {password}")
    print(f"  Hash      : {hashed}")
    print(f"  Saved to  : {filepath}")
    print(f"\n  Crack it  : hashcat -m 0 {filepath} ~/wordlists/rockyou.txt\n")

if __name__ == "__main__":
    main()