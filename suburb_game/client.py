import pygame
import sys
import pathlib
import util
import hashlib
import socket
import json
import ssl
import traceback

HOSTNAME = "suburbgame.com"
PORT = 25565

context = ssl.create_default_context()
# context.load_verify_locations(util.CERT_LOCATION)

unwrapped_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
ClientSocket = context.wrap_socket(unwrapped_sock, server_hostname=HOSTNAME)


dic = {
"intent": "",
"session_name": "",
"session_password": "",
"username": "",
"password": "",
"content": ""
}

# todo: character token auth
# def save_client_data():
#     util.last_client_data["session_name"] = dic["session_name"]
#     util.last_client_data["session_pass_hash"] = dic["session_pass_hash"]
#     util.last_client_data["character"] = dic["character"]
#     util.last_client_data["character_pass_hash"] = dic["character_pass_hash"]
#     util.writejson(util.last_client_data, "last_client_data")

# def load_client_data():
#     dic["session_name"] = util.last_client_data["session_name"]
#     dic["session_pass_hash"] = util.last_client_data["session_pass_hash"]
#     dic["character"] = util.last_client_data["character"]
#     dic["character_pass_hash"] = util.last_client_data["character_pass_hash"]

def receive_data() -> str:
    data_fragments = []
    while True:
        chunk = ClientSocket.recv(10000).decode()
        data_fragments.append(chunk)
        if "\n" in chunk or not chunk: break
    return "".join(data_fragments).replace("\n", "")

def connect():
    global ClientSocket
    unwrapped_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    ClientSocket = context.wrap_socket(unwrapped_sock, server_hostname=HOSTNAME)
    print("Waiting for connection")
    try:
        ClientSocket.send(str.encode(json.dumps({"intent": "connect"})))
        return True
    except:
        try:
            try:
                ClientSocket.settimeout(10)
                ClientSocket.connect((HOSTNAME, PORT))
                return True
            except TimeoutError: return False
        except socket.error as e:
            traceback.print_exception(e)
        return False

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
