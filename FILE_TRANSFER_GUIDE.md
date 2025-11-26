# Chat Application with File Transfer - Implementation Guide

## Overview
This guide explains how to add file attachment functionality to your TCP chat application.

## Files Created

### 1. **chat_client_gui_with_files.py** - Enhanced Client
- Added "Attach File" button to send files
- Automatic file reception and storage in `received_files/` directory
- Uses base64 encoding for binary file transfer
- File size limit: 5 MB (configurable)
- Status bar shows transfer progress

### 2. **chat_server_with_files.py** - Enhanced Server
- Receives files from clients
- Broadcasts files to all other connected clients
- Stores files in `server_files/` directory with sender prefix
- Automatic duplicate file name handling

## Key Features

### Protocol Changes
Messages are now sent as JSON with type field:

```json
// Text message
{"type": "TEXT", "content": "Hello world"}

// File transfer
{
  "type": "FILE",
  "filename": "document.pdf",
  "size": 102400,
  "data": "base64encodeddata...",
  "sender": "username"
}
```

### Client Features

#### Sending Files
1. Click "Attach File" button
2. Select file from dialog
3. Client validates file size (max 5 MB)
4. File is base64 encoded and sent via JSON
5. Confirmation message appears in chat

#### Receiving Files
- Automatically saves to `received_files/` directory
- Shows filename, sender, and file size in chat
- Handles duplicate filenames with counter

#### UI Improvements
- Added "Attach File" button next to Send button
- Status bar shows last file operation
- File transfer messages clearly marked in chat
- All messages in scrollable text area

### Server Features

#### File Processing
- Saves received files with sender prefix: `{sender}_{filename}`
- Broadcasts files to all other connected users
- Stores originals in `server_files/` directory
- Logs all file transfers with timestamp

#### Broadcasting
- Files automatically sent to all clients except sender
- Private messages still supported with `/msg` command
- Graceful error handling for failed transfers

## Installation & Setup

### Step 1: Update Your Files
Replace old server and client with new versions:
```powershell
# Backup originals (optional)
Copy-Item chat_server.py chat_server.backup.py
Copy-Item chat_client_gui_final.py chat_client_gui_final.backup.py

# Use new versions
# Option A: Replace the old ones
# Option B: Run new versions alongside (rename them)
```

### Step 2: Start the Server
```powershell
python chat_server_with_files.py
```

Expected output:
```
[2025-11-26 10:30:45] Starting server on 127.0.0.1:65432
[2025-11-26 10:30:45] Server listening...
```

### Step 3: Run Clients
```powershell
# Terminal 1
python chat_client_gui_with_files.py

# Terminal 2
python chat_client_gui_with_files.py
```

## Usage Example

### Sending a File
1. Launch 2+ client instances
2. Each client enters nickname and connects
3. Click "Attach File" button
4. Select a file (e.g., `document.pdf`)
5. File is sent to server
6. Server broadcasts to other clients
7. Receiving clients save to `received_files/` folder

### Sending a Text Message
- Type message in input field
- Press Enter or click "Kirim" button
- Message appears in all clients

## Configuration

### Modify File Size Limit
In `chat_client_gui_with_files.py`, line 21:
```python
MAX_FILE_SIZE = 5 * 1024 * 1024  # Change 5 to desired MB
```

### Change Server Host/Port
**Client** - Line 15-16:
```python
SERVER_HOST = "192.168.166.3"  # Change to your server IP
SERVER_PORT = 65432
```

**Server** - Line 10-11:
```python
HOST = "127.0.0.1"   # Change to "0.0.0.0" for all interfaces
PORT = 65432
```

### Directories Created Automatically
- **Client:** `received_files/` - stores downloaded files
- **Server:** `server_files/` - stores uploaded files

## Implementation Details

### Base64 Encoding
- All binary files converted to base64 text
- Allows transmission as UTF-8 JSON
- Increases payload size by ~33%
- Simpler than chunked binary transfer

### Message Parsing
```python
# Server/Client receives line-by-line
if line.startswith('{'):
    msg_obj = json.loads(line)
    if msg_obj.get('type') == 'FILE':
        # Handle file
    elif msg_obj.get('type') == 'TEXT':
        # Handle text message
```

### Thread Safety
- Uses locks for client dictionary access
- Thread-safe file operations
- Daemon threads for receive operations

## Troubleshooting

### Issue: "File Terlalu Besar" Error
- Check file size limit in client (MAX_FILE_SIZE)
- Increase limit if needed
- Consider splitting large files

### Issue: File Transfer Hangs
- Check network connection
- Verify file size < limit
- Check server disk space

### Issue: Files Not Appearing in Chat
- Verify `received_files/` directory exists
- Check file permissions
- Monitor server logs for errors

### Issue: Connection Refused
- Verify server is running
- Check HOST/PORT settings match
- Check firewall settings

## Potential Enhancements

### 1. **Chunked Transfer (for large files)**
```python
CHUNK_SIZE = 1024 * 64  # 64 KB chunks
# Send file in multiple messages
```

### 2. **File Checksum Verification**
```python
import hashlib
checksum = hashlib.md5(file_data).hexdigest()
# Include in file message for validation
```

### 3. **File Upload Progress Bar**
```python
# Use ttk.Progressbar in Tkinter
# Update during chunked transfer
```

### 4. **Allowed File Types**
```python
ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.doc', '.jpg', '.png'}
if not any(file_path.endswith(ext) for ext in ALLOWED_EXTENSIONS):
    raise ValueError("File type not allowed")
```

### 5. **File Encryption**
```python
from cryptography.fernet import Fernet
cipher = Fernet(key)
encrypted_data = cipher.encrypt(file_data)
```

### 6. **Private File Transfer**
```python
# Extend /msg command for files
# /file <nickname> <filepath>
```

## Security Considerations

⚠️ **Current Limitations:**
- No encryption (files sent in plaintext)
- No authentication (anyone can join with any nickname)
- No access control (all files visible to all clients)
- No rate limiting (spam possible)

### Recommended Improvements:
1. Add SSL/TLS encryption
2. Implement user authentication
3. Add per-user permissions
4. Rate limiting on file uploads
5. Virus scanning for uploaded files
6. File size quotas per user

## Performance Notes

- **Memory:** Each file loaded entirely into RAM
- **Bandwidth:** Base64 increases by 33%
- **Latency:** Single-threaded per client on server
- **Scalability:** Good for small groups (< 50 clients)

## License
Use as-is for educational purposes.
