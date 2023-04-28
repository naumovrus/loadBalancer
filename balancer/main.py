import asyncio
from flask import Flask, Response
import requests
import itertools
import aiohttp

app = Flask(__name__)

UPDATE_PERIOD = 5

# список серверов
server_list = [
    {"host": "loadbalancerqwe_app_1", "port": 5000, 'is_alive': True},
    {"host": "loadbalancerqwe_app_2", "port": 5000, 'is_alive': True},
]
# servers = filter(lambda s: s['is_alive'], itertools.cycle(server_list))
servers = itertools.cycle(server_list)


@app.route('/', methods=['GET'])
def proxy():
    server = next(servers)
    resp = requests.get(f"http://{server['host']}:{server['port']}")
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
    response = Response(resp.content, resp.status_code, headers)
    return response


async def update_statuses():

    check_urls = [
        f"http://{serv['host']}:{serv['port']}/check"
        for serv in server_list
    ]
    async with aiohttp.ClientSession() as session:
        resps = await fetch_all(session, check_urls)
        for serv, status in zip(server_list, resps):
            serv['is_alive'] = status


async def fetch_all(session, urls):

    tasks = []
    for url in urls:
        task = asyncio.create_task(session.get(url))
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    return results


async def status_updater():

    while True:
        await update_statuses()
        await asyncio.sleep(UPDATE_PERIOD)



if __name__ == '__main__':
    asyncio.run(status_updater())
    app.run(host="0.0.0.0", port=5000)



