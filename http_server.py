#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from http.server import HTTPServer, BaseHTTPRequestHandler

get_registered_paths = {}
post_registered_paths = {}


class HTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in get_registered_paths:
            f = get_registered_paths[self.path]
            rv = f(self, None)
            if type(rv) == dict:
                rv = json.dumps(rv)
                content_type = 'application/json'
            elif type(rv) == list:
                rv = json.dumps(rv)
                content_type = 'application/json'
            elif type(rv) == str:
                content_type = 'text/html'
            else:
                rv = "internal error"
                content_type = 'text/html'

            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(rv.encode('utf-8'))

        else:
            self.send_response(501)
            self.end_headers()
            self.wfile.write("Internal error.".encode('utf-8'))


    def do_POST(self):
        if self.path in post_registered_paths:
            f = post_registered_paths[self.path]
            content_len = int(self.headers.get('Content-Length'))
            post_body = self.rfile.read(content_len)
            rv = f(self, post_body)
            if type(rv) == dict:
                rv = json.dumps(rv)
                content_type = 'application/json'
            elif type(rv) == list:
                rv = json.dumps(rv)
                content_type = 'application/json'
            elif type(rv) == str:
                content_type = 'text/html'
            else:
                rv = "internal error"
                content_type = 'text/html'

            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(rv.encode('utf-8'))

        else:
            self.send_response(501)
            self.end_headers()
            self.wfile.write("Internal error.".encode('utf-8'))


def get(path):
    def decorator(func):
        get_registered_paths[path] = func
        return func
    return decorator


def post(path):
    def decorator(func):
        post_registered_paths[path] = func
        return func
    return decorator


def run(port=8080):
    server = HTTPServer(('0.0.0.0', port), HTTPHandler)
    server.serve_forever()
