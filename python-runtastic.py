import sys
import ConfigParser
import urllib2
import urllib
import io
import httplib
import os
import json
import xml.etree.ElementTree as ET
import uuid

class ConfigurationObject:
	def __init__(self, configuration_file):
		self.conf_file=ConfigParser.ConfigParser()
		self.conf_file.readfp(open(configuration_file))

	def getValue(self, varArea, varName):
		return self.conf_file.get(varArea,varName)


class Runtastic:
	__config=0
	__sessions={}
	
	def __init__(self):
		Runtastic.__config=ConfigurationObject("python-runtastic.ini")
		
	def login(self):
		self.values = { Runtastic.__config.getValue("runtastic","header_username"): Runtastic.__config.getValue("runtastic-user-settings","userName"),
				Runtastic.__config.getValue("runtastic","header_password"): Runtastic.__config.getValue("runtastic-user-settings","userPassword"),
				Runtastic.__config.getValue("runtastic","header_token"): "" 
				}
		self.data=urllib.urlencode(self.values)
		self.conn=httplib.HTTPSConnection(Runtastic.__config.getValue("runtastic","runtasticUrl"))
		self.headers={"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
		self.conn.request("POST",Runtastic.__config.getValue("runtastic","loginUrl"),self.data,self.headers)
		self.conn_response=self.conn.getresponse()
		if self.conn_response.status == 200:
			self.responseOutputJson = json.loads(self.conn_response.read())
			##
			## Retrieve Authenticity Token
			##
			### Problem in runtastic string output. Fix
			fixed_string=self.responseOutputJson['update'].replace("last_name}}}'>","last_name}}}' />")
			### end of fix
			self.responseOutputXml= ET.fromstring(fixed_string)
			self.tmp=self.responseOutputXml.findall("./*/*/*/*/*/*/*/*[@method='post']/*/input[@name='authenticity_token']")
			self.authenticity_token=self.tmp[0].get('value')
			##
			self.sessionDetails={"username": self.responseOutputJson['current_user']['slug'], "userid": self.responseOutputJson['current_user']['id'], "authenticityToken": self.authenticity_token}
			self.sessionid=str(uuid.uuid4())
			Runtastic.__sessions[self.sessionid]=self.sessionDetails
			return self.sessionid
		else:
			print ("Error:" + self.conn_response.reason)
			return 0
			
			
myConnection=Runtastic()
mySessionId=myConnection.login()
print mySessionId

		