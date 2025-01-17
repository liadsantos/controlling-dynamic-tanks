import numpy as np
import matplotlib.pyplot as plt
import threading
import logging
import sys

from opcua import Client
from scipy.integrate import odeint
from multiprocessing.pool import ThreadPool

def tank1_model(h, t, input, out_tank2, H, r, R, gamma):
    """
    Define the right hand side of the tank dynamic equation.
    """

    if h < 0:
        logging.error('The level of the tank is negative - IMPOSSIBLE')
        sys.exit()

    A = np.pi * (r + (R-r)/H * h)**2
    dhdt = (input - gamma * np.sqrt(h) - out_tank2) / A

    return dhdt

def tank2_model(h, t, input, hot_input, out_tank3, H, r, R, gamma):
    if h < 0:
        logging.error('The level of the tank is negative - IMPOSSIBLE')
        sys.exit()

    A = np.pi * (r + (R-r)/H * h)**2
    dhdt = (input + hot_input - gamma * np.sqrt(h) - out_tank3) / A

    return dhdt

def tank3_model(h, t, input, cold_input, H, r, R, gamma):
    if h < 0:
        logging.error('The level of the tank is negative - IMPOSSIBLE')
        sys.exit()

    A = np.pi * (r + (R-r)/H * h)**2
    dhdt = (input + cold_input - gamma * np.sqrt(h)) / A

    return dhdt

def thread_tanks(h0, Q_i, Q_hot, Q_cold):
    """
    A thread tanques deve simular periodicamente a equacao dinamica dos tanques.
    O periodo dessa simulacao deve ser de no minimo 5s. Escolha parametros dos
    tanques conforme achar mais conveniente, especificando-os no relatorio final. 
    Utilize uma metodologia de integracao do tipo Runge-Kutta (o metodo de Euler e menos preciso).

    Parameters:
    -----------
    `h0`: [list]
        The 'zero' reference heights
    `Q_i`: [list]
        The control law inputs
    """
    # --- Define the parameters
    # Discharge coefficients
    gamma_1 = 5
    gamma_2 = 20
    gamma_3 = 60  
 
    # Radios (all tanks have the same size)
    r = 10
    R = 40

    # Height
    H = 70

    # Simulation time (5 seconds)
    simulation_time = np.linspace(0.0, 5.0, 100)    

    h1 = odeint(tank1_model, h0[0], simulation_time, args=(Q_i[0], Q_i[1], H, r, R, gamma_1))
    h2 = odeint(tank2_model, h0[1], simulation_time, args=(Q_i[1], Q_hot, Q_i[2], H, r, R, gamma_2))
    h3 = odeint(tank3_model, h0[2], simulation_time, args=(Q_i[2], Q_cold, H, r, R, gamma_3))

    return h1, h2, h3

def thread_control():
    """
    A thread controle deve efetuar o controle de nivel dos tres tanques a uma taxa de 1s. 
    Implemente uma lei de controle que lhe for mais simples, definindo niveis de 
    referencia href. Assuma condicoes iniciais nulas. A thread devera se comunicar com o
    servidor OPC UA, simulando o processo em questao, enviando e recebendo dados.
    """
    
    ### --- References
    h_ref = 50
    h_ref3 = 60                 
    T2_ref = 75  
    T3_ref = 15

    h0 = np.zeros(3,)           # zero condition for all three tanks
    Q_i = np.zeros(3,)          # actuator
    Q_hot = 0                   # actuator for hot water
    Q_cold = 0                  # actuator for cold water
    T = 25 * np.ones(3,)        # temperature of the tanks
    T_hot = 90                  # temperature of hot reservoir
    T_cold = -5                 # temperature of cold reservoir

    ### --- History of variables
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

    ### --- Auxiliary variables
    fill_tank2 = False
    fill_tank3 = False
    eps = 0.1
    delta = 1e-4                # avoid division by zero
    time_prev = 0   
    time2_prev = 0            
    I2 = 1                      # integrator of tank 2 (first value)
    I3 = 1

    ### --- Communicate with the server
    client_tanks = Client("opc.tcp://Laiss-Laptop.local:53530/OPCUA/SimulationServer")
    client_tanks.connect()
    logging.info("Thread control connected to server")

    servers = client_tanks.find_servers()
    logging.info("Find the available servers")

    for server in servers:
        logging.info("Server URI:", server.ApplicationUri)
        logging.info("Server ProductURI:", server.ProductUri)
        logging.info("Discovery URLs:", server.DiscoveryUrls)
    
    # get the nodes
    node_h1 = client_tanks.get_node("ns=3;s=h1")
    node_h2 = client_tanks.get_node("ns=3;s=h2")
    node_h3 = client_tanks.get_node("ns=3;s=h3")

    # @TODO: Julia, aqui eu passo as informacoes para o servidor OPCUA somente do tanque 1
    # @TODO: A ideia seria passar esses loops abaixo para o outro código "CLP"

    for i in range(500):
        # Control law tank 1
        T[0] = 25
        error1_level = h_ref - h0[0]
        Kp1_level = 50
        Q_i[0] = error1_level * Kp1_level

        if error1_level < 100 * eps and not fill_tank3:
            fill_tank2 = True

        if fill_tank2:
            # Control law tank 2
            error2_level = h_ref - h0[1]
            Kp2_level = 30
            Q_i[1] = error2_level * Kp2_level

            T[1] = (Q_i[1] * T[0] + Q_hot * T_hot) / (Q_i[1] + Q_hot + delta)
            error2_temp = T2_ref - T[1]

            # proportional:
            Kp2_temp = 5
            P2 = error2_temp * Kp2_temp + error2_level * Kp2_level

            # integrative:
            time = (i+1) * eps
            Ki2_temp = 5
            I2 += Ki2_temp * error2_temp * (time - time_prev)

            time_prev = time

            # final control action:
            Q_hot = P2 + I2

            if error2_level < 20 * eps and abs(error2_temp) < 10 * eps:
                fill_tank3 = True           
        
        if fill_tank3:
            # Control law tank 3
            error3_level = h_ref3 - h0[2]
            Kp3_level = 50
            Q_i[2] = error3_level * Kp3_level

            T[2] = (Q_i[2] * T[1] + Q_cold * T_cold) / (Q_i[2] + Q_cold + delta)
            error3_temp = T3_ref - T[2]

            # proportional:
            Kp3_temp = 4
            P3 = error3_temp * Kp3_temp + error3_level * Kp3_level

            # integrative:
            time2 = (i+1) * eps
            Ki3_temp = -5
            I3 += Ki3_temp * (error3_temp + error3_level) * (time2 - time2_prev)

            time2_prev = time2

            # final control action:
            Q_cold = P3 + I3

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

        # Send values to server
        node_h1.set_value(h0[0])
        node_h2.set_value(h0[1])
        node_h3.set_value(h0[2])

        # Call thread that simulates the tanks dynamics
        pool = ThreadPool(processes=1)
        new_h0 = pool.apply_async(thread_tanks, args=(h0, Q_i, Q_hot, Q_cold))
        h1, h2, h3 = new_h0.get()
        h0[0] = h1[-1].item()      # take the last value from ODE
        h0[1] = h2[-1].item()
        h0[2] = h3[-1].item()

        # Update the interface of visualization
        plt.clf()

        plt.subplot(3,1,1)
        plt.plot(time_steps, level_tank1, label=f'Level tank 1: {h0[0]:.4f}')
        plt.plot(time_steps, level_tank2, label=f'Level tank 2: {h0[1]:.4f}')
        plt.plot(time_steps, level_tank3, label=f'Level tank 3: {h0[2]:.4f}')
        plt.legend()

        plt.subplot(3,1,2)
        plt.plot(time_steps, valve_1, label=f'Valve 1: {Q_i[0]:.4f}')
        plt.plot(time_steps, valve_2, label=f'Valve 2: {Q_i[1]:.4f}')
        plt.plot(time_steps, valve_3, label=f'Valve 3: {Q_i[2]:.4f}')
        plt.plot(time_steps, valve_hot, label=f'Valve hot: {Q_hot:.4f}')
        plt.plot(time_steps, valve_cold, label=f'Valve cold: {Q_cold:.4f}')
        plt.legend()

        plt.subplot(3,1,3)
        plt.plot(time_steps, temp_tank1, label=f'Temperature tank1: {T[0]:.4f}')
        plt.plot(time_steps, temp_tank2, label=f'Temperature tank2: {T[1]:.4f}')
        plt.plot(time_steps, temp_tank3, label=f'Temperature tank3: {T[2]:.4f}')
        plt.legend()

        plt.pause(0.1)

    

if __name__ == "__main__":
    plt.ion()
    plt.show()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s'
    )

    thread_control()    