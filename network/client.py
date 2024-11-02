from typing import Optional, Tuple
import asyncio
import json
import uuid
import websockets as ws
from network.events import (
    Status,
    Event,
    EventType,
    EventFactory
)
from Definitions import PlayerSpot

class GameClient:
    def __init__(self):
        self.player_id: str = str(uuid.uuid4())
        self.websocket: ws.WebSocketClientProtocol = None
        self.event_queue: asyncio.Queue[Event] = asyncio.Queue()
        self.listen_task: asyncio.Task = None

    async def connect(self, uri: str) -> None:
        self.websocket = await ws.connect(uri)
        self.listen_task = asyncio.create_task(self.listen())
        print("Connected to server")
        
    async def send_event(self, event: Event):
        message = event.model_dump_json()
        print(f'client send event: {message=}')
        await self.websocket.send(message)

    async def join_server(self) -> PlayerSpot:
        print(f"Joining server as {self.player_id}")
        payload_class = EventFactory.get_payload_model(EventType.JOIN)
        join_payload = payload_class(player_id=self.player_id)
        join_event = EventFactory.create_event(EventType.JOIN, join_payload, self.player_id)
        await self.send_event(join_event)
        print("Waiting for server response...")
        response = await self.get_event()
        
        if response.event_type == EventType.STATUS_RESPONSE.value:
            raise Exception(f"Failed to join server: {response.payload.reason}")

        print(f"Joined server as {response.payload.spot}")
        return response.payload.spot
    
    async def leave_server(self):
        print(f"Leaving server as {self.player_id}")
        payload_class = EventFactory.get_payload_model(EventType.LEAVE)
        leave_payload = payload_class(player_id=self.player_id)
        leave_event = EventFactory.create_event(EventType.LEAVE, leave_payload, self.player_id)
        await self.send_event(leave_event)
        print("Waiting for server response...")
        response = await self.get_event()
        
        if response.event_type != EventType.STATUS_RESPONSE.value:
            raise Exception(f"Failed to leave server: {response}")
        
        if response.payload.status != Status.SUCCESS.value:
            raise Exception(f"Failed to leave server: {response.payload.reason}")

        print(f"Left server as {self.player_id}")

    async def listen(self):
        try:
            async for message in self.websocket:
                event_data = json.loads(message)
                event = EventFactory.from_dict(event_data)
                print(f"Received event: {event_data}")
                await self.event_queue.put(event)
        except ws.ConnectionClosed:
            print("Connection closed")
        finally:
            await self.websocket.close()

    async def close(self):
        # send a leave event
        await self.leave_server()
        await self.websocket.close()
        self.listen_task.cancel()  

    async def get_event(self, timeout: float = None) -> Optional[Event]:
        get_event_task = asyncio.create_task(self.event_queue.get())
        try:
            return await asyncio.wait_for(get_event_task, timeout=timeout)
        except asyncio.TimeoutError:
            return None

    def run(self) -> Tuple[PlayerSpot, int]:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # connect to the server
        loop.run_until_complete(self.connect("ws://localhost:6789"))
        # join the server
        player_spot = loop.run_until_complete(self.join_server())
        print(f"Joined as {player_spot}")
        # wait for the game to start
        start_game_event = loop.run_until_complete(self.get_event())
        print(start_game_event)

        return player_spot, start_game_event.payload.seed

def run_client():
    client = GameClient()
    try:
        spot, seed = client.run()
        print(f"Joined as {spot} with seed {seed}")
    except Exception as e:
        print(e)
    finally:
        asyncio.get_event_loop().run_until_complete(client.close())        

if __name__ == "__main__":
    run_client()
