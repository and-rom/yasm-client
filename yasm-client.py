#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import os
import re
import socket
import threading
import sys

class Sentry:
	config = configparser.ConfigParser()
	name = ""
	#iface = ""
	#port = 0
	params = []
	wtype = ""
        # инициализация, получение параметров из файла конфигурации
	def __init__ (self):
		self.config.read('config.ini')
		self.name = self.config['Global']['Name']
		#self.iface = self.config['Global']['Inretface']
		#self.port = self.config['Global']['Port']

		paramnames = tuple(self.config['Params'].keys())

		sections = []
		for paramname in paramnames:
			sections.append (self.config['Params'][paramname])

		attribs = ("Descr", "Type", "Exec", "Parse_func_type", "Parse_func_name", "Parse_exp")

		for section in sections:
			param = {}
			param['Name']=section
			for attrib in attribs:
				param[attrib]=self.config[section][attrib]
			self.params.append(param)
        # передача параметров соединения
	def connectionParams (self):
		return (self.iface, int(self.port))
        # опрос датчиков
	def inspect (self,wtype):
		self.wtype=wtype
		for param in self.params:
			if (self.wtype == param['Type'] or self.wtype == 'all'):
				rawoutput = self.execute(param['Exec'])
				output = self.parse(rawoutput,param['Parse_func_type'],param['Parse_func_name'],param['Parse_exp'])
				param['Value']=str(output)
#		print (self.params)
#		print ("inspect result :: " + str(output))
        # вызов внешней программы для получение значения датчика
	def execute (self,command):
		result = os.popen(command[1:len(command)-1]).read()
		return result
        # обработка результатов опроса датчиков
	def parse (self,rawoutput,functype,funcname,exp):
		if functype == 'int':
			options = {'lm-sensors' : self.lmsensors,
				   'bmcontrol' : self.bmcontrol,
				   'ping' : self.ping,
				   'onacpower' : self.onacpower,
				  }
			result = options[funcname](rawoutput, exp)
		elif functype == 'ext':
			print("External function")
		return result
        # обработка результатов опроса датчиков
	def lmsensors(self, rawoutput, exp):
		rg = re.compile(exp[1:len(exp)-1],re.IGNORECASE|re.DOTALL)
		m = rg.search(rawoutput)	
		if m:
			return m.group(1)
		else:
			return "err"
         # обработка результатов опроса датчиков
	def bmcontrol(self, rawoutput, exp):
		re1 = "(Device not plugged)|(Error GET_TEMPERATURE)"
		rg = re.compile(re1,re.IGNORECASE|re.DOTALL)
		m = rg.search(rawoutput)	
		if not m:
			return float(rawoutput)
		else:

			return "err"
         # обработка результатов опроса датчиков
	def ping(self, rawoutput, exp):
		rg = re.compile(exp[1:len(exp)-1],re.IGNORECASE|re.DOTALL)
		m = rg.search(rawoutput)	
		if m:
			return 1
		else:
			return "err"
         # обработка результатов опроса датчиков
	def onacpower(self, rawoutput, exp):
		if rawoutput=="0":
			return 1
		elif rawoutput=="1":
			return 0
		elif rawoutput=="255":
			return "err"
		else:
			return "err"
	def json (self):
		json =  "{\""+self.name + "\":{"
		m = len(self.params)
		for param in self.params:
			if (self.wtype == param['Type'] or self.wtype == 'all'):
				json = json + "\"" + param['Name'] + "\":{"
				json = json + "\"Descr\":" + "\"" + param['Descr'] + "\","
				json = json + "\"Value\":" + "\"" +  param['Value'] + "\","
				json = json + "\"Type\":" + "\"" +  param['Type'] + "\""
				json = json + "},"
		json = json[0:len(json)-1]
		json = json + "}}"
		return json

class Connect(threading.Thread):
	def __init__(self,sock,addr):
		self.sock = sock
		self.addr = addr
		self.m = Sentry()
		threading.Thread.__init__(self)
	def run (self):
		print ("Received connection from IP", self.addr[0])
		while True:
			data = self.sock.recv(1024)
			print (data)
			if not data:
				self.close()
			else:
				if (data==b'temp' or data==b'net' or data==b'power' or data==b'all'):
					self.m.inspect(data.decode())
					self.sock.send(self.m.json().encode())
				elif data==b'close':
					self.close()
				else:
					self.sock.send(b'err')
	def close (self):
		print ("Close")
		self.sock.send(b'close')
		#self.sock.close()

config = configparser.ConfigParser()
config.read('config.ini')
iface = config['Global']['Inretface']
port = int(config['Global']['Port'])


#o m = Sentry()

#o sock = socket.socket()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# TODO: добавить try except на отлов если адрес уже используется

#o sock.bind(m.connectionParams())
s.bind((iface, port))

#o sock.listen(1)
s.listen(5)
while True:
	sock, addr = s.accept()
	print ("Conn")
	Connect(sock, addr).start()
############o##############
#try:
#	closed=True
#	while True:
#		if closed:
#			conn, addr = sock.accept()
#		data = conn.recv(1024)
#		if not data:
#			conn.close()
#		else:
#			if (data==b'temp' or data==b'net' or data==b'power' or data==b'all'):
#				m.inspect(data.decode())
#				conn.send(m.json().encode())
#				closed=False
#			elif data==b'close':
#				conn.close()
#				closed=True
#			else:
#				conn.send(b'err')
#				closed=False
#except (KeyboardInterrupt, SystemExit):
#	try:
#		conn
#	except NameError:
#		exit()
#		print ("Con closed")
#	else:
#		conn.close()
#		print ("Con closed")
#		exit()



