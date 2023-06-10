import socket
import getopt
import sys
import json
from random import shuffle

# ---------- SCRIPT FUNCTIONS ----------
def getScriptArguments(argv):
    # Get the current machine number from argv
    global machine
    arg_help = f'Comando incorreto! Tente {argv[0]} -m <machine_number>.'
    
    try:
        opts, args = getopt.getopt(argv[1:], 'm:', ['machine'])
    except:
        print(arg_help)
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ('-m', '--machine'):
            machine = int(arg)

def readConfigure():
    # Return an array containing the configuration
    machines = []

    with open("configure.txt", "r") as configure:
        lines = configure.readlines()

    num_machines = int(lines[0].split(": ")[1])
    machines.append(num_machines)

    for i in range(2, len(lines), 5):
        host = lines[i+1].split(": ")[1].strip()
        port_send = int(lines[i+2].split(": ")[1])
        port_receive = int(lines[i+3].split(": ")[1])

        machine_info = [host, port_send, port_receive]
        machines.append(machine_info)

    return machines

def openSockets(machines, machine):
    # Open the right and left socket in the wing network
    global local_ip
    global left_socket
    global left_port
    global right_socket
    global send_address
    
    local_ip = str(machines[machine][0])
    
    # Left socket
    left_port = int(machines[machine][2])
    
    left_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    left_socket.bind((local_ip, left_port))

    # Right socket
    if(machine < machines[0]):
        right_socket_ip = machines[machine+1][0]
        right_socket_port = machines[machine+1][2]
    else:
        right_socket_ip = machines[1][0]
        right_socket_port = machines[1][2]
    
    right_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    right_socket.bind((local_ip, right_socket_port))
    send_address = (str(right_socket_ip), int(right_socket_port))
    
def closeSockets(socket_left, socket_right):
    # Close left and right sockets
    socket_left.close()
    socket_right.close()

# ---------- MESSAGE FUNCTIONS ----------
def create_message(machine, play, destiny):
    message = {
        "init_mark": 126,
        "origin": machine,
        "destiny": destiny,
        "play": play,
        "receive": 10**(machine-1),
        "end_mark": 127        
    }
    return message

def confirmReceive(message, machine):
    message["receive"] += 10**(machine-1)
    return message

def serializeData(message):
    serialized_data = json.dumps(message).encode()
    return serialized_data

def decodeData(serialized_data):
    decoded_data = serialized_data.decode()
    message = json.loads(decoded_data)
    return message

def sendMessage(socket, address, message):
    serialized_data = serializeData(message)
    socket.sendto(serialized_data, address)
    
def receiveMessage(socket):
    serialized_data, addr = socket.recvfrom(1024)
    message = decodeData(serialized_data)
    return message

# ---------- GAME FUNCTIONS ----------

def createDeck():
    deck = []
    
    for i in range(13):
        for j in range(i):
            deck.append(i)

    deck.append(13)
    deck.append(13)

    shuffle(deck)

    return deck

# Dar uma carta
# Passar a vez
# Jogar quantidade de cartas

# ---------- MAIN PROGRAM ----------

if __name__ == "__main__":
    state = 0
    machine = 0
    bat = 0
    hand = []
    deck = []
    getScriptArguments(sys.argv)
    

    # Deal setup
    if(machine == 4):
        deck = createDeck()
        
    machines = readConfigure()
    if(machines[0] < 4):
        print('Use mais máquinas!')
        quit(2)

    if(machine == 1):
        bat = 1

    openSockets(machines, machine)

    while True:
        # Setup state
        if(state == 0):
            # Other players
            if (machine != 4):
                message = receiveMessage(left_socket)
                if(message["destiny"] == machine):
                    if(message["play"]["empty_deck"] == 1):
                        state = 1
                    else:
                        hand.append(message["play"]["deal_card"])
                message = confirmReceive(message, machine)
                sendMessage(right_socket, send_address, message)          
            
            # The deal
            elif(machine == 4):
                while(deck != []):
                    hand.append(deck.pop())
                    for i in [1 , 2 , 3]:
                        card = deck.pop()
                        message = create_message(machine, {"empty_deck": 0, "deal_card": card}, i)
                        sendMessage(right_socket, send_address, message)
                        message = receiveMessage(left_socket)
                        
                for i in [1 , 2 , 3]:
                    message = create_message(machine, {"empty_deck": 1}, i)
                    sendMessage(right_socket, send_address, message)
                    message = receiveMessage(left_socket)
                    print(i, message)
                state = 1

                        
            
        # Playing state
        elif(state == 1):
            print('Mudou de estado!', hand)
            break
        
            if(bat == 0):
                message = receiveMessage(left_socket)
                print('Mensagem recebida!:', message)
                if(message["receive"] == 1111):
                    break
                message = confirmReceive(message, machine)
                sendMessage(right_socket, send_address, message)
            else:
                message = create_message(machine, 1)
                sendMessage(right_socket, send_address, message)
                print('Mensagem enviada!', message)
                bat = 0

        