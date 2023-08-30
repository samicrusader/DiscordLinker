import aiohttp
import json
import pytz
import os
from anyio import Path
from datetime import datetime, timedelta
from fastapi import FastAPI
from starlette.responses import RedirectResponse

# Change me to wherever you want the cache for current invites to be stored
cache_path = '/tmp/discordlinker.json'

app = FastAPI()
token = os.environ['DISCORD_TOKEN']


@app.get('/')
async def root():
    return 'pageok'


@app.get('/getFriendInvite')
async def get_friend_invite():
    data = {'code': '', 'expires': (datetime.now(pytz.timezone('UTC')) + timedelta(seconds=10)).isoformat(), 'max_uses': 0, 'logged_uses': 0}
    if await Path(cache_path).exists():
        data = json.load(open(cache_path, 'r'))
    if datetime.fromisoformat(data['expires']) <= datetime.now(pytz.timezone('UTC')) or data['logged_uses']+1 > data['max_uses']:
        print('generating new invite')
        async with aiohttp.ClientSession() as session:
            async with session.post('https://discord.com/api/v9/users/@me/invites', data='{}',
                                    headers={'authorization': token, 'content-type': 'application/json'}) as resp:
                if not resp.status == 200:
                    raise Exception(await resp.json())
                data['code'] = (await resp.json())['code']
                data['expires'] = (await resp.json())['expires_at']
                data['max_uses'] = (await resp.json())['max_uses']
                data['logged_uses'] = 1
    else:
        data['logged_uses'] += 1
    json.dump(data, open(cache_path, 'w'))
    return RedirectResponse(url=f'https://discord.com/invite/{data["code"]}')
