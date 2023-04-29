from flask import Flask, make_response, g
import socket
import asyncio
from random import randint

app = Flask(__name__)

app.config['requests_counter'] = 0


@app.route('/check')
def check():
    return make_response('/', 200)


@app.route('/')
async def index():
    await asyncio.sleep(randint(3, 4))
    return f"Ready task from {socket.gethostname()}"


@app.before_request()
def before_request():
    g.requests_counter = app.config['requests_counter']
    app.config['requests_counter'] += 1


@app.after_request()
def after_request(response):
    g.requests_counter = app.config['requests_counter']
    app.config['requests_counter'] -= 1
    return response


@app.route('/requests_count')
async def cnt_requests():
    return str(g.requests_counter)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
