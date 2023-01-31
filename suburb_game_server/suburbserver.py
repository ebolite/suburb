import socket
import os
from _thread import *
import json
import hashlib

import sessions
import util
import config

HOST_IP = "192.168.4.28"
PORT = 25565

def threaded_client(connection):
    try:
        conns.append(connection)
        print(f"Connections: {len(conns)}")
        while True:
            data = connection.recv(2048)
            reply = ""
            if not data:
                break
            decoded = data.decode("utf-8")
            dict = json.loads(decoded)
            print(dict)
            intent = dict["intent"]
            session = dict["session"]
            session_pass_hash = dict["session_pass_hash"]
            if intent == "create_session":
                if session in util.sessions:
                    reply = f"The session `{session}` is already registered."
                else:
                    s = sessions.Session(session)
                    s.pass_hash = dict["session_pass_hash"]
                    reply = f"The session `{session}` has been successfully registered."
            else:
                if session in util.sessions:
                    s = sessions.Session(session)
                    print(s.pass_hash)
                    if session_pass_hash == s.pass_hash:
                        reply = handle_request(dict)
                    else:
                        reply = f"Incorrect session password."
                else:
                    reply = f"Invalid session name `{session}`."
            connection.sendall(str.encode(reply))
        conns.remove(connection)
        connection.close()
    except (ConnectionResetError, UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"\nExcepted error!\n{e}\n")
        connection.close()

def handle_request(dict):
    intent = dict["intent"]
    if intent == "connect":
        return "Successfully connected."
    session = dict["session"]
    s = sessions.Session(session)
    character = dict["character"]
    character_pass_hash = dict["character_pass_hash"]
    content = dict["content"]
    if intent == "create_character":
        if character in s.players:
            return f"Character `{character}` already exists."
        else:
            p = sessions.Player(character, s)
            p.character_pass_hash = character_pass_hash
            return f"Successfully created `{character}`. You may now log in."
    p = sessions.Player(character, s)
    if not p.verify(character_pass_hash):
        return f"Incorrect character password."
    if intent == "login":
        return f"Successfully logged in!"
    if intent == "interests":
        out = json.dumps(config.interests)
        return out
    if intent == "setup_character":
        if p.setup:
            out = "That character has already been setup!"
        else:
            p.nickname = content["name"]
            p.noun = content["noun"]
            p.pronouns = content["pronouns"]
            p.interests = content["interests"]
            p.aspect = content["aspect"]
            p.gameclass = content["class"]
            p.gristcategory = content["gristcategory"]
            p.secondaryvial = content["secondaryvial"]
            p.setup = True
            land = sessions.Overmap(f"{p.name}{p.Session.name}", p.Session, p)
            p.land = land.name
            p.landsession = p.Session
            out = f"Your land is the {land.title}! ({land.acronym})"
        return out
    
if __name__ == "__main__":
    ServerSocket = socket.socket()
    try:
        ServerSocket.bind((HOST_IP, PORT))
    except socket.error as e:
        print(str(e))

    print("Waiting for connections...")
    ServerSocket.listen(5)

    conns = []
    threads = 0

    while True:
        Client, address = ServerSocket.accept()
        print(f"Connected to: {address[0]} : {str(address[1])}")
        start_new_thread(threaded_client, (Client, ))
        threads += 1
        print(f"Thread Number: {str(threads)}")