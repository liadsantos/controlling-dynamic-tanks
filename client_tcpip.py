import socket
import numpy as np

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

def thread_TCP_IP_client():

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        
        mensagem_enviar = ''
    
        print("\nDigite a variável que você deseja controlar:")
        print("1. Entrada de Líquido Tanque 1")
        print("2. Entrada de Líquido Tanque 2")
        print("3. Entrada de Líquido Tanque 3")
    
        escolha = input("Digite a sua escolha: ")
    
        if escolha == "1":
            valor_selecionado = input("Digite o valor da entrada de líquido: ")
            mensagem_enviar = f"Q_i1 {valor_selecionado}".encode()
        elif escolha == "2":
            valor_selecionado = input("Digite o valor da entrada de líquido: ")
            mensagem_enviar = f"Q_i1 {valor_selecionado}".encode()
        elif escolha == "3":
            valor_selecionado = input("Digite o valor da entrada de líquido: ")
            mensagem_enviar = f"Q_i1 {valor_selecionado}".encode()
    
        # Abre o arquivo no modo 'w' (write) para escrever
        with open("historiador.txt", "w") as arquivo:
            arquivo.write(f"Enviado: {mensagem_enviar} \n")
    
            s.sendall(mensagem_enviar)
    
            mensagem_recebida = s.recv(1024).decode()
    
            arquivo.write(f"Recebido: {mensagem_recebida} \n")
""""
Read and actuate on the process via OPC server
"""
...

thread_TCP_IP_client()