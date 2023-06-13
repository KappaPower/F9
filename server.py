import os
from aiohttp import web
import asyncio

WS_FILE = os.path.join(os.path.dirname(__file__), "websocket.html")


async def websocket_handler(request: web.Request):
    resp = web.WebSocketResponse()
    available = resp.can_prepare(request)
    if not available:
        with open(WS_FILE, "rb") as fp:
            return web.Response(body=fp.read(), content_type="text/html")

    await resp.prepare(request)
    await resp.send_str("Welcome")

    try:
        url = f"http://{request.host}/news"
        print(f"Server started at {url}")
        for ws in request.app["sockets"]:
            await ws.send_str("New client joined")
        request.app["sockets"].append(resp)

        async for msg in resp:
            if msg.type == web.WSMsgType.TEXT:
                for ws in request.app["sockets"]:
                    if ws is not resp:
                        await ws.send_str(msg.data)
            else:
                return resp
        return resp

    finally:
        request.app["sockets"].remove(resp)
        print("Client disconnected.")
        for ws in request.app["sockets"]:
            await ws.send_str("Client disconnected.")


async def on_shutdown(app: web.Application):
    for ws in app["sockets"]:
        await ws.close()


def create_app():
    app = web.Application()
    app["sockets"] = []
    app.router.add_get("/news", websocket_handler)
    app.on_shutdown.append(on_shutdown)
    return app


if __name__ == "__main__":
    app = create_app()
    runner = web.AppRunner(app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, 'localhost', 8080)
    print(f"Server started at http://localhost:8080/news")
    loop.run_until_complete(site.start())
    loop.run_forever()
