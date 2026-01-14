import subprocess
import sys
import time

def run_command(command, description):
    print(f"[*] Running: {description}...")
    start_time = time.time()
    try:
        subprocess.check_call(command, shell=True)
        duration = time.time() - start_time
        print(f"[+] PASS: {description} ({duration:.2f}s)\n")
        return True
    except subprocess.CalledProcessError:
        duration = time.time() - start_time
        print(f"[-] FAIL: {description} ({duration:.2f}s)\n")
        return False

def main():
    print("=========================================")
    print("   AUTOMATED TESTING - BACKEND SIMAORKA  ")
    print("=========================================\n")
    
    # 1. System Check
    if not run_command("python manage.py check", "System Check"):
        print("Aborting tests due to system check failure.")
        sys.exit(1)

    # 2. Run Tests
    # Using --keepdb to speed up repeated runs if needed, but standard run is safer for clean state
    if not run_command("python manage.py test", "Unit Tests"):
        print("Tests failed.")
        sys.exit(1)

    print("=========================================")
    print("   ALL CHECKS PASSED SUCCESSFULLY        ")
    print("=========================================")

if __name__ == "__main__":
    main()
