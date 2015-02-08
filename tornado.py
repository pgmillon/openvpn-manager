#!flask/bin/python

from app import app
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer

http_server = HTTPServer(WSGIContainer(app))
http_server.listen(8000)
IOLoop.instance().start()