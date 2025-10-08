#!/usr/bin/env python3
"""
tcp_client_log.py
Client TCP dengan log handshake, port sumber, dan komunikasi teks.
"""

import socket
import threading
import datetime

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 65432

def log(msg):
    waktu = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{waktu}] {msg}")

def receive_messages(sock):
    """Thread untuk menerima data dari server"""
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                log("[!] Koneksi dengan server terputus.")
                break
            print(data.decode(), end="")
        except:
            log("[!] Error dalam menerima data.")
            break

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    log(f"[TCP] Membuka socket lokal...")

    sock.connect((SERVER_HOST, SERVER_PORT))
    local_addr, local_port = sock.getsockname()
    log(f"[TCP] Terhubung ke server {SERVER_HOST}:{SERVER_PORT} dari port lokal {local_port}")

    # Jalankan thread penerima pesan
    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    try:
        while True:
            msg = input()
            if not msg:
                continue
            sock.sendall((msg + "\n").encode())
            if msg.lower() == "/quit":
                log("[i] Menutup koneksi...")
                break
    except KeyboardInterrupt:
        log("[i] Dihentikan oleh user.")
    finally:
        sock.close()
        log("[i] Socket ditutup.")

if __name__ == "__main__":
    main()
