#!/usr/bin/env python3
import asyncio
import json
import sys
import logging
from rutp import RUTPConnection, ConnState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessengerClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.conn = None
        self.username = None
        self._connected = asyncio.Event()

    async def connect(self):
        loop = asyncio.get_running_loop()
        self.conn = RUTPConnection(loop)
        # Фоновая задача для отслеживания состояния
        asyncio.create_task(self._watch_state())
        await self.conn.connect(self.host, self.port)
        # Ждём перехода в ESTABLISHED (максимум 5 секунд)
        try:
            await asyncio.wait_for(self._connected.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            raise RuntimeError("Handshake timeout")
        logger.info(f"Connected to {self.host}:{self.port}")
        asyncio.create_task(self._receiver())

    async def _watch_state(self):
        while True:
            if self.conn and self.conn._state == ConnState.ESTABLISHED:
                self._connected.set()
                break
            await asyncio.sleep(0.05)

    async def _receiver(self):
        queue = asyncio.Queue()
        self.conn.on_data = lambda data: queue.put_nowait(data)
        while True:
            data = await queue.get()
            try:
                msg = json.loads(data.decode())
                if msg.get("type") == "message":
                    sender = msg.get("from", "?")
                    text = msg.get("text", "")
                    print(f"\n[Message from {sender}]: {text}")
                    print("> ", end="", flush=True)
                elif msg.get("type") == "ok":
                    print(f"[OK] {msg.get('message')}")
                elif msg.get("type") == "error":
                    print(f"[ERROR] {msg.get('error')}")
                elif msg.get("type") == "search_result":
                    users = msg.get("users", [])
                    if users:
                        print("Found users: " + ", ".join(users))
                    else:
                        print("No users found.")
            except Exception as e:
                logger.error(f"Parse error: {e}")

    async def _send_command(self, cmd_dict: dict):
        if self.conn:
            self.conn.send(json.dumps(cmd_dict).encode())

    async def run(self):
        await self.connect()
        print("RUTP Messenger Client")
        print("Commands: register <name>, search <pattern>, send <user> <message>, exit")
        loop = asyncio.get_running_loop()
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=2)
            cmd = parts[0].lower()
            if cmd == "exit":
                await self.conn.close()
                print("Bye!")
                break
            elif cmd == "register" and len(parts) == 2:
                username = parts[1]
                await self._send_command({"cmd": "register", "username": username})
                self.username = username
            elif cmd == "search" and len(parts) == 2:
                pattern = parts[1]
                await self._send_command({"cmd": "search", "pattern": pattern})
            elif cmd == "send" and len(parts) == 3:
                target = parts[1]
                text = parts[2]
                if not self.username:
                    print("You must register first")
                    continue
                await self._send_command({"cmd": "message", "to": target, "text": text})
            else:
                print("Unknown command")

async def main():
    host = "127.0.0.1"
    port = 8888
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    client = MessengerClient(host, port)
    try:
        await client.run()
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        logger.error(f"Client error: {e}")
    finally:
        if client.conn:
            await client.conn.close()

if __name__ == "__main__":
    asyncio.run(main())