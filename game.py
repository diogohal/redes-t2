import socket
import getopt
import sys

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

def openSockets(machines):
    # Open the right and left socket in the wing network
    global machine
    global socket_left
    global socket_left_address
    global socket_right
    global socket_right_address
    
    # Receive socket
    if(machine > 1):
        rec_ip = machines[machine-1][0]
        rec_port = machines[machine-1][1]
    else:
        rec_ip = machines[machines[0]][0]
        rec_port = machines[machines[0]][1]
    
    socket_left = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    
    socket_left_address = (rec_ip, rec_port)

    # Send socket
    if(machine < machines[0]):
        send_ip = machines[machine+1][0]
        send_port = machines[machine+1][1]
    else:
        send_ip = machines[1][0]
        send_port = machines[1][1]
    
    socket_right = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    
    socket_right_address = (send_ip, rec_port)
       
def closeSockets():
    # Close left and right sockets
    socket_left.close()
    socket_right.close()
    
def sendMessage(socket, address, message):
    socket.sendto(message.encode(), address)

# ---------- MAIN PROGRAM ----------
machine = 0

if __name__ == "__main__":
    getScriptArguments(sys.argv)
machines = readConfigure()
if(machines[0] < 4):
    print('Use mais máquinas!')
    quit(2)

openSockets(machines)

message = 'Hello'
sendMessage(socket_right, socket_right_address, message)

socket_left.bind(socket_right_address)
while True:
    data, address = socket_left.recvfrom(1024)
    print(data)