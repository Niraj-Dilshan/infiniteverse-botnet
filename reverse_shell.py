import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("192.168.17.130",5555))


def shell():
	while True:
		command = sock.recv(1024)
		if command == 'quit':
			break
		else:
			massage = "Hello World"
			sock.sendall(massage.encode('utf-8'))


shell()

sock.close()

