import asyncio
from flask import Flask, Response
import requests
import itertools
import aiohttp
import socket
import docker
from random import randint

app = Flask(__name__)

client = docker.from_env()
UPDATE_PERIOD = 5

# Cписок серверов
server_list = [
    {"host": "loadbalancerqwe_app_1", "port": 5000, 'is_alive': True, 'requests_count': 0},
    {"host": "loadbalancerqwe_app_2", "port": 5000, 'is_alive': True, 'requests_count': 0},
    {"host": "loadbalancerqwe_app_3", "port": 5000, 'is_alive': True, 'requests_count': 0},
    {"host": "loadbalancerqwe_app_4", "port": 5000, 'is_alive': True, 'requests_count': 0},
    {"host": "loadbalancerqwe_app_5", "port": 5000, 'is_alive': True, 'requests_count': 0},
]

servers = itertools.cycle(server_list)


@app.route('/', methods=['GET'])
def proxy():
    server = next(servers)
    resp = requests.get(f"http://{server['host']}:{server['port']}")
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
    response = Response(resp.content, resp.status_code, headers)
    return response


# Проверка инстансов
async def update_statuses():
    check_urls = [
        f"http://{serv['host']}:{serv['port']}/check"
        for serv in server_list
    ]
    async with aiohttp.ClientSession() as session:
        resps = await fetch_all(session, check_urls)
        for serv, status in zip(server_list, resps):
            serv['is_alive'] = status


async def get_counter_requests():
    tasks = []
    async with aiohttp.ClientSession() as session:
        for server in server_list:
            url = f"http://{server['host']}:{server['port']}/requests_count"
            task = asyncio.create_task(session.get(url))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        servers_requests_count = []

        for server, response in zip(server_list, responses):
            server_data = {
                'host': server['host'],
                'port': server['port'],
                'requests_count': int(await response.text())
            }
            servers_requests_count.append(server_data)

        return servers_requests_count


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


# Включение и отключение инстансов

async def shutdown_server(host):
    container = client.containers.get(host)
    container.stop()


async def start_server(host):
    container = client.containers.get(host)
    container.stop()


# Проверка поднятых серверов
async def check_servers(server_list):
    port = 5000
    hosts = [host['host'] for host in server_list]
    results = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for i in range(len(hosts)):
        results.append(sock.connect_ex((hosts[i], port)))
    # Количество работающих серверов
    if results.count(0) == 3:
        sock.close()
        return True


async def start_close_instances(server_list):
    while True:
        hosts = [host['host'] for host in server_list]
        rand_num1 = randint(0, 4)
        rand_num2 = randint(0, 4)
        rand_num2 = rand_num2 if rand_num2 != rand_num1 else randint(0, 4)
        host1 = hosts[rand_num1]
        host2 = hosts[rand_num2]

        await asyncio.sleep(120)
        await shutdown_server(host1)
        await asyncio.sleep(120)
        await shutdown_server(host2)

        if check_servers(server_list):
            await start_server(host1)
            await start_server(host2)


if __name__ == "__main__":
    # healthcheck
    asyncio.run(status_updater())
    asyncio.run(start_close_instances(server_list))
    app.run(host="127.0.0.1", port=5000)
