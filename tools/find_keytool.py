import os
import subprocess
import sys

def find_keytool():
    search_paths = [
        r'C:\Program Files\Android',
        r'C:\Program Files\Java',
        r'C:\Program Files (x86)\Java',
        r'C:\Program Files\Common Files\Oracle\Java'
    ]
    
    print("Searching for keytool.exe...")
    for path in search_paths:
        if not os.path.exists(path):
            continue
            
        for root, dirs, files in os.walk(path):
            if 'keytool.exe' in files:
                keytool_path = os.path.join(root, 'keytool.exe')
                print(f"Found: {keytool_path}")
                return keytool_path
    return None

def get_sha1(keytool_path):
    keystore_path = os.path.expanduser(r'~\.android\debug.keystore')
    if not os.path.exists(keystore_path):
        print(f"Error: Keystore not found at {keystore_path}")
        return

    cmd = [
        keytool_path,
        '-list',
        '-v',
        '-keystore', keystore_path,
        '-alias', 'androiddebugkey',
        '-storepass', 'android',
        '-keypass', 'android'
    ]
    
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    except Exception as e:
        print(f"Error running keytool: {e}")

if __name__ == "__main__":
    kt = find_keytool()
    if kt:
        get_sha1(kt)
    else:
        print("Could not find keytool.exe in common locations.")
