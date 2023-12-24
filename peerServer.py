import socket
import threading

# Connection Data
host = '127.0.0.1'
port = 55555

# Starting Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

# Lists For Clients and Their Nicknames
roomMembers = []
memberSockets = []

# Sending Messages To All Connected Clients
def broadcast(message):
    for client in roomMembers:
        client.send(message)

# Handling Messages From Clients
def handle(client):
    while True:
        try:
            # Broadcasting Messages
            message = client.recv(1024).decode('ascii').split('|')
            if message[0] == "JOIN_REQUEST":
                roomMembers.append(message[1])  # message[1] is client port number
                response = "|".join(roomMembers)
                response = "JOINED" + '|' + response
                client.send(response).encode('ascii')
                broadcastMessage = "NEW_USER" + '|' + message[1] 
        # Print And Broadcast Nickname
                broadcast("{} joined!".format(message[2]).encode('ascii')) # message[2] is the username
                broadcast(broadcastMessage.encode('ascii'))
            # broadcast(message)
            elif message[0] == "LEAVE_CHAT_ROOM":
                index = roomMembers.index(message[1])
                roomMembers.remove(message[1])
                memberSockets[index].close()
                del memberSockets[index] 

                broadcast('{} left!'.format(message[2]).encode('ascii')) # message[2] is the username.
            else:
                print(message) 
        except:
            # Removing And Closing Clients
            index = roomMembers.index(message[1])
            roomMembers.remove(message[1])
            memberSockets[index].close()
            del memberSockets[index] 

            broadcast('{} left!'.format(message[2]).encode('ascii')) # message[2] is the username.
            break
# Receiving / Listening Function
def receive(): # the main purpose of recieve is to open connections (sockets) 
    while True:
        # Accept Connection
        client, (ip, portNumber) = server.accept()
        print("Connected with {}".format(str(portNumber)))

        roomMembers.append(portNumber)
        memberSockets.append(client)
        
        # Request And Store Nickname
        
        client.send('Connected to server!'.encode('ascii'))

        # Start Handling Thread For Client
        thread = threading.Thread(target=handle, args=(client,)) # This thread is for the handle function, the peerserver is constantly handling all messages recieved from all the members connected to it
        thread.start()

receive()
