import socket
import numpy as np
import threading

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

def thread_TCP_IP_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        loop_comunicacao = True
        
        with open("historiador.txt", "w", buffering=1) as arquivo:
        
            while loop_comunicacao:
                mensagem_enviar = ''
    
                print("\nDigite a variável que você deseja controlar:")
                print("1. Entrada de Líquido Tanque 1")
                print("2. Entrada de Líquido Tanque 2")
                print("3. Entrada de Líquido Tanque 3")
                print("4. Entrada de Líquido Tanque de água quente")
                print("5. Entrada de Líquido Tanque de água fria")
                print("6. Iniciar Controle Automático")
                print("7. Encerrar Controle Automático")
                print("8. Encerrar conexão")
    
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
                    valor_selecionado = input("Digite o valor da entrada de líquido: ")
                    mensagem_enviar = f"Q_hot {valor_selecionado}"
                elif escolha == "5":
                    valor_selecionado = input("Digite o valor da entrada de líquido: ")
                    mensagem_enviar = f"Q_cold {valor_selecionado}"
                elif escolha == "6":
                    mensagem_enviar = "Iniciar"
                elif escolha == "7":
                    mensagem_enviar = "Encerrar"
                elif escolha == "8":
                    mensagem_enviar = "Quit"
                    loop_comunicacao = False
    
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