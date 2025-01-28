import socket
import numpy as np
import threading

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

def thread_TCP_IP_client():

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        loop_comunicacao = 1
        
        with open("historiador.txt", "w", buffering=1) as arquivo:
        
            while loop_comunicacao == 1:
                mensagem_enviar = ''
    
                print("\nDigite a variável que você deseja controlar:")
                print("1. Entrada de Líquido Tanque 1")
                print("2. Entrada de Líquido Tanque 2")
                print("3. Entrada de Líquido Tanque 3")
                print("4. Iniciar Controle Automático")
                print("5. Encerrar Controle Automático")
                print("6. Encerrar conexão")
    
                escolha = input("Digite a sua escolha: ")
    
                if escolha == "1":
                    valor_selecionado = input("Digite o valor da entrada de líquido: ")
                    mensagem_enviar = f"Q_i1 {valor_selecionado}"
                elif escolha == "2":
                    valor_selecionado = input("Digite o valor da entrada de líquido: ")
                    mensagem_enviar = f"Q_i2 {valor_selecionado}"
                elif escolha == "3":
                    valor_selecionado = input("Digite o valor da entrada de líquido: ")
                    mensagem_enviar = f"Q_i3 {valor_selecionado}"
                elif escolha == "4":
                    mensagem_enviar = "Iniciar"
                elif escolha == "5":
                    mensagem_enviar = "Encerrar"
                elif escolha =="6":
                    break
    
                # Abre o arquivo no modo 'w' (write) para escrever
            
                arquivo.write(f"Enviado: {mensagem_enviar} \n")
    
                s.sendall(mensagem_enviar.encode())

    
                # arquivo.write(f"Recebido: {mensagem_recebida.decode()} \n")
""""
Read and actuate on the process via OPC server
"""
...

tcp_client_thread = threading.Thread(target=thread_TCP_IP_client)
tcp_client_thread.start() 