import socket
import threading

HOST = "10.10.5.27"
LISTEN_PORT = 666
BUFFER_SIZE = 1024

clients = []
nicknames = []
banned_users = []

# Create a TCP/IP socket
listening_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (HOST, LISTEN_PORT)
listening_sock.bind(server_address)

print("litening for clients...")
listening_sock.listen()


#broadcast the message to all clients
def broadcast(msg):
    for client in clients:
        try:
            client.send(msg.encode())
        #if the client is not connected, remove it
        except:
            remove_client(client)


#connect the client to the server
def connect_client():
    while True:
        #accept the client
        client_soc, client_address = listening_sock.accept()

        #ask the client for a nickname
        client_soc.send("NICK".encode())
        nickname = client_soc.recv(BUFFER_SIZE).decode()

        #if the nickname is already taken, ask the client for a new nickname
        while nickname in nicknames:
            client_soc.send("NICK_A".encode())
            nickname = client_soc.recv(BUFFER_SIZE).decode()

        #if the nickname is banned, kick the client
        if nickname in banned_users:
            client_soc.send("kicked".encode())
            client_soc.close()

        #add the client to the list
        nicknames.append(nickname)
        clients.append(client_soc)

        #notify the other clients that the client is connected
        notify_all(f"{nickname} connected to the chat!", print_msg=False)
        print(f"{nickname} connected from {client_address}!")
        #start a new thread to handle the client
        handle_thread = threading.Thread(target=handle_clients, args=(client_soc,))
        handle_thread.start()


def handle_clients(client):
    try:
        while True:
            #receive the message from the client
            msg = client.recv(BUFFER_SIZE).decode()

            #if the message is a kick command, kick the user
            if msg.split(":", 1)[1].startswith(" !kick"):
                sender = msg.split(":", 1)[0]
                to_kick = msg.split(" ")[2]
                kick_user(to_kick, sender)

            #if the message is a private message command, send the message to the user
            elif msg.split(":", 1)[1].startswith(" !private"):
                #get the sender destination and message
                sender = msg.split(":", 1)[0]
                try:
                    dst = msg.split(" ")[2]
                    message = msg.split(" ", 3)[3]
                    #send the message to the user
                    status_msg = private_msg(sender, dst, message)
                    if status_msg:
                        private_msg("Admin", sender, status_msg)
                except:
                    private_msg("Admin", sender, "invalid request format")

            #if the message is a ban command, ban the user
            elif msg.split(":", 1)[1].startswith(" !ban"):
                sender = msg.split(":", 1)[0]
                to_ban = msg.split(" ")[2]
                ban_user(sender, to_ban)

            elif msg.split(":", 1)[1].startswith(" !unban"):
                sender = msg.split(":", 1)[0]
                to_unban = msg.split(" ")[2]
                unban_user(sender, to_unban)

            elif msg.split(":", 1)[1].startswith(" !online"):
                sender = msg.split(":", 1)[0]
                notify_all(f"{len(clients)} online users: {', '.join(nicknames)}", to_nickname=sender, print_msg=False)

            elif msg.split(":", 1)[1].startswith(" !commands"):
                commands_list = """Commands:
    Admin only:
        Kick user - !kick <username>
        Ban user - !ban <username>
        Unban user - !unban <username>

    Everyone:
        Command list - !commands
        Private message - !private <username> <message>
        Online users - !online"""
                sender = msg.split(":", 1)[0]
                notify_all(commands_list, to_nickname=sender, print_msg=False)

            #if the message is not a command, broadcast the message to all clients
            else:
                broadcast(msg)

    #if the client is not connected, remove it
    except:
        user_left_msg = remove_client(client)
        if user_left_msg:
            notify_all(user_left_msg)

#remove the client from the list
def remove_client(client):
    #if the client is in the list
    if client in clients:
        #get the index of the client
        index = clients.index(client)
        #remove the client from the list
        clients.remove(client)
        #close the client socket
        try:
            client.close()
        except:
            pass
        #if the clients nickname is in the list
        if index < len(nicknames):
            #get the nickname of the client
            nickname = nicknames[index]
            #remove the nickname from the list
            nicknames.remove(nickname)
            return f"{nickname} left the chat!"
    return ""

#kick the user
def kick_user(to_kick_nickname, kicker_nickname, silent=False):
    #if the user is in the list
    if to_kick_nickname in nicknames:
        #if the user is in the list
        if kicker_nickname == "yedid" or kicker_nickname == "Admin":
            #get the index of the user
            index = nicknames.index(to_kick_nickname)
            #get the client of the user
            client = clients[index]
            #try to kick the user
            try:
                client.send("kicked".encode())
            except:
                pass
            remove_client(client)
            if not silent and to_kick_nickname not in banned_users:
                notify_all(f"{to_kick_nickname} got kicked", print_msg=False)
        #if the kicker is not "yedid" or "Admin"
        else:
            #notify the kicker that he doesn't have the permission to kick
            notify_all("you don't have the permission to kick", to_nickname=kicker_nickname, print_msg=False)
    #if the user is not in the list
    else:
        notify_all(f"{to_kick_nickname} isn't connected", to_nickname=kicker_nickname, print_msg=False)

def ban_user(sender, to_ban):
    if sender == "yedid":
        if to_ban not in banned_users:
            kick_user(to_ban, "Admin", silent=True)
            banned_users.append(to_ban)
            notify_all(f"{to_ban} got banned!")
        else:
            notify_all(f"{to_ban} is already banned", to_nickname=sender, print_msg=False)
    else:
        notify_all("you don't have the permission to ban", to_nickname=sender, print_msg=False)

def unban_user(sender, to_unban):
    if sender == "yedid":
        if to_unban in banned_users:
            banned_users.remove(to_unban)
            notify_all(f"{to_unban} is no longer banned")
        else:
            notify_all(f"{to_unban} is not banned", to_nickname=sender, print_msg=False)
    else:
        notify_all("you don't have the permission to unban", to_nickname=sender, print_msg=False)
def private_msg(sender, send_to, msg):
    if send_to in nicknames:
        index = nicknames.index(send_to)
        client_soc = clients[index]
        try:
            client_soc.send(f"[Private] {sender}: {msg}".encode())
            return None
        except:
            remove_client(client_soc)
            return f"User '{send_to}' is no longer connected"
    else:
        return f"User '{send_to}' is not connected"

def notify_all(message, to_nickname=None, sender="Admin", broadcast_msg=True, print_msg=True):
    if print_msg:
        print(message)
    if to_nickname:
        private_msg(sender, to_nickname, message)
    elif broadcast_msg:
        broadcast(message)


def stats():
    print(f"{len(clients)} connected users: {', '.join(nicknames)}")
    print(f"{len(banned_users)} banned users: {', '.join(banned_users)}")

def get_stats():
    while True:
        txt = input()
        if txt == "1":
            stats()

stats_thread = threading.Thread(target=get_stats)
stats_thread.start()
connect_client()
