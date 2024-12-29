import numpy as np
import matplotlib.pyplot as plt
import threading
import logging
import opcua
import sys
import pandas as pd

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
    gamma_1 = 5
    gamma_2 = 20
    gamma_3 = ...   # @TODO: to define
 
    # Radios (all tanks have the same size)
    r = 10
    R = 40

    # Height
    H = 70

    # Simulation time
    simulation_time = np.linspace(0.0, 5.0, 100)    

    h1 = odeint(tank1_model, h0[0], simulation_time, args=(Q_i[0], Q_i[1], H, r, R, gamma_1))
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

    # References
    h_ref = 50
    T_ref = 75  
    h_ref3 = 0  # @TODO: to be defined

    h0 = np.zeros(3,)           # zero condition for all three tanks
    Q_i = np.zeros(3,)          # actuator
    Q_hot = 0                   # actuator for hot water
    T = 25 * np.ones(3,)        # temperature of the tanks
    T_hot = 90                  # temperature of hot reservoir

    # Aux variables
    level_tank1 = list()
    time_steps = list()
    valve_1 = list()
    valve_2 = list()
    valve_hot = list()
    temp_tank2 = list()
    level_tank2 = list()

    fill_tank2 = False
    eps = 0.1
    delta = 1e-4
    time_prev = 0
    I2 = 1

    # data_history = {}
    # data_history["Time"] = []
    # data_history["Hot valve"] = []
    # data_history["Temperature t2"] = []

    for i in range(100):
        # Control law tank 1
        T[0] = 25
        error1 = h_ref - h0[0]
        controller1 = 50
        Q_i[0] = error1 * controller1

        if error1 < 100 * eps:
            fill_tank2 = True

        if fill_tank2:
            # Control law tank 2
            error2_level = h_ref - h0[1]
            Kp2_level = 30
            Q_i[1] = error2_level * Kp2_level

            T[1] = (Q_i[1] * T[0] + Q_hot * T_hot) / (Q_i[1] + Q_hot + delta)
            error2_temp = T_ref - T[1]

            # proportional:
            Kp2_temp = 5
            P = error2_temp * Kp2_temp + error2_level * Kp2_level

            # integrative:
            time = (i+1) * eps
            Ki2_temp = 5
            I2 += Ki2_temp * error2_temp * (time - time_prev)

            time_prev = time

            # final control action:
            Q_hot = P + I2

        time_steps.append(i)
        level_tank1.append(h0[0])
        valve_1.append(Q_i[0])
        valve_2.append(Q_i[1])
        valve_hot.append(Q_hot)
        temp_tank2.append(T[1])
        level_tank2.append(h0[1])

        # Call thread that simulates the tanks dynamics
        pool = ThreadPool(processes=1)
        new_h0 = pool.apply_async(thread_tanks, args=(h0, Q_i, Q_hot))
        h1, h2, h3, sim_time = new_h0.get()
        h0[0] = h1[-1]
        h0[1] = h2[-1]

        plt.clf()

        plt.subplot(3,1,1)
        plt.plot(time_steps, level_tank1, label=f'Level tank 1: {h0[0]:.4f}')
        plt.plot(time_steps, level_tank2, label=f'Level tank 2: {h0[1]:.4f}')
        plt.legend()

        plt.subplot(3,1,2)
        plt.plot(time_steps, valve_1, label=f'Valve 1')
        plt.plot(time_steps, valve_2, label=f'Valve 2')
        plt.plot(time_steps, valve_hot, label=f'Valve hot: {Q_hot:.4f}')
        plt.legend()

        plt.subplot(3,1,3)
        plt.plot(time_steps, temp_tank2, label=f'Temperature tank2: {T[1]:.4f}')
        plt.legend()

        plt.pause(1.0)

        # data_history["Time"].append(i)
        # data_history["Hot valve"].append(Q_hot)
        # data_history["Temperature t2"].append(T[1])

        # df = pd.DataFrame(data_history)
        # df.to_csv("./debug/history.csv")


if __name__ == "__main__":
    plt.ion()
    plt.show()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s'
    )

    thread_control()    