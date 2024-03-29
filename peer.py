import ast
from socket import *
import threading
import time
import select
import logging
from colorama import Fore, Style, init
import hashlib
import secrets
import re
import sys



class TextFormatting:
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"
    HYPERLINK = "\033]8;;{}\033\\{}\033]8;;\033\\"


def applyformatting(message):

    if message.startswith("*"):
        message = TextFormatting.BOLD + message[1:] + TextFormatting.RESET
    elif message.startswith("#"):
        message = TextFormatting.ITALIC + message[1:] + TextFormatting.RESET
    elif message.startswith("_"):
        message = TextFormatting.UNDERLINE + message[1:] + TextFormatting.RESET
    elif message.startswith("http:") or message.startswith("https:"):
        return TextFormatting.HYPERLINK.format(message, message)
    return message

# Server side of peer
class PeerServer(threading.Thread):


    # Peer server initialization
    def __init__(self, username, peerServerPort):
        threading.Thread.__init__(self)
        # keeps the username of the peer
        self.username = username
        # tcp socket for peer server
        self.tcpServerSocket = socket(AF_INET, SOCK_STREAM)
        # port number of the peer server
        self.peerServerPort = peerServerPort
        # if 1, then user is already chatting with someone
        # if 0, then user is not chatting with anyone
        self.isChatRequested = 0
        self.isRoomRequested = 0
        # keeps the socket for the peer that is connected to this peer
        self.connectedPeerSocket = None
        # keeps the ip of the peer that is connected to this peer's server
        self.connectedPeerIP = None
        # keeps the port number of the peer that is connected to this peer's server
        self.connectedPeerPort = None
        # online status of the peer
        self.isOnline = True
        # keeps the username of the peer that this peer is chatting with
        self.chattingClientName = None
        self.busy = 0
    

    # main method of the peer server thread
    def run(self):

        print("Peer server started.")    

        # gets the ip address of this peer
        # first checks to get it for windows devices
        # if the device that runs this application is not windows
        # it checks to get it for macos devices
        hostname=gethostname()
        try:
            self.peerServerHostname=gethostbyname(hostname)
        except gaierror:
            import netifaces as ni
            self.peerServerHostname = ni.ifaddresses('en0')[ni.AF_INET][0]['addr']

        # ip address of this peer
        #self.peerServerHostname = 'localhost'
        #Here we use listen to listen for incoming connections
        # socket initializations for the server of the peer
        self.tcpServerSocket.bind((self.peerServerHostname, self.peerServerPort))
        self.tcpServerSocket.listen(4)
        # inputs sockets that should be listened
        inputs = [self.tcpServerSocket]
        # server listens as long as there is a socket to listen in the inputs list and the user is online
        while inputs and self.isOnline:
            # monitors for the incoming connections
            try:
                readable, writable, exceptional = select.select(inputs, [], [])
                # If a server waits to be connected enters here
                for s in readable:
                    # if the socket that is receiving the connection is 
                    # the tcp socket of the peer's server, enters here
                    if s is self.tcpServerSocket:
                        # accepts the connection, and adds its connection socket to the inputs list
                        # so that we can monitor that socket as well
                        connected, addr = s.accept()
                        connected.setblocking(0)
                        inputs.append(connected)
                        # if the user is not chatting, then the ip and the socket of
                        # this peer is assigned to server variables
                        if self.isChatRequested == 0:     
                            print(self.username + " is connected from " + str(addr))
                            self.connectedPeerSocket = connected
                            self.connectedPeerIP = addr[0]
                    # if the socket that receives the data is the one that
                    # is used to communicate with a connected peer ((((((((((already connected)))))))))), then enters here
                    else:
                        # message is received from connected peer
                        messageReceived = s.recv(1024).decode() 
                        # logs the received message
                        logging.info("Received from " + str(self.connectedPeerIP) + " -> " + str(messageReceived))
                    
                        # if message is a request message it means that this is the receiver side peer server
                        # so evaluate the chat request 
                        if len(messageReceived) > 11 and messageReceived[:12] == "CHAT_REQUEST":
                            # text for proper input choices is printed however OK or REJECT is taken as input in main process of the peer
                            # if the socket that we received the data belongs to the peer that we are chatting with
                            if s is self.connectedPeerSocket and not self.isRoomRequested:
                                # parses the message
                                messageReceived = messageReceived.split('|')
                                # gets the port of the peer that sends the chat request message
                                self.connectedPeerPort = int(messageReceived[1])
                                # gets the username of the peer sends the chat request message
                                self.chattingClientName = messageReceived[2]
                                # prints prompt for the incoming chat request
                                print("Incoming chat request from " + self.chattingClientName + " >> ")
                                print("Enter OK to accept or REJECT to reject:  ")
                                # makes isChatRequested = 1 which means that peer is chatting with someone
                                self.isChatRequested = 1
                            # if the socket that we received the data does not belong to the peer that we are chatting with
                            # and if the user is already chatting with someone else(isChatRequested = 1), then enters here
                            elif s is not self.connectedPeerSocket and self.isChatRequested == 1:
                                # sends a busy message to the peer that sends a chat request when this peer is 
                                # already chatting with someone else
                                message = "BUSY"
                                s.send(message.encode())
                                # remove the peer from the inputs list so that it will not monitor this socket
                                inputs.remove(s)
                        # if an OK message is received then ischatrequested is made 1 and then next messages will be shown to the peer of this server
                        elif self.isRoomRequested:
                            message = messageReceived.split('|')
                            # gets the username of the peer sends the chat request message
                            self.chattingClientName = message[0]
                            messageReceived = message[1]
                            messageReceived = applyformatting(messageReceived)
                            if messageReceived == ":q":
                                print("\n" + self.chattingClientName + " quit\n" )
                            elif messageReceived == "JOINED":
                                print('\n' + self.chattingClientName + " joined the room!")
                            else:
                                print(self.chattingClientName + ": " + messageReceived)
                            inputs.clear()
                            inputs.append(self.tcpServerSocket)

                        elif messageReceived == "OK":
                            self.isChatRequested = 1
                        # if an REJECT message is received then ischatrequested is made 0 so that it can receive any other chat requests
                        elif messageReceived == "REJECT":
                            self.isChatRequested = 0
                            inputs.remove(s)
                        # if a message is received, and if this is not a quit message ':q' and 
                        # if it is not an empty message, show this message to the user
                        elif messageReceived[:2] != ":q" and len(messageReceived)!= 0:
                            messageReceived = applyformatting(messageReceived)
                            print(str(self.chattingClientName) + ": " + str(messageReceived))
                        # if the message received is a quit message ':q',
                        # makes ischatrequested 1 to receive new incoming request messages
                        # removes the socket of the connected peer from the inputs list
                        elif messageReceived[:2] == ":q":
                            self.isChatRequested = 0
                            inputs.clear()
                            inputs.append(self.tcpServerSocket)
                            # connected peer ended the chat
                            if len(messageReceived) == 2:
                                print("User you're chatting with ended the chat")
                                print("Press enter to quit the chat: ")
                        # if the message is an empty one, then it means that the
                        # connected user suddenly ended the chat(an error occurred)
                        elif len(messageReceived) == 0:
                            self.isChatRequested = 0
                            inputs.clear() 
                            inputs.append(self.tcpServerSocket)
                            print("User you're chatting with suddenly ended the chat")
                            print("Press enter to quit the chat: ")
            # handles the exceptions, and logs them
            except OSError as oErr:
                logging.error("OSError: {0}".format(oErr))
            except ValueError as vErr:
                logging.error("ValueError: {0}".format(vErr))
            

# Client side of peer
class PeerClient(threading.Thread):
    # variable initializations for the client side of the peer
    def __init__(self, ipToConnect, portToConnect, username, peerServer, responseReceived):
        threading.Thread.__init__(self)
        # keeps the ip address of the peer that this will connect
        self.ipToConnect = ipToConnect
        # keeps the username of the peer
        self.username = username
        # keeps the port number that this client should connect
        self.portToConnect = portToConnect
        # client side tcp socket initialization
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        # keeps the server of this client
        self.peerServer = peerServer
        # keeps the phrase that is used when creating the client
        # if the client is created with a phrase, it means this one received the request
        # this phrase should be none if this is the client of the requester peer
        self.responseReceived = responseReceived
        # keeps if this client is ending the chat or not
        self.isEndingChat = False
        #User wants to join chat room not request chat (TA3DEL MEN 3ANDNA)
        self.isChatRoom = False


    # main method of the peer client thread
    def run(self):
        print("Peer client started.")
        # connects to the server of other peer
        self.tcpClientSocket.connect((self.ipToConnect, self.portToConnect))
        # if the server of this peer is not connected by someone else and if this is the requester side peer client then enters here
        if self.peerServer.isChatRequested == 0 and self.responseReceived is None and self.isChatRoom is False:
            # composes a request message and this is sent to server and then this waits a response message from the server this client connects
            requestMessage = "CHAT_REQUEST" +'|' + str(self.peerServer.peerServerPort)+ "|" + self.username
            # logs the chat request sent to other peer
            logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + requestMessage)
            # sends the chat request
            self.tcpClientSocket.send(requestMessage.encode())
            print("Request message " + requestMessage + " is sent.")
            # received a response from the peer which the request message is sent to
            self.responseReceived = self.tcpClientSocket.recv(1024).decode()
            # logs the received message
            logging.info("Received from " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + self.responseReceived)
            print("Response is " + self.responseReceived)
            # parses the response for the chat request
            self.responseReceived = self.responseReceived.split()
            # if response is ok then incoming messages will be evaluated as client messages and will be sent to the connected server
            if self.responseReceived[0] == "OK":
                # changes the status of this client's server to chatting
                self.peerServer.isChatRequested = 1
                # sets the server variable with the username of the peer that this one is chatting
                self.peerServer.chattingClientName = self.responseReceived[1]
                # as long as the server status is chatting, this client can send messages
                while self.peerServer.isChatRequested == 1:
                    # message input prompt
                    messageSent = input()
                    sys.stdout.write("\033[F")
                    sys.stdout.write("\033[K")
                    # sends the message to the connected peer, and logs it
                    self.tcpClientSocket.send(messageSent.encode())
                    logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + messageSent)
                    if messageSent != ":q":
                        messageFormatted = applyformatting(messageSent)
                        print("me: " + messageFormatted)
                    
                    # if the quit message is sent, then the server status is changed to not chatting
                    # and this is the side that is ending the chat
                    if messageSent == ":q":
                        self.peerServer.isChatRequested = 0
                        self.isEndingChat = True
                        break
                # if peer is not chatting, checks if this is not the ending side
                if self.peerServer.isChatRequested == 0:
                    if not self.isEndingChat:
                        # tries to send a quit message to the connected peer
                        # logs the message and handles the exception
                        try:
                            self.tcpClientSocket.send(":q ending-side".encode())
                            logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> :q")
                        except BrokenPipeError as bpErr:
                            logging.error("BrokenPipeError: {0}".format(bpErr))
                    # closes the socket
                    self.responseReceived = None
                    self.tcpClientSocket.close()
            # if the request is rejected, then changes the server status, sends a reject message to the connected peer's server
            # logs the message and then the socket is closed       
            elif self.responseReceived[0] == "REJECT":
                self.peerServer.isChatRequested = 0
                print("client of requester is closing...")
                self.tcpClientSocket.send("REJECT".encode())
                logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> REJECT")
                self.tcpClientSocket.close()
            # if a busy response is received, closes the socket
            elif self.responseReceived[0] == "BUSY":
                print("Receiver peer is busy")
                self.tcpClientSocket.close()
        # if the client is created with OK message it means that this is the client of receiver side peer
        # so it sends an OK message to the requesting side peer server that it connects and then waits for the user inputs.
        elif self.responseReceived == "OK":
            # server status is changed
            self.peerServer.isChatRequested = 1
            # ok response is sent to the requester side
            okMessage = "OK"
            self.tcpClientSocket.send(okMessage.encode())
            logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + okMessage)
            print("Client with OK message is created... and sending messages")
            # client can send messsages as long as the server status is chatting
            while self.peerServer.isChatRequested == 1:
                # input prompt for user to enter message
                messageSent = input()
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[K")                
                self.tcpClientSocket.send(messageSent.encode())
                logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + messageSent)
                if messageSent != ":q":
                    messageFormatted = applyformatting(messageSent)
                    print("me: " + messageFormatted)
                # if a quit message is sent, server status is changed
                if messageSent == ":q":
                    self.peerServer.isChatRequested = 0
                    self.isEndingChat = True
                    break
            # if server is not chatting, and if this is not the ending side
            # sends a quitting message to the server of the other peer
            # then closes the socket
            if self.peerServer.isChatRequested == 0:
                if not self.isEndingChat:
                    self.tcpClientSocket.send(":q ending-side".encode())
                    logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> :q")
                self.responseReceived = None
                self.tcpClientSocket.close()
                

# main process of the peer
class peerMain():

    # peer initializations
    def __init__(self):
        while True:
            self.registryName = input("Enter IP address of registry: ") 
            self.registryPort = 15600
            self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)

            try:
                # Attempt to connect to the registry
                self.tcpClientSocket.connect((self.registryName, self.registryPort))
                break  # Exit the loop if the connection is successful
            except Exception as e:
                # Handle connection errors
                print(f"{Fore.RED}Error connecting to the registry, make sure to enter the correct IP address")
        # # ip address of the registry
        # self.registryName = input("Enter IP address of registry: ")
        # #self.registryName = 'localhost'
        # # port number of the registry
        # self.registryPort = 15600
        # # tcp socket connection to registry
        # self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        
        # initializes udp socket which is used to send hello messages
        self.udpClientSocket = socket(AF_INET, SOCK_DGRAM)
        # udp port of the registry
        self.registryUDPPort = 15500
        # login info of the peer
        self.loginCredentials = (None, None)
        # online status of the peer
        self.isOnline = False
        # server port number of this peer
        self.peerServerPort = None
        # server of this peer
        self.peerServer = None
        # client of this peer
        self.peerClient = None
        # timer initialization
        self.timer = None
        
        choice = "0"
        # log file initialization
        logging.basicConfig(filename="peer.log", level=logging.INFO)

        print(f"{Fore.YELLOW}\n***** Main Menu *****")
        # as long as the user is not logged out, asks to select an option in the menu
        while choice != "3":
            # menu selection prompt
            print(f"{Fore.YELLOW}\nChoose from the following options, Write the number corresponding to each command:")
            print(f"{Fore.CYAN}1. Create account")
            print(f"{Fore.CYAN}2. Login")
            print(f"{Fore.CYAN}3. Logout")
            print(f"{Fore.CYAN}4. Search")
            print(f"{Fore.CYAN}5. Start a chat")
            print(f"{Fore.CYAN}6. Show online users")
            print(f"{Fore.CYAN}7. Create Chat room")
            print(f"{Fore.CYAN}8. Join Chat room")
            print(f"{Fore.CYAN}9. Enter Chat room")
            print(f"{Fore.CYAN}10. Delete Chat room")

            print(f"{Style.RESET_ALL}Type '{Fore.RED}CANCEL{Style.RESET_ALL}' to cancel or exit.")
    
            choice = input("Enter your choice: ")
            # if choice is 1, creates an account with the username
            # and password entered by the user
            # print(choice == "10" and self.isOnline)
            if choice is "1" and not self.isOnline:
                username = input("Enter Username: ")
                password = input("Enter Password: ")
                
                self.createAccount(username, password)
                # self.test_create_account_exists()
            # if choice is 2 and user is not logged in, asks for the username
            # and the password to login
            elif choice is "1" and self.isOnline:
                print(f"{Fore.RED}Please logout before creating another account.")
            elif choice is "2" and not self.isOnline:
                username = input("Enter Username: ")
                password = input("Enter Password: ")
                # asks for the port number for server's tcp socket
                peerServerPort = int(input("Enter a port number for peer server: "))
                
                status = self.login(username, password, peerServerPort)
                # is user logs in successfully, peer variables are set
                if status is 1:
                    self.isOnline = True
                    self.loginCredentials = (username, password)
                    self.peerServerPort = peerServerPort
                    # creates the server thread for this peer, and runs it
                    self.peerServer = PeerServer(self.loginCredentials[0], self.peerServerPort)
                    self.peerServer.start()
                    # hello message is sent to registry
                    self.sendHelloMessage()
            elif choice is "2" and self.isOnline:
                print(f"{Fore.RED}Please logout before logging in with another account.")
            # if choice is 3 and user is logged in, then user is logged out
            # and peer variables are set, and server and client sockets are closed
            elif choice is "3" and self.isOnline:
                self.logout(1)
                self.isOnline = False
                self.loginCredentials = (None, None)
                self.peerServer.isOnline = False
                self.peerServer.tcpServerSocket.close()
                if self.peerClient is not None:
                    self.peerClient.tcpClientSocket.close()
                print("Logged out successfully")
            # is peer is not logged in and exits the program
            elif choice is "3" and not self.isOnline:
                print(f"{Fore.RED}Please login before logging out.")

            # if choice is 4 and user is online, then user is asked
            # for a username that is wanted to be searched
            elif choice is "4" and self.isOnline:
                username = input("Enter username of person to be searched: ")
                searchStatus = self.searchUser(username)
                # if user is found its ip address is shown to user
                if searchStatus is not None and searchStatus != 0:
                    print("User found Successfully !" + "\n User details: IP address of " + username + " is " + searchStatus)
            elif choice is "4" and not self.isOnline:
                print(f"{Fore.RED}Please login before searching for a user.")
            # if choice is 5 and user is online, then user is asked
            # to enter the username of the user that is wanted to be chatted
            elif choice is "5" and self.isOnline:
                username = input("Enter the username of user to start chat: ")
                searchStatus = self.searchUser(username)
                # if searched user is found, then its ip address and port number is retrieved
                # and a client thread is created
                # main process waits for the client thread to finish its chat
                if searchStatus is not None and searchStatus is not 0 :
                    searchStatus = searchStatus.split(":")
                    self.peerClient = PeerClient(searchStatus[0], int(searchStatus[1]) , self.loginCredentials[0], self.peerServer, None)
                    self.peerClient.start()
                    self.peerClient.join()
            elif choice is "5" and not self.isOnline:
                print(f"{Fore.RED}Please login before starting a chat.")   
            elif choice is "6" and self.isOnline:
                self.getOnlineUsers()
            elif choice is "6" and not self.isOnline:
                print(f"{Fore.RED}Please login before requesting online list.")  
            elif choice is "7" and self.isOnline:
                roomName = input("Enter name of the room to be created: ")
                password = input('Enter password: ')
                self.createRoom(roomName, password)
            elif choice is "7" and not self.isOnline:
                print(f"{Fore.RED}Please login before creating a chat room.")
            elif choice is "8" and self.isOnline:
                roomName = input("Enter name of the room you want to join: ")
                password = input("Please enter room password: ")
                self.joinRoom(roomName, password) 
            elif choice is "9" and self.isOnline:
                status = self.showRooms()
                if status:
                    roomname = input("Enter room name: ")
                    self.enterRoom(roomname)
            elif choice == '10' and self.isOnline:
                print("Delete Room")
                roomname = input("roomname: " )
                password = input("password: " )
                self.deleteRoom(roomname, password)
            # if this is the receiver side then it will get the prompt to accept an incoming request during the main loop
            # that's why response is evaluated in main process not the server thread even though the prompt is printed by server
            # if the response is ok then a client is created for this peer with the OK message and that's why it will directly
            # sent an OK message to the requesting side peer server and waits for the user input
            # main process waits for the client thread to finish its chat
            elif choice == "OK" and self.isOnline:
                okMessage = "OK " + self.loginCredentials[0]
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> " + okMessage)
                self.peerServer.connectedPeerSocket.send(okMessage.encode())
                self.peerClient = PeerClient(self.peerServer.connectedPeerIP, self.peerServer.connectedPeerPort , self.loginCredentials[0], self.peerServer, "OK")
                self.peerClient.start()
                self.peerClient.join()
            # if user rejects the chat request then reject message is sent to the requester side
            elif choice == "REJECT" and self.isOnline:
                self.peerServer.connectedPeerSocket.send("REJECT".encode())
                self.peerServer.isChatRequested = 0
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> REJECT")
            # if choice is cancel timer for hello message is cancelled
            elif choice == "CANCEL":
                self.timer.cancel()
                break
        # if main process is not ended with cancel selection
        # socket of the client is closed
        if choice != "CANCEL":
            self.tcpClientSocket.close()

    # account creation function
    def createAccount(self, username, password):
        # join message to create an account is composed and sent to registry
        # if response is success then informs the user for account creation
        # if response is exist then informs the user for account existence
        try:
            message = "SIGN_UP" + "|" + username + "|" + password
            logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
            self.tcpClientSocket.send(message.encode())
            response = self.tcpClientSocket.recv(1024).decode()
            logging.info("Received from " + self.registryName + " -> " + response)
            if response == "SIGN_UP_SUCCESS":
                print(f"{Fore.GREEN}Account created successfully !")
            elif response == "USER_ALREADY_EXISTS":
                print(f"{Fore.RED} Account already exists.")
        except:
            print("Error in createAccount function")

    # login function
    def login(self, username, password, peerServerPort):
        # a login message is composed and sent to registry
        # an integer is returned according to each response
        try:
            message = "LOGIN" + "|" + username + "|" + password + "|" + str(peerServerPort)
            logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
            self.tcpClientSocket.send(message.encode())
            response = self.tcpClientSocket.recv(1024).decode()
            logging.info("Received from " + self.registryName + " -> " + response)
            if response == "LOGIN_SUCCESS":
                print(f"{Fore.GREEN}Logged in successfully !")
                return 1
            elif response == "USER_NOT_FOUND":
                print(f"{Fore.RED}Account does not exist.")
                return 0
            elif response == "USER_ALREADY_O192NLINE":
                print(f"{Fore.RED}Account is already online.")
                return 2
            elif response == "WRONG_PASSWORD":
                print(f"{Fore.RED}Wrong password.")
                return 3
        except:
            print("Error in login function")
        
    def hashedData(self, data):
        # Combine the password with the salt and hash it using SHA-256
        hashed_data = hashlib.sha256((data).encode('utf-8')).hexdigest()
        return hashed_data
    
    def createRoom(self, roomname, password):
        try:
            hashed_password = self.hashedData(password)
            message = "CREATE_CHAT_ROOM" +"|" + roomname + "|" + hashed_password
            logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
            self.tcpClientSocket.send(message.encode())
            response = self.tcpClientSocket.recv(1024).decode()
        
            logging.info("Received from " + self.registryName + " -> " + response)
            if response == "ROOM_CREATED":
                print("room created")
                self.joinRoom(roomname, password)
            elif response == "ROOM_NAME_EXISTS":
                print("choose another name")
        except:
            print("Error occured in createRoom function")
    
        # join room function
    def joinRoom(self, roomname, password):
        try:
            hashed_password = self.hashedData(password)
            message = "JOIN_CHAT_ROOM"+ "|" + roomname + "|" + hashed_password
            logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
            self.tcpClientSocket.send(message.encode())
            response = self.tcpClientSocket.recv(1024).decode()
            logging.info("Received from " + self.registryName + " -> " + response)
            if response == "JOINED":
                print("room joined")
            elif response == "ROOM_NOT_EXIST":
                print("room does not exist")
            elif response == "ROOM_WRONG_PASSWORD":
                print("wrong password")
        except:
            print("Error occured in joinRoom function")
    

    def showRooms(self):
        try:
            message = "SHOW_ROOMS"
            logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
            self.tcpClientSocket.send(message.encode())
            response = self.tcpClientSocket.recv(1024).decode()
            logging.info("Received from " + self.registryName + " -> " + response)
            if response == "NO_ROOMS":
                print("\nYou didn't join any room yet")
                return 0
            else:
                Rooms = ast.literal_eval(response)
                print("    Available Rooms:")
                for index, room in enumerate(Rooms, start=1):
                    print(f"[{index}] {room['roomname']}")
                return 1
        except:
            print("Error in showRooms function")
        

    def enterRoom(self, roomname):
        try:
            message = "ENTER_ROOM|" + roomname
            logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
            self.tcpClientSocket.send(message.encode())
            response = self.tcpClientSocket.recv(1024).decode()
            logging.info("Received from " + self.registryName + " -> " + response)
            if response == "VALID_ROOM":
                self.peerServer.isRoomRequested = 1
                self.peerServer.isChatRequested = 1
                members = self.roomMembers(roomname)    # retrieve room members
                if members:
                    roomMembers = ast.literal_eval(members)
                    print("\nRoom Members")
                    for member in roomMembers:
                        print(member["username"])
                    print("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")
                    self.sendRoomMessage(roomname)
            elif response == "INVALID_ROOM":
                print(f"{Fore.RED}\nYou don't have access to this room")
            elif response == "ROOM_NOT_EXIST":
                print(f"{Fore.RED}\nRoom does not exist...") 
        except:
            print("Error in enterRoom function")


    def roomMembers(self, roomname):
        try:
            message = "SEARCH_ROOM|" + roomname
            logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
            self.tcpClientSocket.send(message.encode())
            response = self.tcpClientSocket.recv(1024).decode()
            if response == "ROOM_EMPTY":
                print("\nRoom is empty")
                return 0
            else:
                return response
        except:
            print("Error in enterRoom function")
        
    def sendRoomMessage(self, roomname):
        try:
            print("\n                        Chat")
            members = self.getOnlineRoomMembers(roomname)
            if members:
                
                roomMembers = ast.literal_eval(members)
                for member in roomMembers:
                    cred = self.searchUser(member["username"])
                    if cred != 0 and cred != None:
                        memberCred = cred.split(':')
                        ip = memberCred[0]
                        port = memberCred[1]
                        msgSocket = socket(AF_INET, SOCK_STREAM)
                        msgSocket.connect((ip, int(port)))
                        message =  self.loginCredentials[0] + "|" + "JOINED" 
                        msgSocket.send(message.encode())
                        msgSocket.close()
            while 1:
                msg = input()
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[K")
                # sends the message to the connected peer, and logs it
                if msg != ":q":
                    messageFormatted = applyformatting(msg)
                    print("me: " + messageFormatted)
                members = self.getOnlineRoomMembers(roomname)
                if members:
                    roomMembers = ast.literal_eval(members)
                    for member in roomMembers:
                        cred = self.searchUser(member["username"])
                        if cred != 0 and cred != None:
                            memberCred = cred.split(':')
                            ip = memberCred[0]
                            port = memberCred[1]
                            msgSocket = socket(AF_INET, SOCK_STREAM)
                            msgSocket.connect((ip, int(port)))
                            message = self.loginCredentials[0] + "|" + msg
                            logging.info("Send to " + ip + ":" + port + " -> " + message)
                            msgSocket.send(message.encode())
                            msgSocket.close()
                if msg == ":q":
                    self.leaveRoom(roomname)
                    self.peerServer.isRoomRequested = 0
                    self.peerServer.isChatRequested = 0
                    break

        except:
            print("Error in sendRoomMessage function")


    def leaveRoom(self, roomname):
        try:
            message = "EXIT_ROOM|" + roomname
            logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
            self.tcpClientSocket.send(message.encode())
            print("\nYou have quit the room.")
        except:
            print("Error in leaveRoom function")
        
    def getOnlineRoomMembers(self, roomname):
        try:
            message = "SEARCH_ROOM_ONLINE|" + roomname
            logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
            self.tcpClientSocket.send(message.encode())
            response = self.tcpClientSocket.recv(1024).decode()
            if response == "ROOM_EMPTY":
                print("\nno members online\n")
                return 0
            else:
                return response
        except:
            print("Error in getOnlineRoomMembers function")
        
    def deleteRoom(self, roomname, password):
        try:
            hashed_password = self.hashedData(password)
            message = "DELETE_ROOM|" + roomname + "|" + hashed_password
            logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
            self.tcpClientSocket.send(message.encode())
            response = self.tcpClientSocket.recv(1024).decode()
            logging.info("Received from " + self.registryName + " -> " + response)
            if response == "ROOM_DELETED":
                print("\nRoom Deleted..." )
            elif response == "ROOM_NOT_EXIST":
                print("\nRoom doesn't exist")
            elif response == "ROOM_WRONG_PASSWORD":
                print("\nIncorrect password")
            elif response == "NOT_CREATOR":
                print("\nYou can't delete the room because you aren't the owner")
        except:
            print("Error in deleteRoom function")

    # logout function
    def logout(self, option):
        # a logout message is composed and sent to registry
        # timer is stopped
        try:
            if option == 1:
                message = "LOGOUT" + "|" + self.loginCredentials[0]
                self.timer.cancel()
            else:
                message = "LOGOUT"
            logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
            self.tcpClientSocket.send(message.encode())
        except:
            print("Error in logout function")

    def getOnlineUsers(self):
        try:

            message = "GET_ONLINE_PEERS"
            self.tcpClientSocket.send(message.encode())
            response = self.tcpClientSocket.recv(1024).decode().split('|')
            if response[0] != "NO_USERS_ONLINE" :
                for user in response:
                    print(f"{Fore.GREEN}-{user} is online")
            else:
                print(f"{Fore.RED} No users are currently online.")
        except:
            print("Error in getOnlineUsers function")
  

    # function for searching an online user
    def searchUser(self, username):
        # a search message is composed and sent to registry
        # custom value is returned according to each response
        # to this search message
        try:
            message = "SEARCH" + "|" + username
            logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
            self.tcpClientSocket.send(message.encode())
            response = self.tcpClientSocket.recv(1024).decode().split('|')
            logging.info("Received from " + self.registryName + " -> " + " ".join(response))
            if response[0] == "USER_FOUND":
                return response[1]
            elif response[0] == "USER_NOT_ONLINE":
                return 0
            elif response[0] == "USER_NOT_FOUND":
                return None
        except:
            print("Error in searchUser function")
        
    # function for sending hello message
    # a timer thread is used to send hello messages to udp socket of registry
    def sendHelloMessage(self):
        message = "HELLO" + "|" + self.loginCredentials[0]
        logging.info("Send to " + self.registryName + ":" + str(self.registryUDPPort) + " -> " + message)
        self.udpClientSocket.sendto(message.encode(), (self.registryName, self.registryUDPPort))
        self.timer = threading.Timer(1, self.sendHelloMessage)
        self.timer.start()

# Replace with your actual module and class

# peer is started
main = peerMain()