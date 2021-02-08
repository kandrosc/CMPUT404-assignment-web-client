#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
from urllib.parse import urlparse, urlencode

def help():
    print("httpclient.py <URL> [GET/POST] [key1 value1 [key2 value2 ....... [keyn value]]]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body="",headers=""):
        self.code = code
        self.body = body
        self.headers = headers

class HTTPClient(object):
    #def get_host_port(self,url):

    # Creates a tcp socket and connects
    def connect(self, host, port):
        # Try to create tcp connection
        try: self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except (self.socket.error, msg):
            print(f'Failed to create socket. Error code: {str(msg[0])} , Error message : {msg[1]}')
            return 1
        # Try to get the remote ip of host
        try: remote_ip = socket.gethostbyname( host )
        except socket.gaierror:
                print ('Hostname could not be resolved. Exiting')
                return 1
        self.socket.connect((host,port))
        return 0

    def get_code(self, data):
        try: code = int(re.findall("(?<=HTTP/1.[0|1] )([0-9]+)",data)[0])
        except IndexError:
            print("Response code not found in header, must not have been proper HTTP!")
            print(data)
            return 1
        return code

    def get_headers(self,data):
        data_list = data.split("\n")
        for i in range(len(data_list)):
            if data_list[i] == "\r":
                sep = i+1
                break
        try: headers = "\n".join(data_list[:sep])
        except NameError:
            print("Format of data is wrong, headers not found. Must not have been proper HTTP!")
            return 1
        return headers

    def get_body(self, data):
        data_list = data.split("\n")
        for i in range(len(data_list)):
            if data_list[i] == "\r":
                sep = i+1
                break
        try: body = "\n".join(data_list[sep:])
        except NameError:
            print("Format of data is wrong, body not found. Must not have been proper HTTP!")
            return 1
        return body
    
    def sendall(self, data):
        try: self.socket.sendall(data.encode('utf-8'))
        except socket.error:
            print("Failed to send data")
            return 1
        return 0
        
    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        try: buffer_out = buffer.decode("utf-8")
        except UnicodeDecodeError: buffer_out = buffer.decode("ISO-8859-1")
        return buffer_out


    def GET(self, url, args={}):
        p = urlparse(url)
        parsed_url, port, path = p.netloc, p.port, p.path
        if port == None: port = 80
        if path == "" or path == " ": path = "/"
        else: parsed_url = parsed_url.split(":")[0]

        err = self.connect(parsed_url,port)
        if err:
            self.close()
            return 1
        payload = f'GET {path} HTTP/1.1\r\nHost: {parsed_url}\r\n\r\n'
        err = self.sendall(payload)
        if err:
            self.close()
            return 1
        self.socket.shutdown(socket.SHUT_WR)
        data = self.recvall(self.socket)
        headers = self.get_headers(data)
        code = self.get_code(headers)
        body = self.get_body(data)
        self.close()
        if code==1 or body==1: return 1
        return HTTPResponse(code, body, headers)

    def POST(self, url, args={}):
        p = urlparse(url)
        parsed_url, port, path = p.netloc, p.port, p.path
        if port == None: port = 80
        if path == "" or path == " ": path = "/"
        else: parsed_url = parsed_url.split(":")[0]
        err = self.connect(parsed_url,port)
        if err:
            self.close()
            return 1
        args = urlencode(args)
        payload = f'POST {path} HTTP/1.1\r\nHost: {parsed_url}\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: {len(args)}\r\n\r\n{args}'
        err = self.sendall(payload)
        if err:
            self.close()
            return 1
        self.socket.shutdown(socket.SHUT_WR)
        data = self.recvall(self.socket)
        headers = self.get_headers(data)
        code = self.get_code(headers)
        body = self.get_body(data)
        self.close()
        if code==1 or body==1: return 1
        return HTTPResponse(code, body, headers)

    def command(self, url, command="GET", args={}):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )

def buildArgs(argList):
    args = {}
    for i in range(0,len(argList),2): args[argList[i]] = argList[i+1]
    return args

if __name__ == "__main__":
    client = HTTPClient()
    argv = sys.argv
    argc = len(argv)
    if (argc <= 1 or (argc>3 and (argc-3)%2==1)):
        help()
        sys.exit(1)
    else:
        url = argv[1]
        try:
            command =  argv[2].upper()
            if command != "GET" and command != "POST":
                help()
                sys.exit(1)
        except IndexError: command = "GET"
        args = buildArgs(argv[3:])
        resp = client.command( url, command, args )
    if type(resp) != HTTPResponse: sys.exit(1)
    print(resp.code)
    print(resp.headers)
    print(resp.body)
