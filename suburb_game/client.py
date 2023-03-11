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
"intent": "",
"session_name": "",
"session_pass_hash": "",
"character": "",
"character_pass_hash": "",
"content": ""
}

def receive_data() -> str:
    data_fragments = []
    while True:
        chunk = ClientSocket.recv(10000).decode()
        data_fragments.append(chunk)
        if "\n" in chunk or not chunk: break
    return "".join(data_fragments).replace("\n", "")

def connect():
    print("Waiting for connection")
    try:
        ClientSocket.send(str.encode(json.dumps({"intent": "connect"})))
        return True
    except:
        try:
            ClientSocket.settimeout(2)
            ClientSocket.connect((HOST, PORT))
            return True
        except socket.error as e:
            print(e)
        return False

def hash(str): # returns encoded and hashed data
    encoded = str.encode()
    return hashlib.sha256(encoded).hexdigest()

def request(intent) -> str:
    dic["intent"] = intent
    Input = json.dumps(dic)
    ClientSocket.send(str.encode(Input))
    return receive_data()

#request, returns decoded JSON as dict
def requestdic(intent) -> dict:
    dic["intent"] = intent
    Input = json.dumps(dic)
    ClientSocket.send(str.encode(Input))
    reply = receive_data()
    return json.loads(reply)

#request, but with additional content sent to the server
def requestplus(intent, content) -> str:
    dic["intent"] = intent
    dic["content"] = content
    Input = json.dumps(dic)
    ClientSocket.send(str.encode(Input))
    dic["content"] = ""
    return receive_data()

def requestplusdic(intent, content) -> dict:
    dic["intent"] = intent
    dic["content"] = content
    Input = json.dumps(dic)
    ClientSocket.send(str.encode(Input))
    dic["content"] = ""
    reply = receive_data()
    return json.loads(reply)
