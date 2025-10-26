### Prerequisites
- Python 3.9+
- Required packages: FastAPI, Uvicorn, websockets 

## Package Installation
```bash
pip install -r requirement.txt
```
## How to Run:

1. Start the Server (Terminal 1)
```bash
   python main.py
```
2. Start Clients (Terminal 2, 3, ...)
 ```bash
   python client_example.py
```
## Tested Scenarios

- **Basic Real-time Messaging:** Users in the same topic can chat in real time. Messages are broadcast to everyone except the sender, who receives a delivery confirmation.  
- **Username Management:** Duplicate usernames in a topic get a numeric suffix (e.g., `alice#2`). The server notifies users if their username is modified.  
- **Topic Room Management:** Use the `/list` command to view active topics with user counts. Topics are automatically removed when all users leave.  
- **Message Lifecycle:** Messages expire and are deleted after 30 seconds. No message is stored beyond its time-to-live (TTL).  
- **Error Handling & Resilience:** Invalid JSON is handled gracefully. Disconnected users are cleaned up without affecting others, keeping the server stable.  
- **Concurrent Operations:** Multiple clients can join different topics simultaneously without cross-talk between rooms.


## Project Structure
```bash
.
├── main.py              # FastAPI WebSocket server
├── client_example.py    # Example client implementation
├── requirement.txt     # Project dependencies
└── README.md           # This file
```

