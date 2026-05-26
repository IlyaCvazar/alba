#!/usr/bin/env python3
"""
RUTP Terminal Chat Client (исправленная версия)
-----------------------------------------------
- После регистрации автоматически выполняет вход.
- Корректно обрабатывает состояние logged_in.
- Добавлена команда 'whoami' для отображения своего ID.
"""

import asyncio
import json
import sys
from typing import Optional

from rutp import RUTPConnection

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8888


class TerminalColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class RUTPTerminalClient:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.conn: Optional[RUTPConnection] = None
        self.user_id: Optional[int] = None
        self.user_name: Optional[str] = None
        self.logged_in = False
        self.receive_task: Optional[asyncio.Task] = None
        self.running = True
        # Сохраняем последние учётные данные для автоматического входа после регистрации
        self._pending_login: Optional[tuple] = None

    async def connect(self):
        self.conn = RUTPConnection(self.loop)
        await self.conn.connect(SERVER_HOST, SERVER_PORT)
        print(f"{TerminalColors.OKGREEN}Connected to server {SERVER_HOST}:{SERVER_PORT}{TerminalColors.ENDC}")
        self.receive_task = asyncio.create_task(self._receive_messages())

    async def _receive_messages(self):
        queue = asyncio.Queue()
        self.conn.on_data = lambda data: asyncio.create_task(queue.put(data))

        while self.running and self.conn:
            try:
                raw = await queue.get()
                msg = json.loads(raw.decode())
                await self._handle_incoming(msg)
            except json.JSONDecodeError:
                print(f"{TerminalColors.FAIL}Invalid JSON received{TerminalColors.ENDC}")
            except Exception as e:
                if self.running:
                    print(f"{TerminalColors.FAIL}Error in receive: {e}{TerminalColors.ENDC}")
                break

    async def _handle_incoming(self, msg: dict):
        msg_type = msg.get("type")

        if msg_type == "message":
            from_id = msg.get("from_id")
            from_name = msg.get("from_name", str(from_id))
            text = msg.get("text", "")
            print(f"\n{TerminalColors.OKBLUE}[{from_name} (ID {from_id})]: {text}{TerminalColors.ENDC}")
            print("> ", end="", flush=True)

        elif msg_type == "user_list":
            users = msg.get("users", [])
            print(f"\n{TerminalColors.OKGREEN}--- Online users ({len(users)}) ---{TerminalColors.ENDC}")
            for u in users:
                print(f"  {u['id']}: {u['name']}")
            print("> ", end="", flush=True)

        elif msg_type == "login_ok":
            self.user_id = msg.get("user_id")
            self.user_name = msg.get("name")
            self.logged_in = True
            print(f"{TerminalColors.OKGREEN}Login successful! Your ID: {self.user_id}, Name: {self.user_name}{TerminalColors.ENDC}")
            print("> ", end="", flush=True)

        elif msg_type == "register_ok":
            # Регистрация успешна, теперь автоматически логинимся
            self.user_id = msg.get("user_id")
            self.user_name = msg.get("name")
            # Если есть сохранённые учётные данные, отправляем логин
            if self._pending_login:
                login, password = self._pending_login
                await self.login(login, password)
                self._pending_login = None
            else:
                # На всякий случай, если регистрация без сохранения (не должно случиться)
                print(f"{TerminalColors.OKGREEN}Registration successful! Your ID: {self.user_id}, Name: {self.user_name}{TerminalColors.ENDC}")
                print(f"{TerminalColors.WARNING}Please log in manually using 'login <login> <password>'{TerminalColors.ENDC}")
                print("> ", end="", flush=True)

        elif msg_type == "error":
            print(f"{TerminalColors.FAIL}Error: {msg.get('message')}{TerminalColors.ENDC}")
            print("> ", end="", flush=True)

    async def send_json(self, data: dict):
        if self.conn:
            self.conn.send(json.dumps(data, ensure_ascii=False).encode())

    async def register(self, login: str, password: str, name: str, age: str):
        # Сохраняем данные для последующего автоматического входа
        self._pending_login = (login, password)
        await self.send_json({
            "type": "register",
            "login": login,
            "password": password,
            "name": name,
            "age": age
        })

    async def login(self, login: str, password: str):
        await self.send_json({
            "type": "login",
            "login": login,
            "password": password
        })

    async def send_message(self, to_id: int, text: str):
        if not self.logged_in:
            print(f"{TerminalColors.WARNING}You are not logged in. Use 'login' first.{TerminalColors.ENDC}")
            return
        await self.send_json({
            "type": "message",
            "to_id": to_id,
            "text": text
        })

    async def show_help(self):
        help_text = f"""
{TerminalColors.BOLD}Available commands:{TerminalColors.ENDC}
  {TerminalColors.OKGREEN}register <login> <password> <name> <age>{TerminalColors.ENDC}  - create new account and auto-login
  {TerminalColors.OKGREEN}login <login> <password>{TerminalColors.ENDC}                 - login to existing account
  {TerminalColors.OKGREEN}send <to_id> <message>{TerminalColors.ENDC}                  - send a message
  {TerminalColors.OKGREEN}users{TerminalColors.ENDC}                                   - show online users
  {TerminalColors.OKGREEN}whoami{TerminalColors.ENDC}                                  - show your ID and name
  {TerminalColors.OKGREEN}quit / exit{TerminalColors.ENDC}                            - exit
        """
        print(help_text)

    async def process_input(self, line: str):
        if not line.strip():
            return False
        parts = line.strip().split()
        cmd = parts[0].lower()

        if cmd in ("quit", "exit"):
            self.running = False
            if self.conn:
                await self.conn.close()
            print("Goodbye!")
            return True

        elif cmd == "register":
            if len(parts) != 5:
                print(f"{TerminalColors.WARNING}Usage: register <login> <password> <name> <age>{TerminalColors.ENDC}")
            else:
                _, login, password, name, age = parts
                await self.register(login, password, name, age)

        elif cmd == "login":
            if len(parts) != 3:
                print(f"{TerminalColors.WARNING}Usage: login <login> <password>{TerminalColors.ENDC}")
            else:
                _, login, password = parts
                await self.login(login, password)

        elif cmd == "send":
            if len(parts) < 3:
                print(f"{TerminalColors.WARNING}Usage: send <to_id> <message>{TerminalColors.ENDC}")
            else:
                try:
                    to_id = int(parts[1])
                    message = " ".join(parts[2:])
                    await self.send_message(to_id, message)
                except ValueError:
                    print(f"{TerminalColors.WARNING}Invalid ID. Must be a number.{TerminalColors.ENDC}")

        elif cmd == "users":
            print(f"{TerminalColors.WARNING}User list is broadcasted automatically. If empty, try logging in first.{TerminalColors.ENDC}")

        elif cmd == "whoami":
            if self.logged_in:
                print(f"{TerminalColors.OKGREEN}Your ID: {self.user_id}, Name: {self.user_name}{TerminalColors.ENDC}")
            else:
                print(f"{TerminalColors.WARNING}Not logged in.{TerminalColors.ENDC}")

        elif cmd == "help":
            await self.show_help()

        else:
            print(f"{TerminalColors.WARNING}Unknown command: {cmd}. Type 'help'.{TerminalColors.ENDC}")

        return False

    async def input_loop(self):
        while self.running:
            line = await self.loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            exit_now = await self.process_input(line.strip())
            if exit_now:
                break
            if self.running and self.logged_in:
                print("> ", end="", flush=True)

    async def run(self):
        try:
            await self.connect()
            print(f"{TerminalColors.BOLD}Welcome to RUTP Chat Terminal!{TerminalColors.ENDC}")
            await self.show_help()
            print("> ", end="", flush=True)
            await self.input_loop()
        except ConnectionRefusedError:
            print(f"{TerminalColors.FAIL}Cannot connect to server. Make sure the server is running on {SERVER_HOST}:{SERVER_PORT}{TerminalColors.ENDC}")
        except Exception as e:
            print(f"{TerminalColors.FAIL}Unexpected error: {e}{TerminalColors.ENDC}")
        finally:
            if self.receive_task:
                self.receive_task.cancel()
            if self.conn:
                await self.conn.close()


async def main():
    loop = asyncio.get_running_loop()
    client = RUTPTerminalClient(loop)
    await client.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")