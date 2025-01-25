import logging
from opcua import Client
from opcua.ua import AttributeIds
import numpy as np
import matplotlib.pyplot as plt
import socket
import threading
import time
import select

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

from opcua import Client

def thread_OPC_client():
    Q_i = np.zeros(3,)
    
    # COnexão com o servidor TCP/IP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(b"Hello, world")
          
    
    # Conexão com o servidor OPC
    client_tanks = Client("opc.tcp://LAPTOP-2VIRAFSA:53530/OPCUA/SimulationServer")
    client_tanks.connect()
    logging.info("Thread control connected to server")

    servers = client_tanks.find_servers()
    logging.info("Find the available servers")

    for server in servers:
        logging.info(f"Server URI: {server.ApplicationUri}")
        logging.info(f"Server ProductURI: {server.ProductUri}")
        logging.info(f"Discovery URLs: {server.DiscoveryUrls}")
        
    root_node = client_tanks.get_root_node()
    objects_node = root_node.get_child(["0:Objects"])
    print("Nodos disponíveis no servidor:")
    for node in objects_node.get_children():
        print(node)
    
    # get the nodes
    node_h1 = client_tanks.get_node("ns=3;s=h1")
    node_h2 = client_tanks.get_node("ns=3;s=h2")
    node_h3 = client_tanks.get_node("ns=3;s=h3")

    ### --- History of variables
    time_steps = list()

    level_tank1 = list()
    level_tank2 = list()    
    level_tank3 = list()

    valve_1 = list()            # history of Q_1
    valve_2 = list()            # history of Q_2
    valve_3 = list()            # history of Q_3
    # valve_hot = list()          # history of Q_hot
    # valve_cold = list()         # history of Q_cold

    # temp_tank1 = list()
    # temp_tank2 = list()         
    # temp_tank3 = list()
    
    h0 = np.zeros(3,) 

    for i in range(500):
        # Append values for tracing
        data = s.recv(1024)
        
        if s.find("Q_i1") != -1:
            Q_i[0] = s[5:]
        elif  s.find("Q_i2") != -1:
            Q_i[1] = s[5:]
        elif  s.find("Q_i3") != -1:
            Q_i[2] = s[5:]

        print(f"Received {data!r}")
        time_steps.append(i)
        
        
        h0[0] = node_h1.get_value()
        h0[1] = node_h2.get_value()
        h0[2] = node_h3.get_value()
        
        level_tank1.append(h0[0])
        level_tank2.append(h0[1])
        level_tank3.append(h0[2])

        valve_1.append(Q_i[0])
        valve_2.append(Q_i[1])
        valve_3.append(Q_i[2])
        # valve_hot.append(Q_hot)
        # valve_cold.append(Q_cold)

        # temp_tank1.append(T[0])
        # temp_tank2.append(T[1])
        # temp_tank3.append(T[2])
        # Update the interface of visualization
        plt.clf()

        plt.subplot(3,1,1)
        plt.plot(time_steps, level_tank1, label=f'Level tank 1: {h0[0]:.4f}')
        plt.plot(time_steps, level_tank2, label=f'Level tank 2: {h0[1]:.4f}')
        plt.plot(time_steps, level_tank3, label=f'Level tank 3: {h0[2]:.4f}')
        plt.legend()

        # plt.subplot(3,1,2)
        # plt.plot(time_steps, valve_1, label=f'Valve 1: {Q_i[0]:.4f}')
        # plt.plot(time_steps, valve_2, label=f'Valve 2: {Q_i[1]:.4f}')
        # plt.plot(time_steps, valve_3, label=f'Valve 3: {Q_i[2]:.4f}')
        # plt.plot(time_steps, valve_hot, label=f'Valve hot: {Q_hot:.4f}')
        # plt.plot(time_steps, valve_cold, label=f'Valve cold: {Q_cold:.4f}')
        # plt.legend()

        # plt.subplot(3,1,3)
        # plt.plot(time_steps, temp_tank1, label=f'Temperature tank1: {T[0]:.4f}')
        # plt.plot(time_steps, temp_tank2, label=f'Temperature tank2: {T[1]:.4f}')
        # plt.plot(time_steps, temp_tank3, label=f'Temperature tank3: {T[2]:.4f}')
        # plt.legend()

        plt.pause(0.1)
        time.sleep(0.1)
    

def thread_TCP_IP_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

# Lista de sockets a serem monitorados (começando com o servidor)
    sockets_list = [server_socket]
    while True:
    # Usando select para esperar por eventos de leitura em sockets
        readable, writable, exceptional = select.select(sockets_list, [], [], 0.1)

        for sock in readable:
            if sock == server_socket:
            # Aceitar uma nova conexão
                client_socket, client_address = server_socket.accept()
                print(f"Nova conexão de {client_address}")
                sockets_list.append(client_socket)  # Adiciona o cliente à lista de sockets a serem monitorados
            else:
            # Receber dados de um cliente
                try:
                    data = sock.recv(1024)
                    if data:
                        print(f"Recebido: {data.decode('utf-8')}")
                        sock.sendall(data)  # Envia os dados de volta para o cliente (eco)
                    else:
                        # Se o cliente fechou a conexão
                        print(f"Cliente desconectado")
                        sockets_list.remove(sock)
                        sock.close()
                except:
                    print(f"Erro de comunicação com o cliente")
                    sockets_list.remove(sock)
                    sock.close()
    """
    Receive connections from TCP/IP clients to control the process
    """
    ...

if __name__ == "__main__":
    plt.ion()
    plt.show()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s'
    )

    # lock = threading.Lock()
    # opc_clp_thread = threading.Thread(target=thread_OPC_client)
    # opc_clp_thread.start()
    thread_TCP_IP_server()


