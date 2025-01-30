# Controle de tanques dinâmicos com sistemas distribuídos

**Alunas:** <br>
Júlia Tarchi Maia de Souza <br>
Lais Isabelle Alves dos Santos

Este projeto foi desenvolvido como trabalho final da disciplina de Sistemas Distribuídos do curso de Engenharia de Controle e Automação. Ele consiste em desenvolver um sistema que, primeiramente, controle a dinâmica de três tanques.

Comece por instalar os pacotes necessários do projeto:
```python
pip install -r requirements.txt
```

Para configuração do servidor OPC UA [Prosys](https://prosysopc.com/products/opc-ua-simulation-server/), a imagem a seguir esclarece os objetos criados, com o exemplo da variável altura do tanque 1.
![image](https://github.com/user-attachments/assets/75c5dcd1-069e-47c9-9b58-bf453551fe82)


Para executar a rótina, primeiro inicialize o servidor TCP/IP para receber conexões com o cliente e também estabelecer conexão com o servidor OPC UA configurado anteriormente.
```python
python CLP.py
```

Em um terminal diferente, estabela a comunicação com o cliente TCP/IP. O programa se inicial com controle manual dos tanques, mas ao selecionar 6, é possível trocar para controle automático. <br>
ATENÇÃO: Uma vez que as equações diferenciais necessitam de uma altura positiva, dependendo do nível dos tanques ao chamar a rotina automática, pode ser que a dinâmica não funcione. 
```python
python client_tcpip.py
```

Em um terceiro terminal, chave a rotina que faz os cálculos da dinâmica dos tanques
```python
python control_tanks.py
```
