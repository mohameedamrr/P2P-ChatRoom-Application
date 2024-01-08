from pymongo import MongoClient
import hashlib
import secrets

class DB:
    # db initializations
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['p2p-chat']

    def is_account_exist(self, username):
        return self.db.accounts.find_one({'username': username}) is not None

    def register(self, username, password):
        # Generate a random salt
        salt = secrets.token_hex(16)  # Use a cryptographically secure random generator

        # Combine the password with the salt and hash it using SHA-256
        hashed_password = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

        account = {
            "username": username,
            "password": hashed_password,
            "salt": salt  # Store the salt along with the hashed password
        }
        self.db.accounts.insert_one(account)

    def verify_password(self, username, password):
        user_data = self.db.accounts.find_one({"username": username})
        if user_data:
            stored_password = user_data["password"]
            stored_salt = user_data["salt"]
            # Hash the provided password with the stored salt and compare it with the stored password
            hashed_password = hashlib.sha256((password + stored_salt).encode('utf-8')).hexdigest()
            return hashed_password == stored_password
        return False

    # retrieves the password for a given username
    def get_password(self, username):
        return self.db.accounts.find_one({"username": username})["password"]

    # checks if an account with the username is online
    def is_account_online(self, username):
        return self.db.online_peers.count_documents({"username": username}) > 0


    # logs in the user
    def user_login(self, username, ip, port):
        online_peer = {
            "username": username,
            "ip": ip,
            "port": port
        }
        self.db.online_peers.insert_one(online_peer)

    # logs out the user 
    def user_logout(self, username):
        self.db.online_peers.delete_one({"username": username})


    # retrieves the ip address and the port number of the username
    def get_peer_ip_port(self, username):
        res = self.db.online_peers.find_one({"username": username})
        return (res["ip"], res["port"])
        # retrieves the list of online peers
    
    def get_online_peers(self):
        online_peers = self.db.online_peers.find()
        return [peer['username'] for peer in online_peers]
    
    def createRoom(self, roomname, password, username):
        room = {
            "roomname": roomname,
            "password": password,
            "creator": username
        }
        self.db.rooms.insert_one(room)                                
    
    def deleteRoom(self, roomname, username):
        self.db.rooms.delete_one({"roomname": roomname, "creator": username})                 
        self.db.room_peers.delete_many({"roomname": roomname})
        self.db.online_room_peers.delete_many({"roomname": roomname})

    def isRoomExists(self, roomname):
        return bool(self.db.rooms.find_one({'roomname': roomname}))  

    def getRoomDetails(self, roomname):
        return self.db.rooms.find_one({"roomname": roomname}, {"_id": 0, "password": 1, "creator": 1})


    def joinRoom(self, roomname, username):
        member = {
            "roomname": roomname,
            "username": username,
        }
        self.db.room_peers.insert_one(member)                                

    def leaveRoom(self, roomname, username):
        self.db.room_peers.delete_one({"roomname": roomname, "username": username})                    

    def showAvailableRooms(self, username):
        cursor = self.db.room_peers.find({"username": username}, {"_id": 0, "roomname": 1})
        rooms = [{"roomname": doc["roomname"]} for doc in cursor]
        if rooms:
            return rooms
        else:
            return None

    def getPeersInRoom(self, roomname, current_username):
        cursor = self.db.room_peers.find({"roomname": roomname, "username": {"$ne": current_username}}, {"_id": 0, "username": 1})
        users_in_room = [{"username": doc["username"]} for doc in cursor]
        if users_in_room:
            return users_in_room
        else:
            return None

    def isPeerInRoom(self, roomname, username):
        user = self.db.room_peers.find_one({"roomname": roomname, "username": username})
        return user is not None

  


    def enterRoom(self, roomname, username):
        member = {
            "roomname": roomname,
            "username": username,
        }
        self.db.online_room_peers.insert_one(member)                               

    def exitRoom(self, roomname, username):
        self.db.online_room_peers.delete_one({"roomname": roomname, "username": username})

    def get_users_entered_room(self, roomname, current_username):
        cursor = self.db.online_room_peers.find({"roomname": roomname, "username": {"$ne": current_username}}, {"_id": 0, "username": 1})
        users_in_room = [{"username": doc["username"]} for doc in cursor]
        if users_in_room:
            return users_in_room
        else:
            return None