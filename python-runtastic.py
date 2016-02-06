import ConfigParser
import httplib
import json
import re
import urllib
import uuid
import xml.etree.ElementTree as ET


class ConfigurationObject:
    def __init__(self, configuration_file):
        self.conf_file = ConfigParser.ConfigParser()
        self.conf_file.readfp(open(configuration_file))

    def get_config_value(self, c_area, c_name):
        return self.conf_file.get(c_area, c_name)


class Runtastic:
    __config = 0
    __sessions = {}

    def __init__(self):
        Runtastic.__config = ConfigurationObject("python-runtastic.local")

    def login(self, session_uuid):
        if Runtastic.__sessions.has_key(session_uuid):
            return session_uuid
        else:
            self.values = {Runtastic.__config.get_config_value("runtastic",
                                                               "header_username"): Runtastic.__config.get_config_value(
                "runtastic-user-settings", "userName"),
                Runtastic.__config.get_config_value("runtastic",
                                                    "header_password"): Runtastic.__config.get_config_value(
                    "runtastic-user-settings", "userPassword"),
                Runtastic.__config.get_config_value("runtastic", "header_token"): ""
            }
            self.data = urllib.urlencode(self.values)
            self.conn = httplib.HTTPSConnection(Runtastic.__config.get_config_value("runtastic", "runtasticUrl"))
            self.headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            self.conn.request("POST", Runtastic.__config.get_config_value("runtastic", "loginUrl"), self.data,
                              self.headers)
            self.conn_response = self.conn.getresponse()
            if self.conn_response.status == 200:
                self.responseOutputJson = json.loads(self.conn_response.read())
                ##
                ## Retrieve Authenticity Token
                ##
                ### Problem in runtastic string output. Fix
                fixed_string = self.responseOutputJson['update'].replace("last_name}}}'>", "last_name}}}' />")
                ### end of fix
                self.responseOutputXml = ET.fromstring(fixed_string)
                self.tmp = self.responseOutputXml.findall(
                    "./*/*/*/*/*/*/*/*[@method='post']/*/input[@name='authenticity_token']")
                self.authenticity_token = self.tmp[0].get('value')
                ##
                self.sessionDetails = {Runtastic.__config.get_config_value("python-runtastic", "field_username"):
                                           self.responseOutputJson['current_user']['slug'],
                                       Runtastic.__config.get_config_value("python-runtastic", "field_userid"):
                                           self.responseOutputJson['current_user']['id'],
                                       Runtastic.__config.get_config_value("python-runtastic",
                                                                           "field_token"): self.authenticity_token}
                self.sessionid = str(uuid.uuid4())
                Runtastic.__sessions[self.sessionid] = self.sessionDetails
                print(str(self.responseOutputJson['current_user']['id']) + " " + str(self.authenticity_token))
                return self.sessionid
            else:
                print ("Error:" + self.conn_response.reason)
                return 0

    def logout(self, session_uuid):
        if Runtastic.__sessions.has_key(session_uuid):
            self.conn = httplib.HTTPSConnection(Runtastic.__config.get_config_value("runtastic", "runtasticUrl"))
            self.conn.request("GET", Runtastic.__config.get_config_value("runtastic", "logoutUrl"))
            print (Runtastic.__config.get_config_value("runtastic", "logoutUrl"))
            self.conn_response = self.conn.getresponse()
            if self.conn_response.status == 200 or self.conn_response.status == 302:
                del Runtastic.__sessions[session_uuid]
                print "Signed out"
                return True
            else:
                print (str(self.conn_response.status) + "   " + str(self.conn_response.reason) + str(
                    self.conn_response.getheader("Location")))
                return False
        else:
            return True

    def retrieve_all_sessions(self, session_uuid):
        if Runtastic.__sessions.has_key(session_uuid):
            self.sportUrl = Runtastic.__config.get_config_value("runtastic", "userUrl") + \
                            (Runtastic.__sessions[session_uuid])[Runtastic.__config.get_config_value("python-runtastic",
                                                                                                     "field_username")] + Runtastic.__config.get_config_value(
                "runtastic", "sportSessionURL")
            self.conn = httplib.HTTPSConnection(Runtastic.__config.get_config_value("runtastic", "runtasticUrl"))
            self.headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            self.conn.request("GET", self.sportUrl, self.data, self.headers)
            self.conn_response = self.conn.getresponse()
            if self.conn_response.status == 200:
                self.dataa = re.search("var index_data = (.*)\;", self.conn_response.read()).group()
                self.datab = re.search("\[\[.*\]\]", self.dataa).group()
                print (self.datab)
                self.session_data_json = json.loads(self.datab)
                self.listsess = ",".join(str(self.keyss[0]) for self.keyss in self.session_data_json)
                print self.listsess
                self.values = {Runtastic.__config.get_config_value("runtastic",
                                                                   "header_user_id"):
                                   (Runtastic.__sessions[session_uuid])[
                                       Runtastic.__config.get_config_value("python-runtastic", "field_userid")],
                               Runtastic.__config.get_config_value("runtastic", "header_token"):
                                   (Runtastic.__sessions[session_uuid])[
                                       Runtastic.__config.get_config_value("python-runtastic", "field_token")],
                               Runtastic.__config.get_config_value("runtastic", "header_items"): self.listsess
                               }
                self.data2 = urllib.urlencode(self.values)
                self.conn2 = httplib.HTTPSConnection(Runtastic.__config.get_config_value("runtastic", "runtasticUrl"))
                self.headers2 = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
                self.conn2.request("POST", Runtastic.__config.get_config_value("runtastic", "sessionsApiUrl"),
                                   self.data2, self.headers2)
                self.conn2_response = self.conn2.getresponse()
                if self.conn2_response.status == 200:
                    self.responseOutputJson2 = json.loads(self.conn2_response.read())
                    print (self.responseOutputJson2)
        else:
            print ("Error")


myConnection = Runtastic()
mySessionId = myConnection.login('')
print mySessionId
myConnection.retrieve_all_sessions(mySessionId)
# myConnection.logout(mySessionId)
