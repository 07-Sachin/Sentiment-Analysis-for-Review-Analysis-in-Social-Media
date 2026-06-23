#!/usr/bin/env python3
import subprocess, time, os, sys, threading
from colorama import Fore, init
init(autoreset=True)

def start(cmd, name):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    def stream():
        for line in iter(p.stdout.readline, b''):
            try:
                text = line.decode('utf-8', errors='ignore').rstrip()
            except:
                text = str(line)
            print(Fore.CYAN + f"[{name}] " + Fore.RESET + text)
    t = threading.Thread(target=stream, daemon=True)
    t.start()
    return p, t

def ensure_venv_and_install():
    if not os.path.exists("venv"):
        print("Creating venv...")
        os.system("python -m venv venv")
    print("Installing dependencies...")
    os.system(f"{sys.executable} -m pip install -r requirements.txt --quiet")
    os.system(f"{sys.executable} -m pip install colorama --quiet")

def main():
    ensure_venv_and_install()
    # start gradio app only (no ETL)
    print("Starting Gradio dashboard...")
    p, t = start(f"{sys.executable} dashboard/gradio_dashboard.py", "GRADIO")
    print("Open http://localhost:7860 in your browser")
    try:
        p.wait()
    except KeyboardInterrupt:
        print("Stopping...")
        p.terminate()

if __name__ == '__main__':
    main()
