import asyncio
import json
import sys
from rutp import RUTPConnection

async def main():
    loop = asyncio.get_running_loop()
    client = RUTPConnection(loop)
    await client.connect('127.0.0.1', 8888)
    await asyncio.sleep(0.1)  # ждём завершения handshake

    queue = asyncio.Queue()
    client.on_data = lambda data: queue.put_nowait(data)

    async def receive():
        while True:
            data = await queue.get()
            try:
                msg = json.loads(data.decode())
                if 'from' in msg:
                    print(f"\n[Сообщение от {msg['from']}]: {msg['text']}\n> ", end='', flush=True)
                elif msg.get('type') == 'ok':
                    print(f"\n[OK] {msg['message']}\n> ", end='', flush=True)
            except:
                pass

    asyncio.create_task(receive())

    async def ainput():
        return await loop.run_in_executor(None, sys.stdin.readline)

    print("Чат. Команды: reg <имя>, send <кому> <текст>, exit")
    while True:
        line = await ainput()
        if not line:
            break
        line = line.strip()
        if line.startswith('reg '):
            name = line.split()[1]
            client.send(json.dumps({'cmd': 'register', 'username': name}).encode())
        elif line.startswith('send '):
            parts = line.split(maxsplit=2)
            if len(parts) == 3:
                _, to, text = parts
                client.send(json.dumps({'cmd': 'message', 'to': to, 'text': text}).encode())
        elif line == 'exit':
            break

    await client.close()

asyncio.run(main())
