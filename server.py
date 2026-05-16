import asyncio
import json
from rutp import RUTPServer, RUTPConnection

users = {}

async def client_handler(conn: RUTPConnection):
    queue = asyncio.Queue()
    conn.on_data = lambda d: queue.put_nowait(d)
    username = None

    try:
        while True:
            data = await queue.get()
            msg = json.loads(data.decode())
            if msg['cmd'] == 'register':
                username = msg['username']
                users[username] = conn
                conn.send(json.dumps({'type': 'ok', 'message': f'Welcome {username}'}).encode())
            elif msg['cmd'] == 'message':
                target = msg['to']
                if target in users:
                    users[target].send(json.dumps({'from': username, 'text': msg['text']}).encode())
                else:
                    conn.send(json.dumps({'type': 'error', 'message': f'User {target} not found'}).encode())
    except asyncio.CancelledError:
        if username:
            users.pop(username, None)
        conn.close()
        raise

async def main():
    loop = asyncio.get_running_loop()
    server = RUTPServer(loop, on_connection=lambda conn: asyncio.create_task(client_handler(conn)))
    await server.listen(8888)
    await asyncio.Event().wait()

asyncio.run(main())
