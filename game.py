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
def printLine():
    print('-----------------------------------------------')

def createDeck():
    deck = []
    
    for i in range(13):
        for j in range(i):
            deck.append(i)

    deck.append(13)
    deck.append(13)

    shuffle(deck)

    return deck

def updateGameState(game_state, num_cards, min_card, passed, machine, rnd):
    game_state["num_cards"] = num_cards
    game_state["min_card"] = min_card
    if(passed == True):
        game_state["round_passed"] += 10**(machine-1)
    else:
        game_state["last_played"] = machine
    game_state["played"] += 10**(machine-1)
    game_state["round"] = rnd
    return game_state

def verifyPlay(hand, min_card, num_cards):
    for i in range(min_card):
        if(hand.count(i+1) >= num_cards):
            return True
    return False

def playSet(game_state, hand, machine):
    valid_play = False
    valid_choice = False
    play = 0
    
    # New turn
    if(game_state["end_turn"] == True):
        game_state["end_turn"] = False
    
    # End turn
    if(game_state["round_passed"] == 1111):
        game_state["turn"] += 1
        game_state["end_turn"] = True
        game_state["round"] = 0
        game_state["played"] = 0
        game_state["round_passed"] = 0
    return game_state
    
    # New round reset
    if(game_state["played"] == 1111):
        game_state["round"] += 1
        game_state["played"] = 0
        game_state["round_passed"] = 0
    
    print(f'Você precisa jogar {game_state["num_cards"]} cartas menores ou igual a {game_state["min_card"]}.')
    while not valid_play:
        printLine()
        print(hand)
        # First play
        if (game_state["round"] == 0 and game_state["played"] == 0):
                num_cards = int(input('Escolha o número de cartas que deseja jogar: '))
                min_card = int(input('Escolha a carta que deseja jogar: '))
                printLine()
                if num_cards > hand.count(min_card):
                    print('Jogada inválida!')
                    continue
                
                for i in range(num_cards):
                    hand.remove(min_card)
                    
                game_state = updateGameState(game_state, num_cards, min_card, False, machine, game_state["round"])
                valid_play = True
        # Next plays
        else:
            play = int(input('(1) Jogar uma carta\n(2) Passar a vez\nEscolha sua jogada: '))
            while(valid_choice == False):
                if(play != 1 and play != 2):
                    print('Escolha uma opção válida!')
                elif(play == 1 and verifyPlay(hand, game_state["min_card"], game_state["num_cards"]) == False):
                    print('Você não tem cartas para jogar! Escolha passar a vez.')
                else:
                    valid_choice = True
                    continue
                play = int(input('(1) Jogar uma carta\n(2) Passar a vez\nEscolha sua jogada: '))
            
            if play == 1:
                min_card = int(input('Escolha a carta que deseja jogar: '))
                printLine()
                print(hand.count(min_card))
                while valid_play == False:
                    if(hand.count(min_card) < game_state["num_cards"]):
                        print(f'Jogada inválida! Você precisa jogar um conjunto de {game_state["num_cards"]} cartas.')
                    elif(min_card > game_state["min_card"]):
                        print(f'Jogada inválida! A carta tem que ser menor que {game_state["min_card"]}.')
                    else:
                        valid_play = True
                        continue
                    min_card = int(input('Escolha a carta que deseja jogar: '))
                
                for i in range(game_state["num_cards"]):
                    hand.remove(min_card)
                
                game_state = updateGameState(game_state, game_state["num_cards"], min_card, False, machine, game_state["round"])
                
            elif play == 2:
                game_state = updateGameState(game_state, game_state["num_cards"], game_state["min_card"], True, machine, game_state["round"])
                valid_play = True

    return game_state

# ---------- MAIN PROGRAM ----------

if __name__ == "__main__":
    state = 0
    machine = 0
    bat = 0
    hand = []
    deck = []
    game_state = {
        "num_cards": 0,
        "min_card": 0,
        "turn": 0,
        "round": 0,
        "round_passed": 0,
        "played": 0,
        "last": 0,
        "dalmuti": 4,
        "end_turn": False
    }
    getScriptArguments(sys.argv)
    
    # Deal setup
    if(machine == 4):
        bat = 1
        deck = createDeck()
        
    machines = readConfigure()
    if(machines[0] < 4):
        print('Use mais máquinas!')
        quit(2)

    openSockets(machines, machine)

    while True:
        # ----- Setup state ----- 
        if(state == 0):
            # Other players
            if (machine != game_state["dalmuti"]):
                message = receiveMessage(left_socket)
                if(message["destiny"] == machine or message["destiny"] == 0):
                    if(message["play"]["empty_deck"] == 1):
                        hand.sort()
                        state = 1
                    else:
                        hand.append(message["play"]["deal_card"])
                message = confirmReceive(message, machine)
                sendMessage(right_socket, send_address, message)          
            
            # The deal
            elif(machine == game_state["dalmuti"]):
                while(deck != []):
                    hand.append(deck.pop())
                    for i in [1 , 2 , 3]:
                        card = deck.pop()
                        message = create_message(machine, {"empty_deck": 0, "deal_card": card}, i)
                        sendMessage(right_socket, send_address, message)
                        message = receiveMessage(left_socket)
                
                message = create_message(machine, {"empty_deck": 1}, 0) # send to everyone
                sendMessage(right_socket, send_address, message)
                message = receiveMessage(left_socket)
                state = 1

                        
            
        # ----- Playing state ----- 
        # Primeiro jogador joga uma quantidade de cartas de mesmo número
        # Jogadores seguintes devem jogar a mesma quantidade de cartas de um número igual ou menor
        # Rodada acaba quando todos passarem a vez
        elif(state == 1):                   
            if(bat == 0):
                message = receiveMessage(left_socket)
                print('mensagem recebida!', message)
                game_state = message["play"]["game_state"]
                if(message["destiny"] == machine):
                    bat = 1
                else:
                    sendMessage(right_socket, send_address, message)
            
                # message = confirmReceive(message, machine)
                # sendMessage(right_socket, send_address, message)
            else:
                game_state = playSet(game_state, hand, machine)
                if(game_state["end_turn"] == True):
                    message = create_message(machine, {"game_state": game_state, "pass_token": True}, game_state["last_played"])
                else:
                    if(machine+1 > machines[0]):
                        message = create_message(machine, {"game_state": game_state, "pass_token": True}, 1)
                    else:
                        message = create_message(machine, {"game_state": game_state, "pass_token": True}, machine + 1)
                sendMessage(right_socket, send_address, message)
                print('mensagem enviada!', message)
y                bat = 0

       