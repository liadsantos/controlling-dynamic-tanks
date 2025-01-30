import logging
import numpy as np
import matplotlib.pyplot as plt
import socket
import threading
import time
import select
import queue

from opcua import Client

# Define the IP address and the server port
HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

mensagem_queue = queue.Queue()

def plot_dynamic(
        time_steps, 
        levels_tanks,
        input_valves,
        valve_hot,
        valve_cold,
        temperature_tanks,
        h0,
        T,
        Q_i,
        Q_hot,
        Q_cold
    ):

    plt.rcParams["figure.figsize"] = (12, 6)
    plt.clf()

    plt.subplot(3,1,1)
    plt.plot(time_steps, levels_tanks[0], label=f'Level tank 1: {h0[0]:.4f}')
    plt.plot(time_steps, levels_tanks[1], label=f'Level tank 2: {h0[1]:.4f}')
    plt.plot(time_steps, levels_tanks[2], label=f'Level tank 3: {h0[2]:.4f}')
    plt.legend()

    plt.subplot(3,1,2)
    plt.plot(time_steps, input_valves[0], label=f'Valve 1: {Q_i[0]:.4f}')
    plt.plot(time_steps, input_valves[1], label=f'Valve 2: {Q_i[1]:.4f}')
    plt.plot(time_steps, input_valves[2], label=f'Valve 3: {Q_i[2]:.4f}')
    plt.plot(time_steps, valve_hot, label=f'Valve hot: {Q_hot:.4f}')
    plt.plot(time_steps, valve_cold, label=f'Valve cold: {Q_cold:.4f}')
    plt.legend()

    plt.subplot(3,1,3)
    plt.plot(time_steps, temperature_tanks[0], label=f'Temperature tank1: {T[0]:.4f}')
    plt.plot(time_steps, temperature_tanks[1], label=f'Temperature tank2: {T[1]:.4f}')
    plt.plot(time_steps, temperature_tanks[2], label=f'Temperature tank3: {T[2]:.4f}')
    plt.legend()

    plt.pause(0.1)
    time.sleep(0.1)

def thread_OPC_client(queue):    
    ### --- Conexão com o servidor OPC
    client_tanks = Client("opc.tcp://Laiss-Laptop.local:53530/OPCUA/SimulationServer")
    client_tanks.connect()
    logging.info("Thread OPC client connected to server")

    servers = client_tanks.find_servers()
    logging.info("Find the available servers")

    for server in servers:
        logging.info(f"Server URI: {server.ApplicationUri}")
        logging.info(f"Server ProductURI: {server.ProductUri}")
        logging.info(f"Discovery URLs: {server.DiscoveryUrls}")
        
    # root_node = client_tanks.get_root_node()
    # objects_node = root_node.get_child(["0:Objects"])
    # logging.info("Nodos disponíveis no servidor:")
    # for node in objects_node.get_children():
    #     logging.info(node)
    
    # get the tank variables nodes
    node_h1 = client_tanks.get_node("ns=3;s=h1")
    node_h2 = client_tanks.get_node("ns=3;s=h2")
    node_h3 = client_tanks.get_node("ns=3;s=h3")
    
    # get the valve nodes
    node_q1 = client_tanks.get_node("ns=3;s=q1")
    node_q2 = client_tanks.get_node("ns=3;s=q2")
    node_q3 = client_tanks.get_node("ns=3;s=q3")
    node_qcold = client_tanks.get_node("ns=3;s=qcold")
    node_qhot = client_tanks.get_node("ns=3;s=qhot")

    # get the temperature nodes
    node_t1 = client_tanks.get_node("ns=3;s=T1")
    node_t2 = client_tanks.get_node("ns=3;s=T2")
    node_t3 = client_tanks.get_node("ns=3;s=T3")
    
    # get the MANUAL/AUTO control node
    node_init = client_tanks.get_node("ns=3;s=I1")
 
    # Finish all programs
    node_quit = client_tanks.get_node("ns=3;s=quit")

    logging.info("Got the nodes")

    ### --- History variables
    time_steps = list()

    level_tank1 = list()
    level_tank2 = list()    
    level_tank3 = list()

    valve_1 = list()            # history of Q_1
    valve_2 = list()            # history of Q_2
    valve_3 = list()            # history of Q_3
    valve_hot = list()          # history of Q_hot
    valve_cold = list()         # history of Q_cold

    temp_tank1 = list()
    temp_tank2 = list()         
    temp_tank3 = list()
    
    ### --- Set initial values to zero
    h0 = np.zeros(3,)
    node_h1.set_value(h0[0])
    node_h2.set_value(h0[1])
    node_h3.set_value(h0[2])

    Q_i = np.zeros(3,)
    node_q1.set_value(Q_i[0])
    node_q2.set_value(Q_i[1])
    node_q3.set_value(Q_i[2])

    T = 25 * np.ones(3,)
    node_t1.set_value(T[0])
    node_t2.set_value(T[1])
    node_t3.set_value(T[2])

    node_qcold.set_value(0)
    node_qhot.set_value(0)

    node_init.set_value(0)
    node_quit.set_value(False)

    ### --- Iterate the communication OPA UA client
    for i in range(500):
        init = node_init.get_value()
    
        if not queue.empty():
            mensagem = queue.get()
            logging.info(f"Recebida no OPC: {mensagem}")
            
            if "Q_i1" in mensagem and init == 0:
                Q_i[0] = mensagem.replace("Q_i1", "").strip()
                node_q1.set_value(Q_i[0])

            elif "Q_i2" in mensagem and init == 0:
                Q_i[1] = mensagem.replace("Q_i2", "").strip()
                node_q2.set_value(Q_i[1])

            elif "Q_i3" in mensagem and init == 0:
                Q_i[2] = mensagem.replace("Q_i3", "").strip()
                node_q3.set_value(Q_i[2])

            elif "Q_hot" in mensagem and init == 0:
                Q_hot = float(mensagem.replace("Q_hot", "").strip())
                node_qhot.set_value(Q_hot)

            elif "Q_cold" in mensagem and init == 0:
                Q_cold = float(mensagem.replace("Q_cold", "").strip())
                node_qcold.set_value(Q_cold)
            
            elif "Iniciar" in mensagem:
                node_init.set_value(1)
            
            elif "Encerrar" in mensagem:
                node_init.set_value(0)
            
            elif "Quit" in mensagem:
                node_quit.set_value(True)
        
        else:
            Q_i[0] = node_q1.get_value()
            Q_i[1] = node_q2.get_value()
            Q_i[2] = node_q3.get_value()
            Q_cold = node_qcold.get_value()
            Q_hot = node_qhot.get_value()
        
        h0[0] = node_h1.get_value()
        h0[1] = node_h2.get_value()
        h0[2] = node_h3.get_value()

        T[0] = node_t1.get_value()
        T[1] = node_t2.get_value()
        T[2] = node_t3.get_value()

        # Append values for tracing
        time_steps.append(i)

        level_tank1.append(h0[0])
        level_tank2.append(h0[1])
        level_tank3.append(h0[2])

        valve_1.append(Q_i[0])
        valve_2.append(Q_i[1])
        valve_3.append(Q_i[2])
        valve_hot.append(Q_hot)
        valve_cold.append(Q_cold)

        temp_tank1.append(T[0])
        temp_tank2.append(T[1])
        temp_tank3.append(T[2])

        # Update the interface of visualization
        plot_dynamic(
            time_steps, 
            [level_tank1, level_tank2, level_tank3], 
            [valve_1, valve_2, valve_3],
            valve_hot, 
            valve_cold,
            [temp_tank1, temp_tank2, temp_tank3],
            h0,
            T,
            Q_i,
            Q_hot,
            Q_cold
        )

def thread_TCP_IP_server(queue):   
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()      # wait for connections

    logging.info(f'Server listening on {HOST}:{PORT}')

    # Lista de sockets a serem monitorados (começando com o servidor)
    sockets_list = [server_socket]
    while True:
        # Usando select para esperar por eventos de leitura em sockets
        readable, writable, exceptional = select.select(sockets_list, [], [], 0.1)

        for sock in readable:
            if sock == server_socket:
                # Aceitar uma nova conexão
                client_socket, client_address = server_socket.accept()
                logging.info(f"Nova conexão de {client_address}")
                sockets_list.append(client_socket)  # Adiciona o cliente à lista de sockets a serem monitorados
            else:
                # Receber dados de um cliente
                try:
                    data = sock.recv(1024)
                    if data:
                        mensagem_recebida = data.decode()
                        logging.info(f"Recebido: {mensagem_recebida}") # Envia os dados de volta para o cliente (eco)
                    else:
                        # Se o cliente fechou a conexão
                        logging.info(f"Cliente desconectado")
                        sockets_list.remove(sock)
                        sock.close()
                except:
                    logging.info(f"Erro de comunicação com o cliente")
                    sockets_list.remove(sock)
                    sock.close()

                if any(keyword in mensagem_recebida for keyword in ("Q_", "Encerrar", "Iniciar", "Quit")):
                    queue.put(mensagem_recebida)
                    logging.info(f"Mensagem recebida: {mensagem_recebida}")
               
        time.sleep(0.1)

class ExcludeFilter(logging.Filter):
    def filter(self, record):
        # Exclude mensagens containing specific text
        return not any(excluded in record.getMessage() for excluded in ["received header", "read"])

if __name__ == "__main__":
    plt.ion()
    plt.show()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s'
    )
    logging.getLogger("opcua").setLevel(logging.WARNING)

    tcp_server_thread = threading.Thread(target=thread_TCP_IP_server, args=(mensagem_queue,))
    tcp_server_thread.start()

    thread_OPC_client(mensagem_queue)