import socket
import getopt
import sys
import json
from random import shuffle
import os

# ---------- SCRIPT FUNCTIONS ----------
def getScriptArguments(argv):
    """ Get the current machine number.
    """
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
    """ Return an array containing the configuration file information.
    """
    machines = []

    with open("configure.txt", "r") as configure:
        lines = configure.readlines()

    # Append the number of machines
    num_machines = int(lines[0].split(": ")[1])
    machines.append(num_machines)

    # Append the machines information
    for i in range(2, len(lines), 5):
        host = lines[i+1].split(": ")[1].strip()
        port_send = int(lines[i+2].split(": ")[1])
        port_receive = int(lines[i+3].split(": ")[1])

        machine_info = [host, port_send, port_receive]
        machines.append(machine_info)

    return machines

def openSockets(machines, machine):
    """ Open the right and left socket in the wing network for the machine.
        The left socket is the one where the machine will listen.
        The right socket is the one where the machine will send messages.
    """
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
    else:
        right_socket_ip = machines[1][0]
    right_socket_port = machines[machine][1]
    
    right_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    right_socket.bind((local_ip, right_socket_port))
    send_address = (str(right_socket_ip), int(right_socket_port))
    
def closeSockets(socket_left, socket_right):
    """ Close left and right sockets
    """
    socket_left.close()
    socket_right.close()

# ---------- MESSAGE FUNCTIONS ----------
def create_message(machine, play, destiny):
    """ Create a message to send in the wing network
    """
    message = {
        "init_mark": 126,
        "origin": machine,
        "destiny": destiny,
        "play": play,
        "receive": {f"machine{machine}": True},
        "end_mark": 127        
    }
    return message

def confirmReceive(message, machine):
    """ Confirm a message from wing network
    """
    message["receive"][f"machine{machine}"] = True
    return message

def serializeData(message):
    """ Transform dictionary type into serialized data to send to wing network
    """
    serialized_data = json.dumps(message).encode()
    return serialized_data

def decodeData(serialized_data):
    """ Decode data receive from wing network
    """
    decoded_data = serialized_data.decode()
    message = json.loads(decoded_data)
    return message

def sendMessage(socket, address, message):
    """ Send message to wing network
    """
    serialized_data = serializeData(message)
    socket.sendto(serialized_data, address)
    
def receiveMessage(socket):
    """ Receive message from wing network
    """
    serialized_data, addr = socket.recvfrom(1024)
    message = decodeData(serialized_data)
    return message

# ---------- GAME FUNCTIONS ----------
def printLine():
    print('-----------------------------------------------')

def initializeDicionary(dictionary, num_machines):
    """ Inicialize a dictionary with machinei = False
    """
    for i in range(1, num_machines+1):
        dictionary[f"machine{i}"] = False

def checkDictionaryTrue(dictionary):
    """ Check if every element in the dictionary is true
    """
    for i in dictionary.values():
        if(i == False):
            return False
    return True

def checkDictionaryFalse(dictionary):
    """ Check if every element in the dictionary is false
    """
    for i in dictionary.values():
        if(i == True):
            return False
    return True

def createDeck():
    """ Dalmuti machine initialize a new deck of cards
    """
    deck = []
    for i in range(13):
        for j in range(i):
            deck.append(i)
    deck.append(13)
    deck.append(13)
    shuffle(deck)
    return deck

def updateGameState(game_state, num_cards, min_card, passed, machine, rnd):
    """ Update the game state
    """
    game_state["num_cards"] = num_cards
    game_state["min_card"] = min_card
    if(passed == True):
        game_state["round_passed"][f"machine{machine}"] = True
    else:
        game_state["last_played"] = machine
    game_state["played"][f"machine{machine}"] = True
    game_state["round"] = rnd
    return game_state

def verifyPlay(hand, min_card, num_cards):
    """ Verify if the player has enough cards to play
    """
    for i in range(min_card):
        if(hand.count(i+1) + hand.count(13) >= num_cards):
            return True
    return False

def handleHand(num_cards, min_card, joker, jokerList):
    """ Handle the hand content after a play
    """
    global hand

    # If the player doesn't have enough cards to play, but it has jokers that complete the set
    if (num_cards > hand.count(min_card)) and num_cards <= (hand.count(min_card) + len(jokerList)):
        loop = 1
        # Choose if wants to play with jokers
        while(loop == 1):
            try:
                print('Você vai utilizar seu(s) coringa(s) para completar a mão! Deseja continuar?\n')
                use = int(input('(1)Sim (2) Não\n'))
                loop = 0
            except KeyboardInterrupt:
                exit()
            except:
                print('Entrada Incorreta! Coloque uma opção válida!')

        if (use == 2):
            return False
        
        # If yes, the cards are removed from hand
        if num_cards < hand.count(min_card) + len(jokerList):
            for i in range(len(jokerList)):
                hand.remove(13)
            for i in range(num_cards - len(jokerList)):
                hand.remove(min_card)
        else:
            hand.remove(13)
            for i in range(num_cards - 1):
                hand.remove(min_card)  
                
    # If the player has enough cards to play and also has jokers
    elif (num_cards <= hand.count(min_card) and num_cards <= hand.count(min_card) + len(jokerList) and len(jokerList) > 0):
        loop = 1
        # Choose if wants to complete the set with or without jokers
        while(loop == 1):
            try:
                print('Você pode completar a mão com ou sem os coringas, quer utilizar eles?\n')
                use = int(input('(1)Sim (2) Não\n'))
                loop = 0
            except KeyboardInterrupt:
                exit()
            except:
                print('Entrada Incorreta! Coloque uma opção válida!')

        if use == 2:
            for i in range(num_cards):
                hand.remove(min_card)
        
        elif use == 1 and len(jokerList) == 1:
            hand.remove(13)
            for i in range(num_cards-1):
                hand.remove(min_card)
                
        # Choose if wants to use one or two jokers 
        elif use == 1 and len(jokerList) == 2:
            loop = 1
            while(loop == 1):
                try:
                    print('Você pode usar 1 ou 2 coringas, o que deseja fazer?\n')
                    newUse = int(input('(1) Usar 1 Coringa (2) Usar 2 Coringas\n'))
                    loop = 0
                except KeyboardInterrupt:
                    exit()
                except:
                    print('Entrada Incorreta! Coloque uma opção válida!')

            if newUse == 1:
                hand.remove(13)
                for i in range(num_cards-1):
                    hand.remove(min_card)
            elif newUse == 2:
                hand.remove(13)
                hand.remove(13)
                for i in range(num_cards-2):
                    hand.remove(min_card)
                    
    # If the player has enough cards to play, but doesn't have jokers
    elif (num_cards <= hand.count(min_card) and len(jokerList) == 0):
        for i in range(num_cards):
                hand.remove(min_card)
    
    return True


def playSet(game_state, hand, machine):
    """ Player's move
    """
    global machines

    # Important variables
    joker = filter(lambda x: (x == 13), hand)
    jokerList = list(joker)    
    valid_play = False
    valid_choice = False
    play = 0
    
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # If it's a new turn, change the game state
    if(game_state["end_turn"] == True):
        game_state["end_turn"] = False
    
    # The turn ends when everyone has passed
    if(checkDictionaryTrue(game_state["round_passed"])):
        game_state["turn"] += 1
        game_state["min_card"] = 0
        game_state["num_cards"] = 0
        game_state["end_turn"] = True
        game_state["round"] = 0
        initializeDicionary(game_state["round_passed"], machines[0])
        initializeDicionary(game_state["played"], machines[0])
        return game_state
    
    # Round reset when everyone has played
    if(checkDictionaryTrue(game_state["played"])):
        game_state["round"] += 1
        initializeDicionary(game_state["played"], machines[0])
        initializeDicionary(game_state["round_passed"], machines[0])
    
    # Player's move
    while not valid_play:
        printLine()
        print(hand)
        
        # ---------- First play of the round ----------
        if (game_state["round"] == 0 and checkDictionaryFalse(game_state["played"])):
            loop = 1
            # Choose the set lenght and which card will play
            while(loop == 1):
                try:
                    num_cards = int(input('Escolha o número de cartas que deseja jogar: '))
                    min_card = int(input('Escolha a carta que deseja jogar: '))
                    loop = 0
                except KeyboardInterrupt:
                    exit()
                except:
                    print('Entrada Incorreta! Coloque uma opção válida!')

            printLine()
            
            # If the player doesn't have enough cards, the play is not valid
            if (num_cards > hand.count(min_card) and num_cards > (hand.count(min_card) + len(jokerList))):
                print('Jogada inválida!')
                continue
            
            # If the player doesn't want to complete the set with jokers and doesn't have enough cards, the play is not valid
            if (not handleHand(num_cards, min_card, joker, jokerList)):
                continue
            
            # Update the game state
            game_state = updateGameState(game_state, num_cards, min_card, False, machine, game_state["round"])
            
            # If the hand is empty, game is over
            if(len(hand) == 0):
                game_state["end_game"] = True              
                    
            valid_play = True
            
        # ---------- When it's not the first play of the round ----------
        else:
            loop = 1
            # Choose the move: play a card or pass
            while(loop == 1):
                try:
                    print(f'Você precisa jogar {game_state["num_cards"]} cartas menores ou igual a {game_state["min_card"]}.')
                    play = int(input('(1) Jogar uma carta\n(2) Passar a vez\nEscolha sua jogada: '))
                    loop = 0
                except KeyboardInterrupt:
                    exit()
                except:
                    print('Entrada Incorreta! Coloque uma opção válida!')

            # Validate move and treat invalid inputs
            while(valid_choice == False):
                # If the command doesn't exist
                if(play != 1 and play != 2):
                    print('Escolha uma opção válida!')
                # If the player doesn't have enough cards to play
                elif(play == 1 and verifyPlay(hand, game_state["min_card"], game_state["num_cards"]) == False):
                    print('Você não tem cartas para jogar! Escolha passar a vez.')
                # Validate move 
                else:
                    valid_choice = True
                    continue
                
                loop = 1
                while(loop == 1):
                    try:
                        play = int(input('(1) Jogar uma carta\n(2) Passar a vez\nEscolha sua jogada: '))
                        loop = 0
                    except KeyboardInterrupt:
                        exit()
                    except:
                        print('Entrada Incorreta! Coloque uma opção válida!')
            
            # ----- Play card move ----- 
            if play == 1:
                loop = 1
                # Pick a card
                while(loop == 1):
                    try:
                        min_card = int(input('Escolha a carta que deseja jogar: '))
                        loop = 0
                    except KeyboardInterrupt:
                        exit()
                    except:
                        print('Entrada Incorreta! Coloque uma opção válida!')

                printLine()
                while valid_play == False:
                    # If doesn't have enough cards to play with the selected one
                    if(hand.count(min_card) + len(jokerList) < game_state["num_cards"]):
                        print(f'Jogada inválida! Você precisa jogar um conjunto de {game_state["num_cards"]} cartas.')
                    # If the selected card is greater than the min_card
                    elif(min_card > game_state["min_card"]):
                        print(f'Jogada inválida! A carta tem que ser menor que {game_state["min_card"]}.')
                    # Validate play
                    else:
                        valid_play = True
                        continue
                    
                    loop = 1
                    while(loop == 1):
                        try:
                            min_card = int(input('Escolha a carta que deseja jogar: '))
                            loop = 0
                        except KeyboardInterrupt:
                            exit()
                        except:
                            print('Entrada Incorreta! Coloque uma opção válida!')
                if (handleHand(game_state["num_cards"], min_card, joker, jokerList) == False):
                    print(f'Você precisa de coringas para completar o conjunto da carta {min_card}')
                    valid_play = False
                    continue
                
                # Update the game state after play move
                game_state = updateGameState(game_state, game_state["num_cards"], min_card, False, machine, game_state["round"])

                # If the hand is empty, game is over
                if(len(hand) == 0):
                    game_state["end_game"] = True
            
            # ----- Pass move ----- 
            elif play == 2:
                # Update the game state after pass move
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
        "round_passed": {},
        "played": {},
        "last": 0,
        "dalmuti": 0,
        "end_turn": False,
        "end_game": False
    }
    
    # Get script arguments and configuration
    getScriptArguments(sys.argv)
    machines = readConfigure()

    # Deal setup and Dalmuti setup
    if(machine == machines[0]):
        bat = 1
        game_state["dalmuti"] = machine
        deck = createDeck()

    initializeDicionary(game_state["round_passed"], machines[0])
    initializeDicionary(game_state["played"], machines[0])

    # If it doesn't have enough machines
    if(machines[0] < 4):
        print('Use mais máquinas!')
        quit(2)
    
    # Open right and left sockets
    openSockets(machines, machine)

    while True:
        # ---------- Setup state ---------- 
        if(state == 0):
            # Other players wait for card distribution
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
            
            # The deal distribute cards for other players
            elif(machine == game_state["dalmuti"]):
                while(deck != []):
                    hand.append(deck.pop())
                    for i in range(1, machines[0]):
                        card = deck.pop()
                        message = create_message(machine, {"empty_deck": 0, "deal_card": card}, i)
                        sendMessage(right_socket, send_address, message)
                        message = receiveMessage(left_socket)
                
                # Send cards distribution finished to everyone
                message = create_message(machine, {"empty_deck": 1}, 0) # send to everyone
                sendMessage(right_socket, send_address, message)
                message = receiveMessage(left_socket)
                state = 1
                hand.sort()
                
        # ---------- Playing state ---------- 
        elif(state == 1):                   
            # If the player doesn't have the bat, it waits for the next message
            if(bat == 0):
                message = receiveMessage(left_socket)
                game_state = message["play"]["game_state"]
                # If the bat is passed to the machine, continue
                if(message["destiny"] == machine and message["play"]["pass_token"] == True):
                    bat = 1
                # If the bat is not passed to the machine OR de destiny is not the machine, send it to right
                else:
                    sendMessage(right_socket, send_address, message)
                    if(game_state["end_game"] == True):
                        print(f'Fim de jogo! Computador {message["origin"]} ganhou!')
                        quit()
            
            # If the player has the bat
            else:
                # Player move
                game_state = playSet(game_state, hand, machine)
                # If the game is over, send a message to everyone
                if(game_state["end_game"] == True):
                    message = create_message(machine, {"game_state": game_state, "pass_token": False}, 0)
                # If the turn is over, pass the bat to the next dalmuti
                elif(game_state["end_turn"] == True):
                    message = create_message(machine, {"game_state": game_state, "pass_token": True}, game_state["last_played"])
                # Else, pass the bat to the next machine in the wing network
                else:
                    if(machine+1 > machines[0]):
                        message = create_message(machine, {"game_state": game_state, "pass_token": True}, 1)
                    else:
                        message = create_message(machine, {"game_state": game_state, "pass_token": True}, machine + 1)
                sendMessage(right_socket, send_address, message)
                bat = 0

        