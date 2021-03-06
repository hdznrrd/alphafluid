#!/usr/bin/python
#-*- coding: utf-8 -*-

import signal
import socket
import sys
import time
import urllib
import twitterfluid

tw = twitterfluid.twitterfluid()
running = True

def log(msg):
	f = open("fluid.log","a")
	f.write(time.asctime(time.localtime(time.time()+3600*1)))
	f.write(" ] " + msg + "\n")
	f.close()
	print msg

mapping = (1,2,3,4,26,27)

def handler(signum, frame):
	tw.setDisconnected()
	running = False
	print "Trying to stop!"

signal.signal(signal.SIGTERM, handler)
signal.signal(signal.SIGINT, handler)

def send_bought(st):
		urllib.urlopen("http://appserv.tutschonwieder.net:8080/apex/prod/sellProduct?apikey=382B6E63714B3275306D454B2F6544656D6A666A3974617A74386F3D&automat_id=1&schacht_id=" + str(mapping[int(st)]) + "&anzahl=1")

def send_empty(st):
		urllib.urlopen("http://appserv.tutschonwieder.net:8080/apex/prod/schachtLeer?apikey=382B6E63714B3275306D454B2F6544656D6A666A3974617A74386F3D&automat_id=1&schacht_id=" + str(mapping[int(st)]))

def lick_get_level(shaft):
	lines = urllib.urlopen("http://appserv.tutschonwieder.net:8080/apex/prod/getFuellstand?automat_id=1&schacht_id="+str(shaft)).readlines()
	for line in lines:
		print line
		#if line.startswith('{"\"tensai-prod\".lick_api.getfuellstand(/*in:automat_id*/:1,/*in:schacht_id*/:2)":'):
		if line.find("tensai-prod") >= 0 and line.find(".lick_api.getfuellstand(") >= 0 and line.find("in:automat_id"):
			rpart = line.split(":")[-1]
			#print rpart
			if(rpart[-1] == "}"):
				numonly = rpart[0:-1]
				print numonly
				num = int(numonly)
				if num < 0:
					num = 0
				return num


def mat_send_values(conn):
	log("sending values")
	
	for i in range(0,6):
		time.sleep(0.2)
		conn.send("/i/s/"+str(i)+" "+str(lick_get_level(mapping[i]))+"\r\n")


def mat_send_mention(conn):
	log("sending mentions")
	txt = tw.fetch_mention()
	conn.send("/i/t/" + txt + "\r\n")

def parse(line, conn):
	if not line.startswith("/o/"):
		line = ""
		return
	if line[3] == 'b':		#buy
		send_bought(line[5])
		log("Gekauft: " + line[5])
		tw.tweet_bought(int(line[5]), "")
		mat_send_values(conn)
	elif line[3] == 'o': 	#offline buys (no connection)
		send_bought(line[5])
		log("Offline log: " + line[5])

	elif line[3] == 'e':	#empty
		send_empty(line[5])
		log("Leer: " + line[5])
		tw.tweet_empty(int(line[5]))

	elif line[3] == 'i':	#login
		conn.send("/i/w/\r\n")
		log("welcomed client")
		mat_send_values(conn)
		mat_send_mention(conn)
	line = ""
	return



# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the address given on the command line
server_address = ('', 1337)
sock.bind(server_address)
print 'starting up on %s port %s' % sock.getsockname()
sock.listen(1)
while running:
	print 'waiting for a connection'
	connection, client_address = sock.accept()
	try:
		line = ""
		print 'client connected:', client_address
		log("CONNECT " + client_address[0])
		tw.setConnection(connection)
		while running:
			data = connection.recv(1)
			if data:
				line += data[0]
				
				if data[0] == '\n' or data[0] == '\r':
					if line[0] != 'd' and line[0] != '\n' and line[0] != '\r':
						print line
					parse(line,connection)
					line = ""
			else:
				tw.setDisconnected()
				print 'client disconnected:', client_address
				log("DISCONNECT " + client_address[0])
				break
	finally:
		connection.close()

