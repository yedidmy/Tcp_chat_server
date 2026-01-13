import socket
import threading


SERVER_IP = "127.0.0.1"
SERVER_PORT = 666
BUFFER_SIZE = 1024

#create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (SERVER_IP, SERVER_PORT)
sock.connect(server_address)

nickname = input("Please enter a nickmame: ")

stop_threads = False

def recive():
    global stop_threads, nickname
    while not stop_threads:
        try:
            msg = sock.recv(BUFFER_SIZE).decode()

            while msg == "NICK" or msg == "NICK_A":
                if msg == "NICK":
                    sock.send(nickname.encode())
                elif msg == "NICK_A":
                    nickname = input("That nickname is already in use. Please pick another one: ")
                    sock.send(nickname.encode())
                msg = sock.recv(BUFFER_SIZE).decode()

            if msg == "kicked":
                print("You were kicked from the server")
                stop_threads = True
                sock.close()
            else:
                print(msg)

        except Exception as e:
            print("we had an error:", e)
            stop_threads = True
            sock.close()
            break


def write():
    global stop_threads
    while not stop_threads:
        try:
            msg = f"{nickname}: {input()}"
            sock.send(msg.encode())
        except:
            break


recive_tread = threading.Thread(target=recive)
write_thread = threading.Thread(target=write)

recive_tread.start()
write_thread.start()