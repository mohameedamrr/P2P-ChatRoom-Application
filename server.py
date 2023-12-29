from email import message
import socket, threading
class ClientThread(threading.Thread):

    def __init__(self,ip,port,clientsocket):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.csocket = clientsocket
        print ("[+] New thread started for ",ip,":",str(port))

    def run(self):    
        print ("Connection from : ",ip,":",str(port))

        clientsock.send("Welcome to the multi-threaded server".encode())

        data = "dummydata"

        while len(data):
            data = self.csocket.recv(2048).decode().split('|')
            if data[0] == "CREATE_CHAT_ROOM":
                chatRooms[data[1]] = data[2]
                message = "ROOM_CREATED".encode()
                self.csocket.send(message)
            elif data[0] == "JOIN_CHAT_ROOM":
                if chatRooms.get(data[1]) is not None:
                    adminPortNumber = chatRooms[data[1]].encode()
                    self.csocket.send(adminPortNumber)
                else:
                    self.csocket.send("Invalid Room Name".encode())
            elif data[0] == "DELETE_CHAT_ROOM":
                if chatRooms.get(data[1]) is not None:
                    del chatRooms[data[1]]
                    message = "Room deleted Successfully!".encode()
                    self.csocket.send(message)
                else:
                    self.csocket.send("Invalid Room Name".encode())                    
            elif data.decode()=="quit":
              self.csocket.send(str.encode("Ok By By"))
              self.csocket.close()
              data=''			  
        print ("Client at ",self.ip," disconnected...")

host = "0.0.0.0"
port = 10000

tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

tcpsock.bind((host,port))

#Dictionary for chatrooms
chatRooms = {}

while True:
    tcpsock.listen(4)
    print ("Listening for incoming connections...")
    (clientsock, (ip, port)) = tcpsock.accept()
    #pass clientsock to the ClientThread thread object being created
    newthread = ClientThread(ip, port, clientsock)
    newthread.start()