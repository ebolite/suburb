import socket
import os
from _thread import start_new_thread
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
            session_name = dict["session_name"]
            session_pass_hash = dict["session_pass_hash"]
            if intent == "create_session":
                if session_name in util.sessions:
                    reply = f"The session `{session_name}` is already registered."
                else:
                    session = sessions.Session(session_name)
                    session.pass_hash = dict["session_pass_hash"]
                    print(f"session {session_name} pass_hash {session.pass_hash} dict pass_hash {dict['session_pass_hash']}")
                    reply = f"The session `{session_name}` has been successfully registered."
            else:
                if session_name in util.sessions:
                    session = sessions.Session(session_name)
                    print(session.pass_hash)
                    if session_pass_hash == session.pass_hash:
                        reply = handle_request(dict)
                    else:
                        reply = f"Incorrect session password."
                else:
                    reply = f"Invalid session name `{session_name}`."
            connection.sendall(str.encode(str(reply)))
        conns.remove(connection)
        connection.close()
    except (ConnectionResetError, UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"\nExcepted error!\n{e}\n")
        connection.close()

def handle_request(dict):
    intent = dict["intent"]
    if intent == "connect":
        return "Successfully connected."
    session_name = dict["session_name"]
    session = sessions.Session(session_name)
    character = dict["character"]
    character_pass_hash = dict["character_pass_hash"]
    content = dict["content"]
    if intent == "create_character":
        if character in session.players:
            return f"Character `{character}` already exists."
        else:
            player = sessions.Player(character, session)
            player.character_pass_hash = character_pass_hash
            return f"Successfully created `{character}`. You may now log in."
    player = sessions.Player(character, session)
    if not player.verify(character_pass_hash):
        return f"Incorrect character password."
    match intent:
        case "login":
            return f"Successfully logged in!"
        case "interests":
            out = json.dumps(config.interests)
            return out
        case "setup_character":
            if player.setup:
                out = "That character has already been setup!"
            else:
                player.nickname = content["name"]
                player.noun = content["noun"]
                player.pronouns = content["pronouns"]
                player.interests = content["interests"]
                player.aspect = content["aspect"]
                player.gameclass = content["class"]
                player.gristcategory = content["gristcategory"]
                player.secondaryvial = content["secondaryvial"]
                player.setup = True
                land = sessions.Overmap(f"{player.name}{player.session.name}", player.session, player)
                player.land_name = land.name
                player.land_session = player.session
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