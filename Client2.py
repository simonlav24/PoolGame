
import asyncio
from Client import Client

if __name__ == '__main__':
    host = 'localhost'
    port = 8000

    client = Client()
    asyncio.run(client.start(host, port))

