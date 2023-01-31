import pygame
import sys
import pathlib
import hashlib
import socket
import json

ClientSocket = socket.socket()
HOST = "135.134.43.197" # server host and port
PORT = 25565

dic = {
"intent": None,
"session": None,
"session_pass_hash": None,
"character": None,
"character_pass_hash": None,
"content": None
}

def connect():
    print("Waiting for connection")
    try:
        ClientSocket.connect((HOST, PORT))
        return "Connected!"
    except socket.error as e:
        return str(e)

def hash(str): # returns encoded and hashed data
    encoded = str.encode()
    return hashlib.sha256(encoded).hexdigest()

def request(intent):
    dic["intent"] = intent
    Input = json.dumps(dic)
    ClientSocket.send(str.encode(Input))
    return ClientSocket.recv(1024).decode()

#request, returns decoded JSON as dict
def requestdic(intent):
    dic["intent"] = intent
    Input = json.dumps(dic)
    ClientSocket.send(str.encode(Input))
    return json.loads(ClientSocket.recv(1024).decode())

#request, but with additional content sent to the server
def requestplus(intent, content):
    dic["intent"] = intent
    dic["content"] = content
    Input = json.dumps(dic)
    ClientSocket.send(str.encode(Input))
    dic["content"] = None
    return ClientSocket.recv(1024).decode()
