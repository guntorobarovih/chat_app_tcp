#!/usr/bin/env python3
"""
chat_server_with_files.py
Server TCP chat dengan dukungan file attachment.
"""

import socket
import threading
import traceback
import json
import os
from datetime import datetime

HOST = "127.0.0.1"   # Ubah ke "0.0.0.0" untuk accept dari interface manapun
PORT = 65432

clients_lock = threading.Lock()
clients = {}  # nickname -> (conn, addr)
files_dir = "server_files"

# Buat directory untuk menyimpan file
if not os.path.exists(files_dir):
    os.makedirs(files_dir)

def log_message(msg):
    """Log dengan timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def broadcast(message, exclude_nick=None):
    """Kirim message (str) ke semua clients kecuali exclude_nick."""
    data = (message + "\n").encode("utf-8")
    with clients_lock:
        for nick, (conn, _) in list(clients.items()):
            if nick == exclude_nick:
                continue
            try:
                conn.sendall(data)
            except Exception as e:
                log_message(f"[!] Gagal kirim ke {nick}: {e}")
                remove_client(nick)

def broadcast_json(msg_obj, exclude_nick=None):
    """Broadcast pesan JSON ke semua clients."""
    data = (json.dumps(msg_obj) + "\n").encode("utf-8")
    with clients_lock:
        for nick, (conn, _) in list(clients.items()):
            if nick == exclude_nick:
                continue
            try:
                conn.sendall(data)
            except Exception as e:
                log_message(f"[!] Gagal kirim ke {nick}: {e}")
                remove_client(nick)

def remove_client(nick):
    """Tutup koneksi dan hapus client dari daftar."""
    with clients_lock:
        if nick in clients:
            conn, addr = clients.pop(nick)
            try:
                conn.close()
            except Exception:
                pass
            log_message(f"[i] {nick} disconnected ({addr}).")
            broadcast(f"[Server] {nick} has left the chat.")

def handle_client(conn, addr):
    """Thread handler untuk setiap client."""
    nick = None
    try:
        conn.sendall("Welcome! Please enter your nickname: ".encode("utf-8"))
        nick_bytes = conn.recv(1024)
        if not nick_bytes:
            conn.close()
            return
        nick = nick_bytes.decode("utf-8").strip()
        if not nick:
            conn.sendall("Invalid nickname. Disconnecting.\n".encode("utf-8"))
            conn.close()
            return

        # cek unik nickname
        with clients_lock:
            if nick in clients:
                conn.sendall(f"Nickname '{nick}' already in use. Disconnecting.\n".encode("utf-8"))
                conn.close()
                return
            clients[nick] = (conn, addr)

        log_message(f"[+] {nick} connected from {addr}")
        broadcast(f"[Server] {nick} has joined the chat.", exclude_nick=nick)
        conn.sendall(f"[Server] Welcome, {nick}! You can now send messages and files.\n".encode("utf-8"))

        # loop untuk menerima pesan/file
        buffer = ""
        while True:
            data = conn.recv(4096)
            if not data:
                break
            buffer += data.decode("utf-8", errors="replace")
            
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                
                # Cek apakah ini JSON (file/structured message) atau text biasa
                if line.startswith('{'):
                    try:
                        msg_obj = json.loads(line)
                        
                        if msg_obj.get('type') == 'FILE':
                            # Handle file transfer
                            handle_file_transfer(nick, msg_obj, conn)
                        elif msg_obj.get('type') == 'TEXT':
                            # Handle text message
                            content = msg_obj.get('content', '')
                            if content.lower() == "/quit":
                                conn.sendall("[Server] Bye!\n".encode("utf-8"))
                                remove_client(nick)
                                return
                            broadcast(f"{nick}: {content}", exclude_nick=None)
                        else:
                            broadcast(f"{nick}: {line}", exclude_nick=None)
                    except json.JSONDecodeError:
                        # Jika gagal parse JSON, treat sebagai text biasa
                        broadcast(f"{nick}: {line}", exclude_nick=None)
                else:
                    # Text biasa
                    if line.lower() == "/quit":
                        conn.sendall("[Server] Bye!\n".encode("utf-8"))
                        remove_client(nick)
                        return
                    elif line.startswith("/msg "):
                        # Private message
                        parts = line.split(" ", 2)
                        if len(parts) < 3:
                            conn.sendall("[Server] Usage: /msg <nick> <message>\n".encode("utf-8"))
                        else:
                            target, msg = parts[1], parts[2]
                            with clients_lock:
                                if target in clients:
                                    tconn, _ = clients[target]
                                    try:
                                        tconn.sendall(f"[Private] {nick}: {msg}\n".encode("utf-8"))
                                        conn.sendall(f"[Private to {target}] {nick}: {msg}\n".encode("utf-8"))
                                    except Exception:
                                        conn.sendall(f"[Server] Failed to send private message to {target}\n".encode("utf-8"))
                                else:
                                    conn.sendall(f"[Server] User {target} not found.\n".encode("utf-8"))
                    else:
                        broadcast(f"{nick}: {line}", exclude_nick=None)
                        
    except Exception as e:
        log_message(f"[!] Exception in client handler: {e}")
        traceback.print_exc()
    finally:
        # pastikan client dihapus
        if nick:
            with clients_lock:
                if nick in clients:
                    remove_client(nick)

def handle_file_transfer(sender_nick, file_msg, sender_conn):
    """Handle penerimaan file dari client."""
    try:
        filename = file_msg.get('filename', 'unknown')
        file_base64 = file_msg.get('data', '')
        file_size = file_msg.get('size', 0)
        
        # Decode file
        import base64
        file_data = base64.b64decode(file_base64)
        
        # Simpan file di server
        file_path = os.path.join(files_dir, f"{sender_nick}_{filename}")
        
        # Handle duplicate names
        if os.path.exists(file_path):
            name, ext = os.path.splitext(f"{sender_nick}_{filename}")
            counter = 1
            while os.path.exists(f"{name}_{counter}{ext}"):
                counter += 1
            file_path = os.path.join(files_dir, f"{name}_{counter}{ext}")
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        log_message(f"[File] {sender_nick} uploaded: {filename} ({len(file_data) / 1024:.1f} KB)")
        
        # Broadcast file ke clients lain
        file_msg_broadcast = {
            'type': 'FILE',
            'sender': sender_nick,
            'filename': filename,
            'size': len(file_data),
            'data': file_base64
        }
        broadcast_json(file_msg_broadcast, exclude_nick=sender_nick)
        
        # Konfirmasi ke sender
        sender_conn.sendall(f"[Server] File {filename} sent to other users.\n".encode("utf-8"))
        
    except Exception as e:
        log_message(f"[!] Error handling file transfer: {e}")
        try:
            sender_conn.sendall(f"[Server] Error: Failed to process file transfer: {e}\n".encode("utf-8"))
        except:
            pass

def main():
    log_message(f"Starting server on {HOST}:{PORT}")
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(5)
    log_message("Server listening...")

    try:
        while True:
            conn, addr = server_sock.accept()
            log_message(f"[Connection] New connection from {addr}")
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        log_message("Shutting down server...")
    finally:
        server_sock.close()
        # tutup koneksi client
        with clients_lock:
            for nick, (conn, _) in clients.items():
                try:
                    conn.close()
                except Exception:
                    pass
            clients.clear()

if __name__ == "__main__":
    main()
