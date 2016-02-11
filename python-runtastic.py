"""
The MIT License (MIT)

Copyright (c) 2016 giorger

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import ConfigParser
import httplib
import json
import re
import urllib
import uuid
import xml.etree.ElementTree


class ConfigurationObject:
    def __init__(self, configuration_file):
        self.conf_file = ConfigParser.ConfigParser()
        self.conf_file.readfp(open(configuration_file))

    def get_config_value(self, c_area, c_name):
        return self.conf_file.get(c_area, c_name)


class HTTPConnectionToRuntastic:
    def __init__(self, configuration_file):
        self.config = configuration_file
        self.post_data = ""
        self.conn = httplib.HTTPSConnection(self.config.get_config_value("runtastic", "runtasticUrl"))
        self.sportUrl = self.config.get_config_value("runtastic", "userUrl")
        self.headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        self.username = ""
        self.userid = ""
        self.token = ""
        self.activities_list = ""
        self.url_picker = {
            self.config.get_config_value("runtastic", "loginUrl"): self.connect_to_login_url,
            self.config.get_config_value("runtastic", "logoutUrl"): self.connect_to_logout_url,
            self.config.get_config_value("runtastic", "sportSessionURL"): self.connect_to_sport_session_url,
            self.config.get_config_value("runtastic", "sessionsApiUrl"): self.connect_to_sport_session_api
        }

    def connect_to_login_url(self):
        self.post_data = urllib.urlencode(
            {self.config.get_config_value("runtastic", "header_username"):
                 self.config.get_config_value("runtastic-user-settings", "userName"),
             self.config.get_config_value("runtastic", "header_password"):
                 self.config.get_config_value("runtastic-user-settings", "userPassword"),
             self.config.get_config_value("runtastic", "header_token"): ""})
        self.conn.request("POST", self.config.get_config_value("runtastic", "loginUrl"), self.post_data, self.headers)
        return self.conn.getresponse()

    def connect_to_logout_url(self):
        self.conn.request("GET", self.config.get_config_value("runtastic", "logoutUrl"))
        return self.conn.getresponse()

    def connect_to_sport_session_url(self):
        self.sportUrl = self.sportUrl + self.username + self.config.get_config_value("runtastic", "sportSessionURL")
        self.conn.request("GET", self.sportUrl)
        return self.conn.getresponse()

    def connect_to_sport_session_api(self):
        self.post_data = urllib.urlencode({self.config.get_config_value("runtastic", "header_user_id"): self.userid,
                                           self.config.get_config_value("runtastic", "header_token"): self.token,
                                           self.config.get_config_value("runtastic",
                                                                        "header_items"): self.activities_list})
        self.conn.request("POST", self.config.get_config_value("runtastic", "sessionsApiUrl"), self.post_data,
                          self.headers)
        return self.conn.getresponse()

    def submit_request(self, target_url, *args):
        """
        :param target_url: String
        :rtype: HTTPSConnectionResponse
        """
        if args.__len__() > 0:
            self.username = args[0]
        if args.__len__() > 1:
            self.userid = args[1]
            self.token = args[2]
            self.activities_list = args[3]
        target_url_function = self.url_picker.get(target_url)
        return target_url_function()


class Runtastic:
    __config = 0
    __sessions = {}

    def __init__(self):
        Runtastic.__config = ConfigurationObject("python-runtastic.ini")
        self.runtastic_connection = HTTPConnectionToRuntastic(Runtastic.__config)
        self.runtastic_response = ""
        self.runtastic_response_json = ""
        self.runtastic_response_xml = ""
        self.session_details = ""
        self.tmp = ""
        self.all_sport_sessions = {}

    def parse_for_authenticity_token(self, json_message):
        self.runtastic_response_xml = xml.etree.ElementTree.fromstring(json_message['update'].
                                                                       replace("last_name}}}'>", "last_name}}}' />"))
        return (self.runtastic_response_xml.findall(
            "./*/*/*/*/*/*/*/*[@method='post']/*/input[@name='authenticity_token']"))[0].get('value')

    def parse_for_list_of_sessions(self, raw_message):
        self.tmp = re.search("var index_data = (.*);", raw_message).group()
        self.tmp = re.search("\[\[.*\]\]", self.tmp).group()
        self.tmp = json.loads(self.tmp)
        return ",".join(str(self.keyss[0]) for self.keyss in self.tmp)

    def login(self, session_uuid):
        if session_uuid in Runtastic.__sessions:
            return session_uuid
        else:
            self.runtastic_response = self.runtastic_connection.submit_request(Runtastic.__config.get_config_value(
                "runtastic", "loginUrl"))
            if self.runtastic_response.status == 200:
                self.runtastic_response_json = json.loads(self.runtastic_response.read())
                self.session_details = {Runtastic.__config.get_config_value("python-runtastic", "field_username"):
                                            self.runtastic_response_json['current_user']['slug'],
                                        Runtastic.__config.get_config_value("python-runtastic", "field_userid"):
                                            self.runtastic_response_json['current_user']['id'],
                                        Runtastic.__config.get_config_value("python-runtastic", "field_token"):
                                            self.parse_for_authenticity_token(self.runtastic_response_json)}
                self.tmp = str(uuid.uuid4())
                Runtastic.__sessions[self.tmp] = self.session_details
                return self.tmp
            else:
                print ("Error:" + self.runtastic_response.reason)
                return 0

    def logout(self, session_uuid):
        if Runtastic.__sessions.has_key(session_uuid):
            self.runtastic_response = self.runtastic_connection.submit_request(Runtastic.__config.get_config_value(
                "runtastic", "logoutUrl"))
            if self.runtastic_response.status == 200 or self.runtastic_response.status == 302:
                del Runtastic.__sessions[session_uuid]
                print "Signed out"
                return True
            else:
                print (str(self.runtastic_response.status) + "   " + str(self.runtastic_response.reason) + str(
                    self.runtastic_response.getheader("Location")))
                return False
        else:
            return True

    def retrieve_all_sessions(self, session_uuid):
        if Runtastic.__sessions.has_key(session_uuid):
            self.runtastic_response = self.runtastic_connection.submit_request(Runtastic.__config.get_config_value(
                "runtastic", "sportSessionURL"),
                (Runtastic.__sessions[session_uuid])[Runtastic.__config.get_config_value(
                    "python-runtastic", "field_username")])
            if self.runtastic_response.status == 200:
                self.runtastic_response = self.runtastic_connection.submit_request(Runtastic.__config.get_config_value(
                    "runtastic", "sessionsApiUrl"),
                    (Runtastic.__sessions[session_uuid])[Runtastic.__config.get_config_value(
                        "python-runtastic", "field_username")],
                    (Runtastic.__sessions[session_uuid])[Runtastic.__config.get_config_value("python-runtastic",
                                                                                             "field_userid")],
                    (Runtastic.__sessions[session_uuid])[Runtastic.__config.get_config_value("python-runtastic",
                                                                                             "field_token")],
                    self.parse_for_list_of_sessions(self.runtastic_response.read()))
                if self.runtastic_response.status == 200:
                    self.runtastic_response_json = json.loads(self.runtastic_response.read())
                    for self.session in self.runtastic_response_json:
                        self.all_sport_sessions[self.session['id']] = self.session
                    (Runtastic.__sessions[session_uuid])[Runtastic.__config.get_config_value("python-runtastic",
                                                                                             "field_sport_sessions")] \
                        = self.all_sport_sessions
        else:
            print ("Error")


myConnection = Runtastic()
mySessionId = myConnection.login('')
myConnection.retrieve_all_sessions(mySessionId)
myConnection.logout(mySessionId)
