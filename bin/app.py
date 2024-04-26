from json import JSONDecodeError

import asyncio
import atexit
import logging
import nest_asyncio
import os
import signal
import threading
import uvicorn
from dotmap import DotMap
from fastapi import FastAPI
from pathlib import Path
from starlette.requests import Request
from typing import Any, Dict
from hummingbot.client.hummingbot_application import HummingbotApplication

nest_asyncio.apply()
root_path = Path(os.path.dirname(__file__)).absolute().as_posix()
debug = True
app = FastAPI(debug=debug, root_path=root_path)


@app.post("/run")
async def run(request: Request) -> Dict[str, Any]:
	try:
		body = DotMap(await request.json())
	except JSONDecodeError:
		body = DotMap({})

	body._dynamic = False

	HummingbotApplication.main_application()

	return body


async def start_api():
	signal.signal(signal.SIGTERM, shutdown)
	signal.signal(signal.SIGINT, shutdown)

	host = os.environ.get("HOST", "localhost")
	port = int(os.environ.get("PORT", "30003"))

	os.environ["ENV"] = "development"

	config = uvicorn.Config(
		"app:app",
		host=host,
		port=port,
		log_level=logging.DEBUG,
	)
	server = uvicorn.Server(config)
	await server.serve()


async def main():
	await start_api()


def after_startup():
	pass


async def startup():
	threading.Timer(1, after_startup).start()


# noinspection PyUnusedLocal
def shutdown(*args):
	pass


@atexit.register
def shutdown_helper():
	shutdown()
	asyncio.get_event_loop().close()


app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)


if __name__ == "__main__":
	try:
		loop = asyncio.get_event_loop()
		loop.run_until_complete(main())
	finally:
		shutdown_helper()
