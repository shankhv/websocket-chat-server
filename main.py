from fastapi import FastAPI, WebSocket
import json
import asyncio
import time
import logging
import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI()

chat_rooms = {}
topic_messages = {}


def make_unique_username(username, topic):
    if topic not in chat_rooms:
        return username

    # If username not taken, it's unique
    if username not in chat_rooms[topic]:
        return username

    # Username is taken, so add numbers until we find a free one
    number = 2
    while f"{username}#{number}" in chat_rooms[topic]:
        number = number + 1

    return f"{username}#{number}"


async def delete_message_later(message, topic):
    await asyncio.sleep(30)  # Wait 30 seconds

    # Remove message from our storage
    if topic in topic_messages and message in topic_messages[topic]:
        topic_messages[topic].remove(message)
        logger.info(f"Message expired from {message['username']}")


async def send_message_to_everyone(message, topic, sender_name):
    if topic not in chat_rooms:
        return

    # Store message
    if topic not in topic_messages:
        topic_messages[topic] = []
    topic_messages[topic].append(message)

    # Start a timer to delete this message in 30 seconds
    asyncio.create_task(delete_message_later(message, topic))

    # Print the whole JSON message
    print(f"📨 Sending message: {json.dumps(message)}")

    # Send to all users in topic except sender
    disconnected_users = []
    for username, websocket in chat_rooms[topic].items():
        if username == sender_name:
            continue

        try:
            await websocket.send_json(message)
        except:
            # Mark disconnected users for cleanup
            disconnected_users.append(username)

    # Cleanup disconnected users
    for username in disconnected_users:
        if topic in chat_rooms and username in chat_rooms[topic]:
            del chat_rooms[topic][username]


async def send_topic_list(websocket):
    response = "Active Topics:\n"

    # If no topics exist
    if len(chat_rooms) == 0:
        response = response + "No active topics"
    else:
        # List each topic and how many users
        for topic_name, users in chat_rooms.items():
            user_count = len(users)
            response = response + f"{topic_name} ({user_count} users)\n"

    # Send as plain text
    await websocket.send_text(response.strip())


def log_server_status():
    """Log current server status - active users and topics"""
    total_users = sum(len(users) for users in chat_rooms.values())
    total_topics = len(chat_rooms)

    # Build topic summary
    topic_summary = []
    for topic_name, users in chat_rooms.items():
        user_count = len(users)
        topic_summary.append(f"{topic_name}({user_count})")

    topics_str = ", ".join(topic_summary) if topic_summary else "No active topics"

    logger.info(f"Active users: {total_users} | Active topics: {total_topics} | Topics: {topics_str}")


@app.websocket("/ws")
async def chat_endpoint(websocket: WebSocket):
    username = None
    topic = None

    try:
        # Step 1: Accept the connection
        await websocket.accept()

        # Step 2: Get their username and topic
        first_message = await websocket.receive_text()

        try:
            # Convert JSON text to Python dictionary
            user_info = json.loads(first_message)
            username = user_info.get("username")
            topic = user_info.get("topic")

            # Make sure they sent both username and topic
            if not username or not topic:
                await websocket.send_json({"error": "Need username and topic!"})
                await websocket.close()
                return

        except:
            # If JSON is broken, tell them and close
            await websocket.send_json({"error": "Invalid JSON format"})
            await websocket.close()
            return

        # Step 3: Make username unique if needed
        original_username = username
        username = make_unique_username(username, topic)

        # Step 4: Add user to the chat room
        if topic not in chat_rooms:
            chat_rooms[topic] = {}
            topic_messages[topic] = []

        chat_rooms[topic][username] = websocket

        # Log server status after user join
        log_server_status()

        # Tell user if we changed their name
        if username != original_username:
            await websocket.send_json({
                "system": f"Your username is now '{username}' (original was taken)"
            })

        # Step 5: Keep receiving messages forever
        while True:
            # Wait for a message from this user
            data = await websocket.receive_text()

            # Check if it's the /list command
            if data.strip() == "/list":
                await send_topic_list(websocket)
                continue

            # Try to read the message
            try:
                # Convert JSON to dictionary
                message_data = json.loads(data)
                text = message_data.get("message", "")

                # If message is empty, skip it
                if not text:
                    continue

                # Create message object with username and time
                message = {
                    "username": username,
                    "message": text,
                    "timestamp": message_data.get("timestamp", int(time.time()))
                }

                # Send to everyone in the topic
                await send_message_to_everyone(message, topic, username)

                # Tell sender it was delivered
                await websocket.send_json({
                    "status": "delivered",
                    "message": text,
                    "timestamp": message["timestamp"]
                })

            except json.JSONDecodeError:
                # If JSON is broken, tell them
                await websocket.send_json({"error": "Invalid JSON"})
            except Exception as e:
                pass  # Silent error handling

    except Exception as e:
        # Connection closed or error happened
        pass

    finally:
        # Step 6: Clean up when user leaves
        if username and topic:
            # Remove user from topic
            if topic in chat_rooms and username in chat_rooms[topic]:
                del chat_rooms[topic][username]

                # If topic is now empty, delete it
                if len(chat_rooms[topic]) == 0:
                    del chat_rooms[topic]
                    if topic in topic_messages:
                        del topic_messages[topic]

                # Log server status after user leave
                log_server_status()


# Start the server when you run this file
if __name__ == "__main__":

    print("=" * 50)
    print("🚀 Starting Chat Server...")
    print("=" * 50)

    # Log initial server status
    logger.info("Server started - Waiting for connections...")

    uvicorn.run(app, host="0.0.0.0", port=8000)