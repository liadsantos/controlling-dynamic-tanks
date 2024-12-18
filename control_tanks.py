import numpy as np
import matplotlib.pyplot as plt
import threading
import logging
import opcua
import sys

from scipy.integrate import odeint
from multiprocessing.pool import ThreadPool

def tank_model(h, t, input, H, r, R, gamma):
    """
    Define the right hand side of the tank dynamic equation.
    """

    if h < 0:
        logging.error('The level of the tank is negative - IMPOSSIBLE')
        sys.exit()

    A = np.pi * (r + (R-r)/H * h)**2
    dhdt = (input - gamma * np.sqrt(h)) / A     # @TODO: don't forget to add the -q_(i+1)

    logging.info(f'Value of area = {A}')
    logging.info(f'Value of dynamics = {dhdt}')

    return dhdt

def thread_tanks(h0, Q_i):
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
    gamma_1 = 0.5 
    gamma_2 = 0.1
    gamma_3 = 0.4
 
    # Radios (all tanks have the same size)
    r = 10
    R = 40

    # Height
    H = 70

    # Simulation time (15 seconds, each 0.1 second)
    simulation_time = np.linspace(0.0, 5.0, 50)    

    h1 = odeint(tank_model, h0[0], simulation_time, args=(Q_i[0], H, r, R, gamma_1))
    h2 = 0
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
    h_ref1 = 50
    h_ref2 = 0  # @TODO: to be defined
    h_ref3 = 0  # @TODO: to be defined

    hyst = list()
    time_steps = list()
    for i in range(100):
        # Control laws
        erro1 = h_ref1 - h0[0]
        controler1 = 40
        Q_i[0] = erro1 * controler1

        time_steps.append(i)
        hyst.append(h0[0])

        logging.info('Calling process thread.')
        # tanks = threading.Thread(target=thread_tanks, args=(h0, Q_i))
        # tanks.start()
        # tanks.join()
        pool = ThreadPool(processes=1)
        new_h0 = pool.apply_async(thread_tanks, args=(h0, Q_i))
        h1, h2, h3, sim_time = new_h0.get()
        h0[0] = h1[-1]

        # print(h0[0])
        # print(time_steps)
        plt.clf()
        plt.plot(time_steps, hyst, label='Tank 1 height')
        plt.legend()
        plt.pause(1.0)


if __name__ == "__main__":
    plt.ion()
    plt.show()

    thread_control()