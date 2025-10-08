#!/usr/bin/env python3
"""
tcp_server_log.py
Server TCP dengan log koneksi dan komunikasi untuk pembelajaran.
"""

import socket
import threading
import datetime

HOST = "0.0.0.0"
PORT = 65432

clients = {}

def log(msg):
    """Fungsi untuk menampilkan waktu dan pesan log"""
    waktu = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{waktu}] {msg}")

def handle_client(conn, addr):
    log(f"[+] Koneksi baru dari {addr}")
    conn.sendall(b"Selamat datang di server TCP.\nSilakan masukkan nickname: ")
    nickname = conn.recv(1024).decode().strip()

    if not nickname:
        log(f"[!] {addr} tidak mengirim nickname, koneksi ditutup.")
        conn.close()
        return

    clients[nickname] = conn
    log(f"[INFO] {nickname} bergabung dari {addr}")

    conn.sendall(f"Halo {nickname}! Anda terhubung ke server.\nKetik /quit untuk keluar.\n".encode())

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            message = data.decode().strip()
            log(f"[DATA] {nickname}@{addr}: {message}")

            if message.lower() == "/quit":
                conn.sendall(b"Sampai jumpa!\n")
                break

            # Broadcast ke client lain
            for n, c in clients.items():
                if c != conn:
                    try:
                        c.sendall(f"{nickname}: {message}\n".encode())
                    except:
                        pass

    except Exception as e:
        log(f"[ERROR] {nickname}: {e}")

    finally:
        log(f"[-] {nickname}@{addr} terputus.")
        conn.close()
        if nickname in clients:
            del clients[nickname]

def main():
    log(f"[i] Server dijalankan di {HOST}:{PORT}")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    log("[i] Server menunggu koneksi...")

    try:
        while True:
            conn, addr = server_socket.accept()
            log(f"[TCP] Handshake sukses dari {addr}")
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        log("[i] Server dihentikan secara manual.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()
