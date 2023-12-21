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