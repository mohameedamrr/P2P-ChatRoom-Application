import socket
import threading
 # TODO : Modify the protocols to include the usernames like in peerServer file.
groupMembers = []
groupPortNumbers = []

def connectToMembers(portNumber):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', portNumber))
    groupMembers.append(client)
    groupPortNumbers.append(portNumber)
    

# Connecting To Server
connectToMembers(55555)
groupMembers[0].send("JOIN_REQUEST".encode())


#List to hold the room members i am going to connect with 
# Listening to Server and Sending Nickname
def receive():
    while True:
        try:
            # Receive Message From Server
            # If 'NICK' Send Nickname
            message = groupMembers[0].recv(1024).decode('ascii').split('|')
            if message[0] == 'JOINED':
                for i in message:
                    if i is not "JOINED":
                        connectToMembers(int(i))

            # if server peer accepted the join request the client peer will now connect to all members in the room
            elif message[0] == "NOT_JOINED":
                print("Admin Didn't accept.")
                groupMembers[0].close()
                break

            elif message[0] == 'NEW_USER':
                connectToMembers(message[1])

            elif message[0] == "REMOVE_USER":
                removed_port = int(message[1])
                if removed_port in groupPortNumbers:
                    index = groupPortNumbers.index(removed_port)
                    groupMembers[index].close()
                    print(f"Removing user with port {removed_port}")

                    # Close the socket and remove from the lists
                    # removed_socket.close()
                    del groupMembers[index]
                    del groupPortNumbers[index]

        except:
            # Close Connection When Error
            print("An error occured!")
            groupMembers[0].close()
            break
# Sending Messages To Server
def write():
    while True:
        message = 'User: {}'.format(input(''))
        if message == "LEAVE":
            groupMembers[0].send(message.encode('ascii'))
        for member in groupMembers:
            member.send(message.encode('ascii'))

# Starting Threads For Listening And Writing
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()

