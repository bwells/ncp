#!/usr/bin/env python

import asyncio
from aiohttp import web
import aiohttp
import json
from datetime import datetime

CONTENT = open('index.html').read().encode('utf8')

connected = set()

last_clicked_at = None
last_click = None
count = 0

def register_click(click_type):
    global last_clicked_at
    global last_click
    global count

    last_clicked_at = datetime.now()
    last_click = click_type

    if click_type == 'single':
        count += 1
    elif click_type == 'double':
        count += 2
    elif click_type == 'long':
        count += 1.5

async def index(request):
    return web.Response(body=CONTENT)

async def clicked(request):
    global last_click
    click_type = request.GET.get('type', 'single')
    register_click(click_type)
    print("received click {}".format(last_click))
    return web.Response()

async def snsclicked(request):
    global last_click

    body = await request.text()
    data = json.loads(body)

    if 'SubscribeURL' in data:
        print("Confirm subscription at: {}".format(data['SubscribeURL']))
    else:
        msg = data['Subject']
        click_type = msg.split(': ')[1].lower()
        register_click(click_type)
        print("received click {}".format(last_click))

    return web.Response()

async def clicks(request):
    global connected
    ws = web.WebSocketResponse()
    try:
        connected.add(ws)
        print("connected")

        await ws.prepare(request)

        ws.send_str(last_click or '')

        local_clicked_at = last_clicked_at
        while True:
            if local_clicked_at != last_clicked_at:
                local_clicked_at = last_clicked_at
                response = {'type': last_click, 'clicks': count}
                ws.send_str(json.dumps(response))
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
