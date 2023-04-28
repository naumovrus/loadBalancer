from flask import Flask, make_response
import socket
import asyncio
from random import randint

app = Flask(__name__)

check_cnt = 0


@app.route('/check')
def check():
    global check_cnt
    check_cnt += 1
    return make_response('/', 200)


@app.route('/')
async def index():
    global check_cnt
    print('i am alive')
    await asyncio.sleep(randint(3, 4))
    return f"Ready task from {socket.gethostname()} {check_cnt=}"


if __name__ == "__main__":
    app.run(port=5000)
