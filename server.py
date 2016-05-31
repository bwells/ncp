#!/usr/bin/env python

import asyncio
from aiohttp import web
import aiohttp
import json

CONTENT = open('index.html').read().encode('utf8')

connected = set()

last_click = None

async def index(request):
    return web.Response(body=CONTENT)

async def clicked(request):
    global last_click
    click_type = request.GET.get('type', 'single')
    last_click = click_type
    print("received click {}".format(last_click))
    return web.Response()

async def snsclicked(request):
    global last_click

    body = await request.text()
    data = json.loads(body)

    if 'SubscribeURL' in data:
        print("Confirm subscription at: {}").format(data['SubscribeURL'])
    else:
        msg = data['Subject']
        click_type = msg.split(': ')[1].lower()
        last_click = click_type
        print("received click {}".format(last_click))

    return web.Response()

async def clicks(request):
    global connected
    ws = web.WebSocketResponse()
    try:
        connected.add(ws)
        print("connected")

        await ws.prepare(request)

        local_click = last_click
        while True:
            if local_click != last_click:
                local_click = last_click
                ws.send_str(last_click)
            await asyncio.sleep(1)

    finally:
        print("disconnected")
        connected.remove(ws)

    return ws

loop = asyncio.get_event_loop()
app = web.Application(loop=loop)
app.router.add_route('GET', '/', index)
app.router.add_route('GET', '/click', clicked)
app.router.add_route('POST', '/snsclicked', snsclicked)
app.router.add_route('GET', '/clicks', clicks)
web.run_app(app)
