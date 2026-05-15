#!/usr/bin/env python3
import asyncio
import json
import logging
from typing import Dict

from rutp import RUTPServer, RUTPConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessengerServer:
    def __init__(self):
        self.users: Dict[str, RUTPConnection] = {}
        self.conn_to_user: Dict[RUTPConnection, str] = {}

    async def start(self, port: int):
        loop = asyncio.get_running_loop()
        self.server = RUTPServer(loop, on_connection=self._handle_new_connection)
        await self.server.listen(port)
        logger.info(f"Messenger server listening on port {port}")

    def _handle_new_connection(self, conn: RUTPConnection):
        logger.info(f"New client connected from {conn._remote_addr}")
        asyncio.create_task(self._client_handler(conn))

    async def _client_handler(self, conn: RUTPConnection):
        queue = asyncio.Queue()
        conn.on_data = lambda data: queue.put_nowait(data)

        try:
            while True:
                data = await queue.get()
                try:
                    msg = json.loads(data.decode())
                    await self._process_command(conn, msg)
                except json.JSONDecodeError:
                    await self._send_error(conn, "Invalid JSON")
                except Exception as e:
                    logger.exception("Error processing command")
                    await self._send_error(conn, str(e))
        except asyncio.CancelledError:
            username = self.conn_to_user.pop(conn, None)
            if username:
                self.users.pop(username, None)
                logger.info(f"User {username} disconnected")
            conn.close()
            raise
        except Exception:
            logger.exception("Unexpected error")
            conn.close()

    async def _process_command(self, conn: RUTPConnection, msg: dict):
        cmd = msg.get("cmd")
        if cmd == "register":
            username = msg.get("username")
            if not username:
                await self._send_error(conn, "Username required")
                return
            if username in self.users:
                await self._send_error(conn, "Username already taken")
                return
            self.users[username] = conn
            self.conn_to_user[conn] = username
            await self._send_ok(conn, f"Registered as {username}")
            logger.info(f"User registered: {username}")

        elif cmd == "search":
            pattern = msg.get("pattern", "")
            matching = [u for u in self.users.keys() if pattern.lower() in u.lower()]
            await self._send_response(conn, {"type": "search_result", "users": matching})

        elif cmd == "message":
            target = msg.get("to")
            text = msg.get("text")
            if not target or not text:
                await self._send_error(conn, "Missing 'to' or 'text'")
                return
            sender = self.conn_to_user.get(conn)
            if not sender:
                await self._send_error(conn, "You must register first")
                return
            recipient_conn = self.users.get(target)
            if not recipient_conn:
                await self._send_error(conn, f"User '{target}' not found or offline")
                return
            forward = {
                "type": "message",
                "from": sender,
                "text": text
            }
            recipient_conn.send(json.dumps(forward).encode())
            await self._send_ok(conn, f"Message sent to {target}")

        else:
            await self._send_error(conn, f"Unknown command: {cmd}")

    async def _send_ok(self, conn: RUTPConnection, message: str):
        await self._send_response(conn, {"type": "ok", "message": message})

    async def _send_error(self, conn: RUTPConnection, error: str):
        await self._send_response(conn, {"type": "error", "error": error})

    async def _send_response(self, conn: RUTPConnection, resp: dict):
        conn.send(json.dumps(resp).encode())


async def main():
    server = MessengerServer()
    await server.start(8888)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())