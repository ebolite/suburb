import time

from pymongo import MongoClient
import util

db_client = MongoClient(util.db_connection_string)

suburb_db = db_client["suburb"]

db_sessions = suburb_db["sessions"]
memory_sessions = {}
accessed_sessions = set()

db_players = suburb_db["players"]
memory_players = {item_dict["_id"]:item_dict for item_dict in db_players.find({})}

db_npcs = suburb_db["npcs"]
memory_npcs = {item_dict["_id"]:item_dict for item_dict in db_npcs.find({})}

db_items = suburb_db["items"]
memory_items = {item_dict["_id"]:item_dict for item_dict in db_items.find({})}

db_instances = suburb_db["instances"]
memory_instances = {instance_dict["_id"]:instance_dict for instance_dict in db_instances.find({})}

users_db = db_client["users"]
db_users = users_db["users"]
memory_users = {instance_dict["_id"]:instance_dict for instance_dict in db_users.find({})}

def save_databases():
    t = time.time()
    def callback(session):
        users = session.client["users"]["users"]
        users_data = {item_dict["_id"]:item_dict for item_dict in users.find({})}
        sessions = session.client["suburb"]["sessions"]
        players = session.client["suburb"]["players"]
        players_data = {item_dict["_id"]:item_dict for item_dict in players.find({})}
        npcs = session.client["suburb"]["npcs"]
        npcs_data = {item_dict["_id"]:item_dict for item_dict in npcs.find({})}
        items = session.client["suburb"]["items"]
        items_data = {item_dict["_id"]:item_dict for item_dict in items.find({})}
        instances = session.client["suburb"]["instances"]
        instances_data = {item_dict["_id"]:item_dict for item_dict in instances.find({})}

        users_to_insert = []
        for user_name, user_dict in memory_users.copy().items():
            if user_name not in users_data: users_to_insert.append(user_dict)
            elif user_dict != users_data[user_name]:
                users.update_one({"_id": user_name}, {"$set": user_dict}, upsert=True, session=session)
        if users_to_insert: users.insert_many(users_to_insert, session=session)

        global accessed_sessions
        for session_name, session_dict in memory_sessions.copy().items():
            sessions.update_one({"_id": session_name}, {"$set": session_dict}, upsert=True, session=session)
            if session_name not in accessed_sessions: memory_sessions.pop(session_name)
        accessed_sessions = set()

        players_to_insert = []
        for player_name, player_dict in memory_players.copy().items():
            if player_name not in players_data: players_to_insert.append(player_dict)
            elif player_dict != players_data[player_name]:
                players.update_one({"_id": player_name}, {"$set": player_dict}, upsert=True, session=session)
        if players_to_insert: players.insert_many(players_to_insert, session=session)

        npcs_to_insert = []
        for npc_name, npc_dict in memory_npcs.copy().items():
            if npc_name not in npcs_data: npcs_to_insert.append(npc_dict)
            elif npc_dict != npcs_data[npc_name]:
                npcs.update_one({"_id": npc_name}, {"$set": npc_dict}, upsert=True, session=session)
        if npcs_to_insert: npcs.insert_many(npcs_to_insert, session=session)

        items_to_insert = []
        for item_name, item_dict in memory_items.copy().items():
            if item_name not in items_data: items_to_insert.append(item_dict)
            elif item_dict != items_data[item_name]:
                items.update_one({"_id": item_name}, {"$set": item_dict}, upsert=True, session=session)
        if items_to_insert: items.insert_many(items_to_insert, session=session)

        instances_to_insert = []
        for instance_name, instance_dict in memory_instances.copy().items():
            if instance_name not in instances_data: instances_to_insert.append(instance_dict)
            elif instance_dict != instances_data[instance_name]:
                instances.update_one({"_id": instance_name}, {"$set": instance_dict}, upsert=True, session=session)
        if instances_to_insert: instances.insert_many(instances_to_insert, session=session)
        inserted = npcs_to_insert+items_to_insert+instances_to_insert
        if inserted: print(f"Inserted {len(inserted)}")
    with db_client.start_session() as session:
        session.with_transaction(callback)
    print(f"database save took {time.time()-t:.2f} secs")