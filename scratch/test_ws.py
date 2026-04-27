import asyncio
import websockets
import json
import base64

async def test_ws():
    uri = "ws://127.0.0.1:8088/api/v1/recognition/ws/mobile"
    print(f"Connecting to {uri}")
    try:
        async with websockets.connect(uri) as ws:
            print("Connected!")
            
            # Send start
            await ws.send(json.dumps({"camera_id": "test_cam", "action": "start"}))
            response = await ws.recv()
            print("Response to start:", response)
            
            # Send an image frame
            img_data = b"x" * 1000 # Dummy invalid image
            b64 = base64.b64encode(img_data).decode()
            await ws.send(json.dumps({"camera_id": "test_cam", "image": f"data:image/jpeg;base64,{b64}"}))
            
            # Send stop
            await ws.send(json.dumps({"camera_id": "test_cam", "action": "stop"}))
            response = await ws.recv()
            print("Response to stop:", response)
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e.code} - {e.reason}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_ws())
