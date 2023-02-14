import socket
import os
from _thread import start_new_thread
import json
import hashlib
import time

import sessions
import alchemy
import util
import config
import tiles

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
            intent = dict["intent"]
            session_name = dict["session_name"]
            session_pass_hash = dict["session_pass_hash"]
            if intent == "create_session":
                if len(session_name) > 32: reply = "fuck you"
                elif session_name in util.sessions:
                    reply = f"The session `{session_name}` is already registered."
                else:
                    session = sessions.Session(session_name)
                    session.pass_hash = dict["session_pass_hash"]
                    print(f"session created {session_name}")
                    reply = f"The session `{session_name}` has been successfully registered."
            else:
                if session_name in util.sessions:
                    session = sessions.Session(session_name)
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
        conns.remove(connection)
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
        if character in util.players:
            return f"Character id `{character}` has already been made."
        else:
            player = sessions.Player(character)
            player.character_pass_hash = character_pass_hash
            return f"Successfully created `{character}`. You may now log in."
    if character not in util.players:
        return f"Character {character} does not exist."
    player = sessions.Player(character)
    if not player.verify(character_pass_hash):
        return f"Incorrect character password."
    match intent:
        case "login":
            return f"Successfully logged in!"
        case "interests":
            return json.dumps(config.interests)
        case "setup_character":
            if player.setup:
                return "That character has already been setup!"
            else:
                player.nickname = content["name"]
                player.noun = content["noun"]
                player.pronouns = content["pronouns"]
                player.interests = content["interests"]
                player.aspect = content["aspect"]
                player.gameclass = content["class"]
                player.gristcategory = content["gristcategory"]
                player.secondaryvial = content["secondaryvial"]
                player.add_modus(content["modus"])
                land = sessions.Overmap(f"{player.name}{session.name}", session, player)
                player.land_name = land.name
                player.land_session = session.name
                housemap = land.get_map(land.housemap_name)
                print(f"housemap {housemap.name} {housemap}")
                print(f"housemap session {housemap.session.name} {housemap.session}")
                print(f"overmap {housemap.overmap.name} {housemap.overmap}")
                room = housemap.random_valid_room(config.starting_tiles)
                for interest in player.interests:
                    room.generate_loot(tiles.get_tile(interest).get_loot_list())
                player.goto_room(room)
                player.setup = True
                return f"Your land is the {land.title}! ({land.acronym})"
        case "current_map":
            map_tiles, map_specials, room_instances = player.get_view()
            return json.dumps({"map": map_tiles, "specials": map_specials, "instances": room_instances, "room_name": player.room.tile.name})
        case "player_info":
            return json.dumps(player.get_dict())
        case "sylladex":
            return json.dumps(player.sylladex_instances())
        case "use_item":
            instance_name = content["instance_name"]
            action_name = content["action_name"]
            target_name = content["target_name"]
            instance = alchemy.Instance(instance_name)
            if target_name is not None: target_instance = alchemy.Instance(target_name)
            else: target_instance = None
            return player.use(instance, action_name, target_instance)
        case "captchalogue":
            instance_name = content["instance_name"]
            modus_name = content["modus_name"]
            success = player.captchalogue(instance_name, modus_name)
            return "success" if success else "failure"
        case "uncaptchalogue":
            instance_name = content["instance_name"]
            success = player.uncaptchalogue(instance_name)
            return "success" if success else "failure"
        case "eject":
            instance_name = content["instance_name"]
            modus_name = content["modus_name"]
            velocity = content["velocity"]
            success = player.eject(instance_name, modus_name, velocity)
            return "success" if success else "failure"
        case "move":
            player.attempt_move(content)
            return
        case "console_command":
            console_commands(player, content)


def console_commands(player: sessions.Player, content: str):
    args = content.split(" ")
    command = args.pop(0)
    match command:
        case "harlify":
            item = alchemy.Item(" ".join(args))
            instance = alchemy.Instance(item)
            player.room.add_instance(instance.name)

def autosave():
    last_save = time.time()
    util.saveall()
    while True:
        if time.time() - last_save > 60:
            util.saveall()
            last_save = time.time()

def console():
    while True:
        console_input = input()
            
    
if __name__ == "__main__":
    ServerSocket = socket.socket()
    try:
        ServerSocket.bind((HOST_IP, PORT))
    except socket.error as e:
        print(str(e))

    start_new_thread(autosave, ())
    start_new_thread(console, ())

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
