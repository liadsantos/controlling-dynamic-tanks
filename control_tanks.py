import numpy as np
import matplotlib.pyplot as plt
import threading
import logging
import opcua
import sys

from scipy.integrate import odeint
from multiprocessing.pool import ThreadPool

def tank1_model(h, t, input, H, r, R, gamma):
    """
    Define the right hand side of the tank dynamic equation.
    """

    if h < 0:
        logging.error('The level of the tank is negative - IMPOSSIBLE')
        sys.exit()

    A = np.pi * (r + (R-r)/H * h)**2
    dhdt = (input - gamma * np.sqrt(h)) / A     # @TODO: don't forget to add the -q_(i+1)

    return dhdt

def tank2_model(h, t, input, hot_input, H, r, R, gamma):
    if h < 0:
        logging.error('The level of the tank is negative - IMPOSSIBLE')
        sys.exit()

    A = np.pi * (r + (R-r)/H * h)**2
    dhdt = (input + hot_input - gamma * np.sqrt(h)) / A     # @TODO: don't forget to add the -q_(i+1)

    return dhdt

def thread_tanks(h0, Q_i, Q_hot):
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
    gamma_1 = 5.0
    gamma_2 = 0.5
    gamma_3 = ...   # @TODO: to define
 
    # Radios (all tanks have the same size)
    r = 10
    R = 40

    # Height
    H = 70

    # Simulation time
    simulation_time = np.linspace(0.0, 5.0, 50)    

    h1 = odeint(tank1_model, h0[0], simulation_time, args=(Q_i[0], H, r, R, gamma_1))
    h2 = odeint(tank2_model, h0[1], simulation_time, args=(Q_i[1], Q_hot, H, r, R, gamma_2))
    h3 = 0

    return h1, h2, h3, simulation_time

def thread_control():
    """
    A thread controle deve efetuar o controle de nivel dos tres tanques a uma taxa de 1s. 
    Implemente uma lei de controle que lhe for mais simples, definindo niveis de 
    referencia href. Assuma condicoes iniciais nulas. A thread devera se comunicar com o
    servidor OPC UA, simulando o processo em questao, enviando e recebendo dados.
    """
    
    # @TODO: define if I call the loop here or in the main thread

    h0 = np.zeros(3,)   # zero condition for all three tanks
    Q_i = np.zeros(3,)  # actuator
    Q_hot = 0           # actuator for hot water
    T = np.zeros(3,)    # temperature of the tanks
    T_hot = 90          # temperature of hot reservoir

    # References
    h_ref = 50
    T_ref = 75  
    h_ref3 = 0  # @TODO: to be defined

    # Aux variables
    level_tank1 = list()
    time_steps = list()
    valve_1 = list()
    stop_valve1 = False
    eps = 0.1

    for i in range(50):
        # Control law tank 1
        T[0] = 25
        erro1 = h_ref - h0[0]
        if erro1 < eps:
            stop_valve1 = True      # if the level is ok for tank 1, turn off input valve
            Q_i[0] = 0
    
        elif erro1 >= eps and not stop_valve1:
            controler1 = 20
            Q_i[0] = erro1 * controler1

        # Control law tank 2
        # How the temperature is related to valve hot?

        time_steps.append(i)
        level_tank1.append(h0[0])
        valve_1.append(Q_i[0])

        logging.info('Calling process thread.')
        # tanks = threading.Thread(target=thread_tanks, args=(h0, Q_i))
        # tanks.start()
        # tanks.join()
        pool = ThreadPool(processes=1)
        new_h0 = pool.apply_async(thread_tanks, args=(h0, Q_i))
        h1, h2, h3, sim_time = new_h0.get()
        h0[0] = h1[-1]

        plt.clf()

        plt.subplot(2,1,1)
        plt.plot(time_steps, level_tank1, label='Level tank 1')
        plt.legend()

        plt.subplot(2,1,2)
        plt.plot(time_steps, valve_1, label='Valve 1')
        plt.legend()

        plt.pause(1.0)


if __name__ == "__main__":
    plt.ion()
    plt.show()

    thread_control()    