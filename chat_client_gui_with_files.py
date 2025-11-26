#!/usr/bin/env python3
"""
chat_client_gui_with_files.py
Chat client dengan dukungan file attachment menggunakan base64 encoding.
"""

import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import base64
import os
import json

SERVER_HOST = "192.168.166.3"
SERVER_PORT = 65432
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB limit

class ChatClient:
    def __init__(self, master):
        self.master = master
        master.title("TCP Chat Client with File Support")
        master.geometry("700x500")
        master.minsize(500, 350)
        master.configure(bg="#e9f1f6")

        self.sock = None
        self.connected = False
        self.nickname = ""
        self.file_transfer_dir = "received_files"
        
        # Buat directory untuk file yang diterima
        if not os.path.exists(self.file_transfer_dir):
            os.makedirs(self.file_transfer_dir)

        # ===== FRAME LOGIN =====
        self.frame_login = tk.Frame(master, bg="#e9f1f6")
        tk.Label(self.frame_login, text="Masukkan Nickname", font=("Arial", 12), bg="#e9f1f6").pack(pady=10)
        self.entry_nick = tk.Entry(self.frame_login, font=("Arial", 12), width=30)
        self.entry_nick.pack(pady=5)
        self.btn_connect = tk.Button(self.frame_login, text="Connect", command=self.connect_to_server, font=("Arial", 11))
        self.btn_connect.pack(pady=10)
        self.frame_login.pack(expand=True)

        # ===== FRAME CHAT =====
        self.frame_chat = tk.Frame(master, bg="#e9f1f6")
        self.frame_chat.rowconfigure(0, weight=1)
        self.frame_chat.columnconfigure(0, weight=1)

        self.text_area = scrolledtext.ScrolledText(
            self.frame_chat, wrap=tk.WORD, font=("Consolas", 10),
            state=tk.DISABLED, bg="white"
        )
        self.text_area.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        # Input message
        self.entry_message = tk.Entry(self.frame_chat, font=("Arial", 11))
        self.entry_message.grid(row=1, column=0, padx=(10, 5), pady=(0, 10), sticky="ew")
        self.entry_message.bind("<Return>", self.send_message)

        # Button frame untuk kontrol
        self.btn_send = tk.Button(self.frame_chat, text="Kirim", command=self.send_message, font=("Arial", 10))
        self.btn_send.grid(row=1, column=1, padx=5, pady=(0, 10), sticky="ew")

        self.btn_attach = tk.Button(self.frame_chat, text="Attach File", command=self.attach_file, font=("Arial", 10))
        self.btn_attach.grid(row=1, column=2, padx=5, pady=(0, 10), sticky="ew")

        self.btn_quit = tk.Button(self.frame_chat, text="Keluar", command=self.disconnect, font=("Arial", 10))
        self.btn_quit.grid(row=1, column=3, padx=(0, 10), pady=(0, 10), sticky="ew")

        self.frame_chat.columnconfigure(0, weight=3)
        self.frame_chat.columnconfigure(1, weight=1)
        self.frame_chat.columnconfigure(2, weight=1)
        self.frame_chat.columnconfigure(3, weight=1)

        # Status bar untuk file transfer
        self.label_status = tk.Label(self.frame_chat, text="", font=("Arial", 9), bg="#e9f1f6", fg="blue")
        self.label_status.grid(row=2, column=0, columnspan=4, padx=10, pady=5, sticky="w")

    # ===== Koneksi ke server =====
    def connect_to_server(self):
        nick = self.entry_nick.get().strip()
        if not nick:
            messagebox.showwarning("Peringatan", "Nickname tidak boleh kosong!")
            return
        self.nickname = nick

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SERVER_HOST, SERVER_PORT))
            self.connected = True
        except Exception as e:
            messagebox.showerror("Koneksi Gagal", f"Tidak dapat terhubung ke server:\n{e}")
            return

        # Terima pesan awal
        try:
            welcome = self.sock.recv(4096).decode(errors="replace")
            if welcome:
                self.display_message(welcome.strip())
        except:
            pass

        # Kirim nickname
        try:
            self.sock.sendall((nick + "\n").encode("utf-8"))
        except Exception as e:
            self.display_message(f"[Error] Tidak bisa mengirim nickname: {e}")

        # Jalankan thread untuk menerima pesan/file
        threading.Thread(target=self.receive_messages, daemon=True).start()

        # Ubah tampilan
        self.frame_login.pack_forget()
        self.frame_chat.pack(fill=tk.BOTH, expand=True)
        self.master.title(f"TCP Chat - {nick}")

    # ===== Attach File =====
    def attach_file(self):
        if not self.connected:
            messagebox.showwarning("Tidak Terhubung", "Hubungkan ke server terlebih dahulu!")
            return
        
        file_path = filedialog.askopenfilename(title="Pilih file untuk dikirim")
        if not file_path:
            return
        
        file_size = os.path.getsize(file_path)
        
        # Validasi ukuran file
        if file_size > MAX_FILE_SIZE:
            messagebox.showerror("File Terlalu Besar", 
                f"Ukuran file maksimal adalah {MAX_FILE_SIZE / 1024 / 1024:.1f} MB")
            return
        
        self.send_file(file_path)

    # ===== Kirim File =====
    def send_file(self, file_path):
        try:
            filename = os.path.basename(file_path)
            
            # Baca file dan encode ke base64
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            file_base64 = base64.b64encode(file_data).decode('utf-8')
            
            # Buat pesan JSON untuk file
            file_msg = {
                'type': 'FILE',
                'filename': filename,
                'size': len(file_data),
                'data': file_base64
            }
            
            # Kirim sebagai single line JSON
            json_str = json.dumps(file_msg)
            self.sock.sendall((json_str + "\n").encode('utf-8'))
            
            self.display_message(f"[Mengirim file: {filename} ({len(file_data) / 1024:.1f} KB)]")
            self.label_status.config(text=f"✓ File terkirim: {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Gagal mengirim file: {e}")
            self.display_message(f"[Error mengirim file: {e}]")

    # ===== Terima pesan/file dari server =====
    def receive_messages(self):
        buffer = ""
        while self.connected:
            try:
                data = self.sock.recv(4096)
                if not data:
                    self.master.after(0, lambda: self.display_message("[Terputus dari server]"))
                    break
                buffer += data.decode("utf-8", errors="replace")
                
                # Proses line per line
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Cek apakah ini file JSON atau text biasa
                    if line.startswith('{'):
                        try:
                            msg_obj = json.loads(line)
                            if msg_obj.get('type') == 'FILE':
                                self.master.after(0, lambda m=msg_obj: self.handle_received_file(m))
                            else:
                                self.master.after(0, lambda l=line: self.display_message(l))
                        except json.JSONDecodeError:
                            self.master.after(0, lambda l=line: self.display_message(l))
                    else:
                        self.master.after(0, lambda l=line: self.display_message(l))
                        
            except Exception as e:
                self.master.after(0, lambda: self.display_message(f"[Error koneksi: {e}]"))
                break
        self.connected = False

    # ===== Handle File Diterima =====
    def handle_received_file(self, file_msg):
        try:
            filename = file_msg.get('filename', 'unknown')
            file_base64 = file_msg.get('data', '')
            sender = file_msg.get('sender', 'Unknown')
            
            # Decode file
            file_data = base64.b64decode(file_base64)
            
            # Simpan file
            file_path = os.path.join(self.file_transfer_dir, filename)
            
            # Jika file sudah ada, tambahkan counter
            if os.path.exists(file_path):
                name, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(f"{name}_{counter}{ext}"):
                    counter += 1
                file_path = os.path.join(self.file_transfer_dir, f"{name}_{counter}{ext}")
            
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            display_text = f"[File diterima dari {sender}: {filename} ({len(file_data) / 1024:.1f} KB)] → {file_path}"
            self.display_message(display_text)
            self.label_status.config(text=f"✓ File diterima: {filename}")
            
        except Exception as e:
            self.display_message(f"[Error menerima file: {e}]")

    # ===== Tampilkan pesan ke area chat =====
    def display_message(self, message):
        if not message.strip():
            return
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, message + "\n")
        self.text_area.see(tk.END)
        self.text_area.config(state=tk.DISABLED)

    # ===== Kirim pesan =====
    def send_message(self, event=None):
        msg = self.entry_message.get().strip()
        if not msg:
            return
        try:
            # Kirim sebagai JSON untuk konsistensi
            msg_obj = {'type': 'TEXT', 'content': msg}
            json_str = json.dumps(msg_obj)
            self.sock.sendall((json_str + "\n").encode('utf-8'))
            
            self.display_message(f"{self.nickname}: {msg}")
            self.entry_message.delete(0, tk.END)
            
            if msg.lower() == "/quit":
                self.disconnect()
        except Exception as e:
            self.display_message(f"[Gagal mengirim pesan: {e}]")

    # ===== Putuskan koneksi =====
    def disconnect(self):
        if self.connected and self.sock:
            try:
                self.sock.sendall("/quit\n".encode("utf-8"))
                self.sock.close()
            except:
                pass
        self.connected = False
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()
