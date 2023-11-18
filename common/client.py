# -*- coding:utf-8 -*-
import socket

HOST = '101.200.35.253'  # 服务器的主机名或者 IP 地址
PORT = 8010        # 服务器使用的端口

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.send(b'Hellozjw')
    data = s.recv(1024)

print('Received', repr(data))
