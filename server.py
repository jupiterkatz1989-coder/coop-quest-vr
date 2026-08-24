#!/usr/bin/env python3
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parent;DIST=ROOT/'dist';PREFIX='/coop-quest-vr'
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(DIST),**kw)
    def do_GET(self):
        clean=self.path.split('?',1)[0]
        if clean in {'/health',PREFIX+'/health'}:
            body=b'{"status":"ok","app":"coop-quest-vr"}';self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
        if clean==PREFIX:self.send_response(308);self.send_header('Location',PREFIX+'/');self.end_headers();return
        if clean.startswith(PREFIX+'/'):self.path=self.path[len(PREFIX):]
        target=DIST/self.path.split('?',1)[0].lstrip('/')
        if not target.exists() and '.' not in target.name:self.path='/index.html'
        super().do_GET()
    def log_message(self,fmt,*args):
        if args and str(args[0]).startswith(('4','5')):super().log_message(fmt,*args)
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',8800),Handler).serve_forever()
