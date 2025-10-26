import asyncio
import websockets
import json
from datetime import datetime


async def listen_for_messages(websocket, username):
    try:
        # Keep listening forever
        while True:
            # Wait for a message from the server
            message = await websocket.recv()

            # Clear current input line before showing new message
            print('\r' + ' ' * 80 + '\r', end='')

            try:
                # Try to read it as JSON
                data = json.loads(message)

                # Check what type of message it is
                if "error" in data:
                    # Server sent an error
                    print(f"❌ Error: {data['error']}")

                elif "system" in data:
                    # Server sent a system message
                    print(f"⚠️  System: {data['system']}")

                elif "status" in data:
                    # Our message was delivered!
                    print("✓ Sent!")

                elif "username" in data and "message" in data:
                    # Someone sent a message in our topic
                    sender = data['username']
                    text = data['message']
                    timestamp = data.get('timestamp', 0)
                    time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M')
                    print(f"{time_str} 💬 {sender}: {text}")

            except json.JSONDecodeError:
                # Not JSON, probably plain text (like /list response)
                print(f"{message}")

            # Show the prompt again (ONCE)
            print("You: ", end="", flush=True)

    except websockets.exceptions.ConnectionClosed:
        print("\n\n❌ Disconnected from server")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")


async def send_messages(websocket, username):
    try:
        while True:
            # Wait for user to type something
            message = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: input("")
            )
            # Skip empty messages
            if not message.strip():
                continue

            # Check if user wants to quit
            if message.strip() == "/quit":
                print("\n👋 Goodbye!")
                await websocket.close()
                break

            # Check if user wants to see topic list
            if message.strip() == "/list":
                await websocket.send("/list")
                continue

            # Send the message as JSON
            message_json = {
                "username": username,
                "message": message,
                "timestamp": int(datetime.now().timestamp())
            }
            await websocket.send(json.dumps(message_json))

    except Exception as e:
        print(f"\n❌ Error sending: {e}")


async def run_chat(username, topic):
    server_url = "ws://localhost:8000/ws"

    try:
        # Connect to the server
        print(f"🔌 Connecting to server...")
        websocket = await websockets.connect(server_url)

        # Send our username and topic
        connection_info = {
            "username": username,
            "topic": topic
        }
        await websocket.send(json.dumps(connection_info))

        print(f"✅ Connected as '{username}' to topic '{topic}'")
        print(f"📝 Type messages to chat")
        print(f"💡 Commands: /list (show topics), /quit (exit)")
        print("-" * 50)

        # Show initial prompt
        print("You: ", end="", flush=True)

        # Run both listening and sending at the same time
        await asyncio.gather(
            listen_for_messages(websocket, username),
            send_messages(websocket, username)
        )

    except websockets.exceptions.ConnectionClosed:
        print("\n❌ Connection closed by server")
    except ConnectionRefusedError:
        print("❌ Cannot connect to server - make sure it's running!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")


def main():
    print("=" * 50)
    print("💬 Simple Chat Client")
    print("=" * 50)
    print()

    # Get username and topic from user

    username = input("Enter your username: ").strip()
    topic = input("Enter topic to join: ").strip()

    # Make sure they entered something
    while not username or not topic:
        print("❌ You need to enter both username and topic!")
        username = input("Enter your username: ").strip()
        topic = input("Enter topic to join: ").strip()

    print()

    # Start the chat!
    try:
        asyncio.run(run_chat(username, topic))
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")


# This runs when you execute the file
if __name__ == "__main__":
    main()