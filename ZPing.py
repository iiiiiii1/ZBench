#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
 Author 雨落无声（Github: https://github.com/ylws-4617)
 Reference:
 1. https://www.s0nnet.com/archives/python-icmp
 2. http://www.pythoner.com/357.html
'''

import os 
import argparse 
import socket
import struct
import select
import json
import time

STYLE = {
    'fore': {
        'black': 30, 'red': 31, 'green': 32, 'yellow': 33,
        'blue': 34, 'purple': 35, 'cyan': 36, 'white': 37,
    },
    'back': {
        'black': 40, 'red': 41, 'green': 42, 'yellow': 43,
        'blue': 44, 'purple': 45, 'cyan': 46, 'white': 47,
    },
    'mode': {
        'bold': 1, 'underline': 4, 'blink': 5, 'invert': 7,
    },
    'default': {
        'end': 0,
    }
}


def use_style(string, mode='', fore='', back=''):
    mode = '%s' % STYLE['mode'][mode] if STYLE['mode'].has_key(mode) else ''
    fore = '%s' % STYLE['fore'][fore] if STYLE['fore'].has_key(fore) else ''
    back = '%s' % STYLE['back'][back] if STYLE['back'].has_key(back) else ''
    style = ';'.join([s for s in [mode, fore, back] if s])
    style = '\033[%sm' % style if style else ''
    end = '\033[%sm' % STYLE['default']['end'] if style else ''
    return '%s%s%s' % (style, string, end)

D = {
    'Zhengzhou': '61.168.23.74', 
    'Jinan': 'speedtest1.jnltwy.com', 
    'Tianjin': 'speedtest1.online.tj.cn', 
    'Changji': '61.128.107.242',
    'Lhasa': '221.13.70.244', 
    'Changchun': 'speedtest2.vicp.cc', 
    'Shenzhen': '119.147.52.35', 
    'Lanzhou': 'www.lanzhouunicom.com', 
    'Xining': '221.207.32.94', 
    'Hefei': '112.122.10.26',
    'Wuhan': '113.57.249.2', 
    'Xiangyang': 'www.xydxcs.com', 
    'Nanchang': 'speedtest2.wy.jxunicom.com', 
    'Chongqing': 'speedtest1.cqccn.com', 
    'Shanghai': 'speedtest2.sh.chinamobile.com',
    'Huhehaote': 'www.nmwanwang.com',
    'Urumqi': '4g.xj169.com', 
    'Hangzhou': '122.229.136.10',
    'Xi an': 'xatest.wo-xa.com', 
    'Ningbo': 'ltetest3.139site.com',
    'Taiyuan': 'speedtest.sxunicomjzjk.cn', 
    'Suzhou': '218.94.214.42', 
    'Changsha': 'speedtest01.hn165.com', 
    'Harbin': '221.212.238.106',
    'Beijing': 'st1.bjtelecom.net',
    'Chengdu': 'speed.westidc.com.cn', 
    'Shenyang': 'speedtest1.online.ln.cn',
    'Nanjing': '4gnanjing1.speedtest.jsinfo.net', 
    'Ningxia': '221.199.9.35',
    'Fuzhou': 'upload1.testspeed.kaopuyun.com'
    }

recordfile=open("/tmp/ping.txt","w")

ICMP_ECHO_REQUEST = 8
DEFAULT_TIMEOUT = 2
DEFAULT_COUNT = 3

class Pinger(object):
	""" Pings to a host -- the Pythonic way"""
	
	def __init__(self, target_host, count=DEFAULT_COUNT, timeout=DEFAULT_TIMEOUT):
		self.target_host = target_host
		self.count = count
		self.timeout = timeout
		self.delay_list=list()
		


	def do_checksum(self, source_string):
		"""  Verify the packet integritity """
		sum = 0
		max_count = (len(source_string)/2)*2
		count = 0
		while count < max_count:
			val = ord(source_string[count + 1])*256 + ord(source_string[count])
			sum = sum + val
			sum = sum & 0xffffffff 
			count = count + 2
	 
		if max_count<len(source_string):
			sum = sum + ord(source_string[len(source_string) - 1])
			sum = sum & 0xffffffff 
	 
		sum = (sum >> 16)  +  (sum & 0xffff)
		sum = sum + (sum >> 16)
		answer = ~sum
		answer = answer & 0xffff
		answer = answer >> 8 | (answer << 8 & 0xff00)
		return answer
 
	def receive_pong(self, sock, ID, timeout):
		"""
		Receive ping from the socket.
		"""
		time_remaining = timeout
		while True:
			start_time = time.time()
			readable = select.select([sock], [], [], time_remaining)
			time_spent = (time.time() - start_time)
			if readable[0] == []: # Timeout
				return
	 
			time_received = time.time()
			recv_packet, addr = sock.recvfrom(1024)
			icmp_header = recv_packet[20:28]
			type, code, checksum, packet_ID, sequence = struct.unpack(
				"bbHHh", icmp_header
			)
			if packet_ID == ID:
				bytes_In_double = struct.calcsize("d")
				time_sent = struct.unpack("d", recv_packet[28:28 + bytes_In_double])[0]
				return time_received - time_sent
	 
			time_remaining = time_remaining - time_spent
			if time_remaining <= 0:
				return
	 
	 
	def send_ping(self, sock,  ID):
		"""
		Send ping to the target host
		"""
		target_addr  =  socket.gethostbyname(self.target_host)
	 
		my_checksum = 0
	 
		# Create a dummy heder with a 0 checksum.
		header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
		bytes_In_double = struct.calcsize("d")
		data = (192 - bytes_In_double) * "Q"
		data = struct.pack("d", time.time()) + data
	 
		# Get the checksum on the data and the dummy header.
		my_checksum = self.do_checksum(header + data)
		header = struct.pack(
			"bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1
		)
		packet = header + data
		sock.sendto(packet, (target_addr, 1))
	 
	 
	def ping_once(self):
		"""
		Returns the delay (in seconds) or none on timeout.
		"""
		icmp = socket.getprotobyname("icmp")
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
		except socket.error, (errno, msg):
			if errno == 1:
				# Not superuser, so operation not permitted
				msg +=  "ICMP messages can only be sent from root user processes"
				raise socket.error(msg)
		except Exception, e:
			print "Exception: %s" %(e)
	
		my_ID = os.getpid() & 0xFFFF
	 
		self.send_ping(sock, my_ID)
		delay = self.receive_pong(sock, my_ID, self.timeout)
		sock.close()
		return delay
	 
	 
	def ping(self):
		"""
		Run the ping process
		"""
		for i in xrange(self.count):
			try:
				delay  =  self.ping_once()
			except socket.gaierror, e:
				return False
				break
	 
			if delay  ==  None:
				return False
			else:
				delay  =  delay * 1000
				self.delay_list.append(delay)
		return (sum(self.delay_list)/len(self.delay_list))


count = 1
string =list()
d=dict()

for x in D:
    host=D[x]
    pinger = Pinger(host)
    result = pinger.ping()
	
	
    if result == False:
        latency_str = use_style(str("Fail"), fore='red')
    elif float(result) <= 60:
        latency_str =use_style(str(round(result,2)) + " ms",fore='green')
    elif float(result) <= 130:
        latency_str = use_style(str(round(result,2))+" ms",fore='yellow')
    else:
        latency_str = use_style(str(round(result,2))+" ms", fore='red')

	d[x] = float(result)

    string.append((x,latency_str))
    if len(string) == 3:
        print("{0:12}: {1:20}{2:12}: {3:20}{4:12}: {5:20}".format(string[0][0],string[0][1],string[1][0],string[1][1],string[2][0],string[2][1]))
        string = list()


if len(string) == 2:
    print("{0:12}: {1:20}{2:12}: {3:20}".format(string[0][0],string[0][1],string[1][0],string[1][1]))

if len(string) == 1:
    print("{0:12}: {1:20}".format(string[0][0],string[0][1]))
print d
jsonstr = json.dumps(d)
recordfile.write(jsonstr)
recordfile.close()