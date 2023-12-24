""" 
A simple echo client 
""" 

import socket 

host = 'localhost' 
port = 10000 
size = 1024 

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
s.connect((host,port))

data = s.recv(size)

if len(data):
 print('Received:', data.decode())

data="message goes here"

while len(data):
    
    message= input('Input lowercase sentence (type quit to end communication":')
    if message == "1":
        message = "CREATE_CHAT_ROOM" + "|" + "Chat 1" + "|" + str(port)
        s.send(message.encode()) 
    elif message == "2":
        message = "JOIN_CHAT_ROOM" + "|" + "Chat 1" 
        s.send(message.encode()) 
    data = s.recv(size).decode()
    print(data)
    if message=="quit":
        data=''		

s.close() 