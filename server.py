#!/usr/bin/env python3
import asyncio
import json
import logging
import sys
import os
import sqlite3
from typing import Dict, Optional, Tuple
from rutp import RUTPServer, RUTPConnection, ConnState

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logging.getLogger("rutp").setLevel(logging.WARNING)
logger = logging.getLogger("ChatServer")

USER_DB_FILE = "users.json"
active_users: Dict[int, Tuple[RUTPConnection, dict]] = {}
# Для ограничения количества соединений с IP
ip_connections: Dict[str, int] = {}
MAX_CONNS_PER_IP = 5

DB_FILE = "chat_history.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER NOT NULL,
            to_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_from_to ON messages(from_id, to_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_to_from ON messages(to_id, from_id)')
    conn.commit()
    conn.close()

init_db()

def save_message(from_id: int, to_id: int, text: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO messages (from_id, to_id, message) VALUES (?, ?, ?)", (from_id, to_id, text))
    conn.commit()
    conn.close()
    logger.debug(f"Saved message {from_id}->{to_id}")

def get_message_history(user1: int, user2: int, limit: int = 100) -> list:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT from_id, message, timestamp
        FROM messages
        WHERE (from_id = ? AND to_id = ?) OR (from_id = ? AND to_id = ?)
        ORDER BY timestamp ASC
        LIMIT ?
    ''', (user1, user2, user2, user1, limit))
    rows = c.fetchall()
    conn.close()
    return [{"from": row[0], "text": row[1], "timestamp": row[2]} for row in rows]

def load_users() -> dict:
    if not os.path.exists(USER_DB_FILE):
        return {}
    with open(USER_DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users: dict) -> None:
    with open(USER_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def generate_new_id(users: dict) -> int:
    if not users:
        return 1
    return max(int(uid) for uid in users.keys()) + 1

async def send_message(conn: RUTPConnection, msg_dict: dict) -> bool:
    try:
        if conn._transport is None or conn._remote_addr is None:
            return False
        conn.send(json.dumps(msg_dict, ensure_ascii=False).encode())
        logger.debug(f"Sent to {conn._remote_addr}: {msg_dict.get('type')}")
        return True
    except Exception as e:
        logger.error(f"Send error: {e}")
        return False

async def broadcast_user_list() -> None:
    online_list = [{"id": uid, "name": info["name"]} for uid, (conn, info) in active_users.items() if conn._transport is not None]
    message = {"type": "user_list", "users": online_list}
    to_remove = []
    for uid, (conn, info) in active_users.items():
        if not await send_message(conn, message):
            to_remove.append(uid)
    for uid in to_remove:
        del active_users[uid]
    logger.info(f"Broadcasted user list: {online_list}")

async def handle_client(conn: RUTPConnection):
    addr = conn._remote_addr
    ip = addr[0]
    # Ограничение количества соединений с одного IP
    ip_connections[ip] = ip_connections.get(ip, 0) + 1
    if ip_connections[ip] > MAX_CONNS_PER_IP:
        logger.warning(f"Too many connections from {ip}, rejecting")
        ip_connections[ip] -= 1
        conn.abort()
        return

    logger.info(f"New client from {addr}")
    while conn._state != ConnState.ESTABLISHED:
        await asyncio.sleep(0.05)
    logger.info(f"Connection {addr} established")

    queue = asyncio.Queue()
    conn.on_data = lambda data: asyncio.create_task(queue.put(data))
    user_id: Optional[int] = None
    user_name: Optional[str] = None

    try:
        while True:
            raw = await queue.get()
            try:
                msg = json.loads(raw.decode())
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {addr}: {raw[:100]}")
                await send_message(conn, {"type": "error", "message": "Invalid JSON"})
                continue
            cmd = msg.get("type")
            logger.debug(f"Command {cmd} from {addr}")

            if cmd == "register":
                # ... (без изменений)
                login = msg.get("login")
                password = msg.get("password")
                name = msg.get("name")
                age = msg.get("age")
                if not all([login, password, name, age]):
                    await send_message(conn, {"type": "error", "message": "Missing fields"})
                    continue
                users = load_users()
                existing = None
                for uid, data in users.items():
                    if data.get("login") == login:
                        existing = uid
                        break
                if existing is not None:
                    await send_message(conn, {"type": "error", "message": "Login already exists"})
                    continue
                new_id = generate_new_id(users)
                users[str(new_id)] = {"login": login, "password": password, "name": name, "age": age}
                save_users(users)
                await send_message(conn, {"type": "register_ok", "user_id": new_id, "name": name})
                logger.info(f"Registered {login} -> ID {new_id}")

            elif cmd == "login":
                login = msg.get("login")
                password = msg.get("password")
                if not login or not password:
                    await send_message(conn, {"type": "error", "message": "Missing login/password"})
                    continue
                users = load_users()
                found_id = None
                user_data = None
                for uid, data in users.items():
                    if data.get("login") == login and data.get("password") == password:
                        found_id = int(uid)
                        user_data = data
                        break
                if found_id is None:
                    await send_message(conn, {"type": "error", "message": "Invalid login or password"})
                    continue
                # Вытеснение старого соединения
                if found_id in active_users:
                    old_conn, _ = active_users[found_id]
                    logger.info(f"Kicking old connection for user {found_id} from {old_conn._remote_addr}")
                    await send_message(old_conn, {"type": "error", "message": "Logged in elsewhere"})
                    try:
                        await asyncio.wait_for(old_conn.close(), timeout=1.0)
                    except:
                        old_conn.abort()
                    del active_users[found_id]
                    await asyncio.sleep(0.1)  # дать время на закрытие
                user_id = found_id
                user_name = user_data["name"]
                active_users[user_id] = (conn, {"name": user_name, "login": login})

                all_users_list = []
                for uid, data in users.items():
                    all_users_list.append({
                        "id": int(uid),
                        "name": data["name"],
                        "online": int(uid) in active_users
                    })
                await send_message(conn, {
                    "type": "login_ok",
                    "user_id": user_id,
                    "name": user_name,
                    "all_users": all_users_list
                })
                logger.info(f"User {login} (ID {user_id}) logged in")
                await broadcast_user_list()

            elif cmd == "message":
                # ... (без изменений)
                if user_id is None:
                    await send_message(conn, {"type": "error", "message": "Not logged in"})
                    continue
                target_id = msg.get("to_id")
                text = msg.get("text", "")
                if target_id is None or not text.strip():
                    continue
                target_id = int(target_id)
                save_message(user_id, target_id, text)
                if target_id in active_users:
                    target_conn, _ = active_users[target_id]
                    if target_conn._transport is not None:
                        await send_message(target_conn, {
                            "type": "message",
                            "from_id": user_id,
                            "from_name": user_name,
                            "text": text
                        })
                        logger.debug(f"Message {user_id} -> {target_id}: {text[:50]} (online)")
                    else:
                        del active_users[target_id]
                        await broadcast_user_list()
                        await send_message(conn, {"type": "error", "message": f"User {target_id} disconnected"})
                else:
                    logger.info(f"Message saved for offline user {target_id}")

            elif cmd == "get_history":
                if user_id is None:
                    await send_message(conn, {"type": "error", "message": "Not logged in"})
                    continue
                other_id = msg.get("with_id")
                limit = msg.get("limit", 100)
                if other_id is None:
                    continue
                history = get_message_history(user_id, int(other_id), limit)
                await send_message(conn, {
                    "type": "history",
                    "with_id": other_id,
                    "messages": history
                })
                logger.debug(f"Sent history for {user_id} <-> {other_id} ({len(history)} messages)")

            else:
                await send_message(conn, {"type": "error", "message": f"Unknown command {cmd}"})

    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Error in handle_client: {e}", exc_info=True)
    finally:
        if user_id is not None and user_id in active_users:
            del active_users[user_id]
            logger.info(f"User {user_id} disconnected")
            await broadcast_user_list()
        # Уменьшаем счётчик соединений с IP
        ip_connections[ip] = ip_connections.get(ip, 1) - 1
        if ip_connections[ip] == 0:
            del ip_connections[ip]
        try:
            await conn.close()
        except:
            conn.abort()
        logger.info(f"Connection closed for {addr}")

async def main():
    loop = asyncio.get_running_loop()
    server = RUTPServer(loop, on_connection=lambda c: asyncio.create_task(handle_client(c)))
    await server.listen(8888)
    logger.info("RUTP Chat Server started on port 8888")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
