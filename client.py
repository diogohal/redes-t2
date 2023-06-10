import socket

# Cria um objeto socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Vincula o socket a um endereço IP e porta local
local_ip = '10.254.223.29'  # Endereço IP local
local_port = 12345  # Porta local
udp_socket.bind((local_ip, local_port))

# Endereço IP e porta remotos (Máquina 2)
remote_ip = '10.254.223.30'  # Endereço IP remoto
remote_port = 54321  # Porta remota

# Envie uma mensagem para a Máquina 2
message = 'Olá, Máquina 2!'
udp_socket.sendto(message.encode(), (remote_ip, remote_port))

# Receba dados da Máquina 2
data, addr = udp_socket.recvfrom(1024)  # Tamanho máximo dos dados recebidos
print('Mensagem recebida da Máquina 2:', data.decode())

# Feche o socket
udp_socket.close()