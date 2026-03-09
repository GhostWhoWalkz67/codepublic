import re
import os
import subprocess

# =============================================================
#  PATHS
# =============================================================

WORDLIST      = os.path.expanduser("~/wordlists/rockyou.txt")
WORDLIST_BIG  = os.path.expanduser("~/wordlists/SecLists/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt")
WORDLIST_WIFI = os.path.expanduser("~/wordlists/SecLists/Passwords/WiFi-WPA/probable-v2-wpa-top4800.txt")
RULES_DIR     = "/opt/homebrew/Cellar/hashcat/7.1.2/share/doc/hashcat/rules"
RULE_BEST     = os.path.join(RULES_DIR, "best66.rule")
RULE_DIVE     = os.path.join(RULES_DIR, "dive.rule")
RULE_TOGGLE   = os.path.join(RULES_DIR, "toggles5.rule")
RULE_LEET     = os.path.join(RULES_DIR, "leetspeak.rule")
RULE_ROCKYOU  = os.path.join(RULES_DIR, "rockyou-30000.rule")
DESKTOP       = os.path.expanduser("~/Desktop")
HCXPCAPNGTOOL = "/opt/homebrew/bin/hcxpcapngtool"

SLOW_HASHES = [3200, 500, 1800, 7400]

# =============================================================
#  CRACKING METHODS (general hashes)
# =============================================================

METHODS = {
    "1": {
        "name":        "Dictionary + Best66 Rules (Recommended first attempt)",
        "description": "Tries rockyou.txt mutated with 66 common rules. Fast and effective.",
        "type":        "wordlist+rules",
        "wordlist":    WORDLIST,
        "rules":       RULE_BEST,
    },
    "2": {
        "name":        "Dictionary + Dive Rules (Aggressive)",
        "description": "Rockyou with a much larger ruleset. Slower but catches more variations.",
        "type":        "wordlist+rules",
        "wordlist":    WORDLIST,
        "rules":       RULE_DIVE,
    },
    "3": {
        "name":        "Dictionary + Toggle Rules (Catches CamelCase)",
        "description": "Targets passwords like FuckYouScubaSteve or PassWord123.",
        "type":        "wordlist+rules",
        "wordlist":    WORDLIST,
        "rules":       RULE_TOGGLE,
    },
    "4": {
        "name":        "Dictionary + Leetspeak Rules (Catches p@ssw0rd style)",
        "description": "Targets character substitutions like @ for a, 0 for o, 3 for e.",
        "type":        "wordlist+rules",
        "wordlist":    WORDLIST,
        "rules":       RULE_LEET,
    },
    "5": {
        "name":        "Dictionary + RockYou-30000 Rules (Most Exhaustive)",
        "description": "30,000 rules against rockyou. Very slow but very thorough.",
        "type":        "wordlist+rules",
        "wordlist":    WORDLIST,
        "rules":       RULE_ROCKYOU,
    },
    "6": {
        "name":        "Bigger Wordlist + Best66 Rules",
        "description": "10 million passwords with best66 rules. Good when rockyou fails.",
        "type":        "wordlist+rules",
        "wordlist":    WORDLIST_BIG,
        "rules":       RULE_BEST,
    },
    "7": {
        "name":        "WiFi-Specific Wordlist (WPA2 only)",
        "description": "Small list of ~4800 passwords built specifically for WPA cracking.",
        "type":        "wordlist",
        "wordlist":    WORDLIST_WIFI,
        "rules":       None,
    },
    "8": {
        "name":        "Combinator Attack (Two words joined together)",
        "description": "Smashes two rockyou words together. Catches passwords like sunshinebutterfly.",
        "type":        "combinator",
        "wordlist":    WORDLIST,
        "rules":       None,
    },
    "9": {
        "name":        "Hybrid Attack (Word + 4 digits)",
        "description": "Appends 4 digits to every word. Catches passwords like sunshine2024.",
        "type":        "hybrid",
        "wordlist":    WORDLIST,
        "rules":       None,
    },
    "10": {
        "name":        "TryHackMe Mode — Plain RockYou (No Rules)",
        "description": "Raw rockyou.txt with zero modifications. Best for CTF/THM simple passwords.",
        "type":        "wordlist",
        "wordlist":    WORDLIST,
        "rules":       None,
    },
}

# =============================================================
#  WIFI-SPECIFIC CRACKING METHODS
# =============================================================

WIFI_METHODS = {
    "1": {
        "name":        "WiFi Wordlist — 4800 WPA passwords (fastest)",
        "description": "Small list built specifically for WPA cracking. Try this first.",
        "type":        "wordlist",
        "wordlist":    WORDLIST_WIFI,
        "rules":       None,
    },
    "2": {
        "name":        "RockYou Plain (no rules)",
        "description": "Raw rockyou.txt, no modifications. Fast first pass.",
        "type":        "wordlist",
        "wordlist":    WORDLIST,
        "rules":       None,
    },
    "3": {
        "name":        "RockYou + Best66 Rules (recommended)",
        "description": "Rockyou mutated with 66 rules. Catches Password1!, sunshine2024 etc.",
        "type":        "wordlist+rules",
        "wordlist":    WORDLIST,
        "rules":       RULE_BEST,
    },
    "4": {
        "name":        "RockYou + Toggle Rules (catches CamelCase)",
        "description": "Targets WiFi passwords like HomeNetwork2024 or MyWifiPassword.",
        "type":        "wordlist+rules",
        "wordlist":    WORDLIST,
        "rules":       RULE_TOGGLE,
    },
    "5": {
        "name":        "Hybrid Attack (Word + 4 digits)",
        "description": "Appends 4 digits to every word. Great for passwords like sunshine2024.",
        "type":        "hybrid",
        "wordlist":    WORDLIST,
        "rules":       None,
    },
    "6": {
        "name":        "Combinator Attack (Two words joined)",
        "description": "Joins two rockyou words together. Catches passwords like sunshinebutterfly.",
        "type":        "combinator",
        "wordlist":    WORDLIST,
        "rules":       None,
    },
    "7": {
        "name":        "RockYou + Dive Rules (most aggressive)",
        "description": "Very large ruleset against rockyou. Slow but very thorough.",
        "type":        "wordlist+rules",
        "wordlist":    WORDLIST,
        "rules":       RULE_DIVE,
    },
}

# =============================================================
#  HASH IDENTIFICATION
# =============================================================

def identify_hash(hash_string):
    hash_string = hash_string.strip()
    length = len(hash_string)

    if hash_string.startswith("$2y$") or hash_string.startswith("$2a$"):
        return "bcrypt", 3200
    if hash_string.startswith("$6$"):
        return "SHA-512 crypt", 1800
    if hash_string.startswith("$5$"):
        return "SHA-256 crypt", 7400
    if hash_string.startswith("$1$"):
        return "MD5 crypt", 500

    if re.fullmatch(r"[a-fA-F0-9]+", hash_string):
        if length == 32:
            return "MD5, MD4, or NTLM (ambiguous)", "ambiguous32"
        if length == 40:
            return "SHA1", 100
        if length == 64:
            return "SHA-256", 1400
        if length == 96:
            return "SHA-384", 10800
        if length == 128:
            return "SHA-512", 1700

    return "Unknown", None

# =============================================================
#  SHORT PASSWORD FILTER
# =============================================================

def ask_short_filter(mode):
    print("\n" + "=" * 55)
    print("  SHORT PASSWORD FILTER")
    print("=" * 55)

    if mode in SLOW_HASHES:
        print(f"\n  [!] Warning: This hash type (-m {mode}) is very slow to crack.")
        print("  [!] Filtering to short passwords is strongly recommended.")
    else:
        print("\n  Filtering the wordlist to short passwords only can speed")
        print("  up attacks significantly, especially for simple passwords.")

    use_filter = input("\n  Filter wordlist to short passwords? (y/n): ").strip().lower()
    if use_filter != "y":
        return None

    print("\n  Select max password length:")
    print("  1. 4 characters  (fastest — good for simple CTF hashes)")
    print("  2. 6 characters  (recommended for bcrypt and slow hashes)")
    print("  3. 8 characters  (broader coverage)")
    print("  4. Custom length")

    length_choice = input("\n  Enter choice: ").strip()
    length_map = {"1": 4, "2": 6, "3": 8}

    if length_choice in length_map:
        return length_map[length_choice]
    elif length_choice == "4":
        try:
            return int(input("  Enter max length: ").strip())
        except ValueError:
            print("  [!] Invalid number. Skipping filter.")
            return None
    else:
        print("  [!] Invalid choice. Skipping filter.")
        return None


def filter_wordlist_by_length(max_length):
    filtered_path = os.path.expanduser(f"~/wordlists/rockyou_{max_length}char.txt")

    if os.path.exists(filtered_path):
        print(f"\n  [+] Filtered wordlist already exists: {filtered_path}")
        return filtered_path

    if not os.path.exists(WORDLIST):
        print(f"\n  [!] rockyou.txt not found at: {WORDLIST}")
        return None

    print(f"\n  [+] Filtering rockyou.txt to passwords <= {max_length} chars...")

    count = 0
    with open(WORDLIST, "r", encoding="utf-8", errors="ignore") as infile, \
         open(filtered_path, "w") as outfile:
        for line in infile:
            if len(line.strip()) <= max_length:
                outfile.write(line)
                count += 1

    print(f"  [+] Done — {count:,} passwords saved to {filtered_path}")
    return filtered_path

# =============================================================
#  HASHCAT RUNNER
# =============================================================

def check_path(path, label):
    if not os.path.exists(path):
        print(f"\n  [!] {label} not found at: {path}")
        return False
    return True


def build_command(hashfile, mode, method):
    base = ["hashcat", "-m", str(mode), "--potfile-disable"]

    if method["type"] == "wordlist":
        if not check_path(method["wordlist"], "Wordlist"):
            return None
        return base + [hashfile, method["wordlist"]]

    elif method["type"] == "wordlist+rules":
        if not check_path(method["wordlist"], "Wordlist"):
            return None
        if not check_path(method["rules"], "Rules file"):
            return None
        return base + [hashfile, method["wordlist"], "-r", method["rules"]]

    elif method["type"] == "combinator":
        if not check_path(method["wordlist"], "Wordlist"):
            return None
        return base + ["-a", "1", hashfile, method["wordlist"], method["wordlist"]]

    elif method["type"] == "hybrid":
        if not check_path(method["wordlist"], "Wordlist"):
            return None
        return base + ["-a", "6", hashfile, method["wordlist"], "?d?d?d?d"]

    return None


def print_methods():
    print("\n" + "=" * 55)
    print("  SELECT A CRACKING METHOD")
    print("=" * 55 + "\n")
    for key, method in METHODS.items():
        print(f"  {key}. {method['name']}")
        print(f"     {method['description']}\n")


def print_wifi_methods():
    print("\n" + "=" * 55)
    print("  SELECT A WIFI CRACKING METHOD")
    print("=" * 55 + "\n")
    for key, method in WIFI_METHODS.items():
        print(f"  {key}. {method['name']}")
        print(f"     {method['description']}\n")


def run_single(hashfile, mode, method, filtered_wordlist=None):
    method = dict(method)
    if filtered_wordlist and method["type"] in ("wordlist", "wordlist+rules"):
        method["wordlist"] = filtered_wordlist

    cmd = build_command(hashfile, mode, method)
    if not cmd:
        print("\n  [!] Could not build command. Check your paths.\n")
        return

    print(f"\n  [+] Hash Mode : -m {mode}")
    print(f"  [+] Method    : {method['name']}")
    if filtered_wordlist and method["type"] in ("wordlist", "wordlist+rules"):
        print(f"  [+] Wordlist  : {filtered_wordlist} (filtered)")
    print(f"  [+] Command   : {' '.join(cmd)}")
    print("\n  [+] Press 's' for status, 'p' to pause, 'q' to quit\n")
    print("=" * 55 + "\n")

    try:
        subprocess.run(cmd)
    except FileNotFoundError:
        print("\n  [!] Hashcat not found. Is it installed?\n")


def run_hashcat(hashfile, mode, filtered_wordlist=None):
    print_methods()
    choice = input("  Enter method number: ").strip()
    if choice not in METHODS:
        print("\n  [!] Invalid choice. Exiting.\n")
        return

    method = METHODS[choice]

    if mode == "ambiguous32_auto":
        for auto_mode, label in [("0", "MD5"), ("900", "MD4"), ("1000", "NTLM")]:
            print(f"\n  [+] ── Trying {label} (-m {auto_mode}) ──")
            run_single(hashfile, auto_mode, method, filtered_wordlist)
        print("\n" + "=" * 55)
        print("  [+] Auto mode complete. All three hash types attempted.")
        print("=" * 55 + "\n")
        return

    run_single(hashfile, mode, method, filtered_wordlist)

# =============================================================
#  WIFI MODE
# =============================================================

def find_desktop_files(extensions):
    """Scan Desktop for files matching given extensions."""
    found = []
    for f in os.listdir(DESKTOP):
        if any(f.lower().endswith(ext) for ext in extensions):
            found.append(os.path.join(DESKTOP, f))
    return sorted(found)


def pick_file_from_list(files, label):
    """Present a numbered list of files and let user pick one."""
    print(f"\n  Found {len(files)} {label} file(s) on Desktop:\n")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {os.path.basename(f)}")
    print()
    choice = input("  Enter number to select: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(files):
            return files[idx]
        else:
            print("  [!] Invalid selection.")
            return None
    except ValueError:
        print("  [!] Invalid input.")
        return None


def convert_capture_to_hc22000(pcap_path):
    """Convert a .pcap or .pcapng file to .hc22000 using hcxpcapngtool."""
    if not os.path.exists(HCXPCAPNGTOOL):
        print(f"\n  [!] hcxpcapngtool not found at {HCXPCAPNGTOOL}")
        print("  [!] Install it with: brew install hcxtools\n")
        return None

    base = os.path.splitext(os.path.basename(pcap_path))[0]
    output_path = os.path.join(DESKTOP, f"{base}.hc22000")

    print(f"\n  [+] Converting {os.path.basename(pcap_path)} to .hc22000...")
    print(f"  [+] Output: {output_path}\n")

    result = subprocess.run(
        [HCXPCAPNGTOOL, "-o", output_path, pcap_path],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"  [!] Conversion failed:\n{result.stderr}")
        return None

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        print("  [!] Conversion produced an empty file.")
        print("  [!] The capture may not contain a valid EAPOL handshake.")
        return None

    print(f"  [+] Conversion successful! Saved to: {output_path}")
    return output_path


def wifi_mode():
    print("\n" + "=" * 55)
    print("  WIFI WPA2 ATTACK MODE")
    print("=" * 55)

    print("\n  Do you have:")
    print("  1. Already converted .hc22000 file")
    print("  2. Raw .pcap / .pcapng capture file (will convert automatically)")

    source_choice = input("\n  Enter choice: ").strip()

    hc22000_path = None

    if source_choice == "1":
        # Look for existing .hc22000 files on Desktop
        hc22000_files = find_desktop_files([".hc22000"])
        if not hc22000_files:
            print("\n  [!] No .hc22000 files found on Desktop.")
            manual = input("  Enter full path manually: ").strip()
            if not os.path.exists(manual):
                print("  [!] File not found. Exiting WiFi mode.\n")
                return
            hc22000_path = manual
        else:
            hc22000_path = pick_file_from_list(hc22000_files, ".hc22000")
            if not hc22000_path:
                return

    elif source_choice == "2":
        # Look for .pcap / .pcapng files on Desktop
        pcap_files = find_desktop_files([".pcap", ".pcapng"])
        if not pcap_files:
            print("\n  [!] No .pcap or .pcapng files found on Desktop.")
            manual = input("  Enter full path manually: ").strip()
            if not os.path.exists(manual):
                print("  [!] File not found. Exiting WiFi mode.\n")
                return
            pcap_path = manual
        else:
            pcap_path = pick_file_from_list(pcap_files, ".pcap/.pcapng")
            if not pcap_path:
                return

        hc22000_path = convert_capture_to_hc22000(pcap_path)
        if not hc22000_path:
            return

    else:
        print("\n  [!] Invalid choice. Exiting WiFi mode.\n")
        return

    print(f"\n  [+] Target file : {hc22000_path}")
    print(f"  [+] Hash mode   : -m 22000 (WPA2)")

    # WiFi short filter — optional
    print("\n" + "=" * 55)
    print("  SHORT PASSWORD FILTER")
    print("=" * 55)
    print("\n  WPA2 requires minimum 8 character passwords.")
    print("  Filtering can still help narrow the search range.")
    use_filter = input("\n  Filter wordlist to short passwords? (y/n): ").strip().lower()

    filtered_wordlist = None
    if use_filter == "y":
        print("\n  Select max password length:")
        print("  1. 8 characters  (minimum WPA2 length)")
        print("  2. 10 characters (broader coverage)")
        print("  3. 12 characters (even broader)")
        print("  4. Custom length")
        length_choice = input("\n  Enter choice: ").strip()
        length_map = {"1": 8, "2": 10, "3": 12}
        if length_choice in length_map:
            filtered_wordlist = filter_wordlist_by_length(length_map[length_choice])
        elif length_choice == "4":
            try:
                custom = int(input("  Enter max length: ").strip())
                filtered_wordlist = filter_wordlist_by_length(custom)
            except ValueError:
                print("  [!] Invalid number. Skipping filter.")

    # Show WiFi-specific method menu
    print_wifi_methods()
    choice = input("  Enter method number: ").strip()
    if choice not in WIFI_METHODS:
        print("\n  [!] Invalid choice. Exiting.\n")
        return

    method = WIFI_METHODS[choice]
    run_single(hc22000_path, "22000", method, filtered_wordlist)

# =============================================================
#  MAIN MENU
# =============================================================

def main():
    print("\n" + "=" * 55)
    print("  HASH CRACKER")
    print("=" * 55)
    print("\n  What would you like to do?\n")
    print("  1. Crack a hash")
    print("  2. WiFi WPA2 attack")
    print()

    menu_choice = input("  Enter choice: ").strip()

    if menu_choice == "2":
        wifi_mode()
        return

    if menu_choice != "1":
        print("\n  [!] Invalid choice. Exiting.\n")
        return

    # ── Hash cracking flow ──
    print("\n" + "=" * 55)
    print("  HASH IDENTIFIER & CRACKER")
    print("=" * 55 + "\n")

    hash_input = input("  Paste your hash: ").strip()
    if not hash_input:
        print("  No hash entered. Exiting.")
        return

    hash_type, mode = identify_hash(hash_input)

    print(f"\n  Hash     : {hash_input}")
    print(f"  Type     : {hash_type}")

    if mode == "ambiguous32":
        print("\n  [!] Ambiguous hash — could be MD5, MD4, or NTLM.")
        print("  [!] All three are 32 hex characters and look identical.")
        print("\n  Select hash type to try:")
        print("  1. MD5   (-m 0)    — most common, web apps and Linux")
        print("  2. MD4   (-m 900)  — older, sometimes used in CTFs")
        print("  3. NTLM  (-m 1000) — Windows passwords")
        print("  4. Auto  — try all three automatically (recommended)")
        amb_choice = input("\n  Enter choice: ").strip()
        mode_map = {"1": "0", "2": "900", "3": "1000"}
        if amb_choice in mode_map:
            mode = mode_map[amb_choice]
            print(f"\n  Hashcat  : -m {mode}")
        elif amb_choice == "4":
            mode = "ambiguous32_auto"
            print("\n  [+] Will try MD5, MD4, and NTLM automatically.")
        else:
            print("\n  [!] Invalid choice. Defaulting to MD5 (-m 0).")
            mode = "0"
    elif mode:
        print(f"  Hashcat  : -m {mode}")
    else:
        print("\n  [!] Could not identify hash type. Cannot proceed.\n")
        return

    save = input("\n  Save hash to Desktop and run attack? (y/n): ").strip().lower()
    if save != "y":
        print("\n  Exiting without cracking.\n")
        return

    filename = input("  Name your hash file (no extension): ").strip()
    if not filename:
        filename = "identified_hash"

    filepath = os.path.expanduser(f"~/Desktop/{filename}.txt")

    with open(filepath, "w") as f:
        f.write(hash_input + "\n")

    print(f"\n  [+] Hash saved to: {filepath}")

    try:
        mode_int = int(str(mode).split()[0])
    except (ValueError, AttributeError):
        mode_int = 0

    max_length = ask_short_filter(mode_int)

    filtered_wordlist = None
    if max_length:
        filtered_wordlist = filter_wordlist_by_length(max_length)

    run_hashcat(filepath, mode, filtered_wordlist)


if __name__ == "__main__":
    main()