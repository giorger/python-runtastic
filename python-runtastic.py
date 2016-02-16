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
    """
    Class containing all required configuration for URLs, Headers, Fields to be used
    Configuration is read by a file.
    Can be overridden and direct value to be assigned
    """

    def __init__(self, configuration_file):
        """
        Class constructor
        :param configuration_file: String. Denotes the filename from which to retrieve configuration
        :return: Instance of ConfigurationObject class
        """
        self.conf_file = ConfigParser.ConfigParser()
        self.conf_file.readfp(open(configuration_file))
        self.RUNTASTIC_URL = self.conf_file.get("runtastic", "runtasticUrl")
        self.RUNTASTIC_URL_USER = self.conf_file.get("runtastic", "userUrl")
        self.RUNTASTIC_URL_LOGIN = self.conf_file.get("runtastic", "loginUrl")
        self.RUNTASTIC_URL_LOGOUT = self.conf_file.get("runtastic", "logoutUrl")
        self.RUNTASTIC_URL_SPORT_SESSION = self.conf_file.get("runtastic", "sportSessionURL")
        self.RUNTASTIC_URL_SESSIONS_API = self.conf_file.get("runtastic", "sessionsApiUrl")
        self.RUNTASTIC_HDR_USERNAME = self.conf_file.get("runtastic", "header_username")
        self.RUNTASTIC_HDR_PASSWORD = self.conf_file.get("runtastic", "header_password")
        self.RUNTASTIC_HDR_TOKEN = self.conf_file.get("runtastic", "header_token")
        self.RUNTASTIC_HDR_UID = self.conf_file.get("runtastic", "header_user_id")
        self.RUNTASTIC_HDR_ITEMS = self.conf_file.get("runtastic", "header_items")
        self.RUNTASTIC_USR_USERNAME = self.conf_file.get("runtastic-user-settings", "userName")
        self.RUNTASTIC_USR_PASSWORD = self.conf_file.get("runtastic-user-settings", "userPassword")
        self.RUNTASTIC_FLD_USERNAME = self.conf_file.get("python-runtastic", "field_username")
        self.RUNTASTIC_FLD_UID = self.conf_file.get("python-runtastic", "field_userid")
        self.RUNTASTIC_FLD_TOKEN = self.conf_file.get("python-runtastic", "field_token")
        self.RUNTASTIC_FLD_SPORT_SESSIONS = self.conf_file.get("python-runtastic", "field_sport_sessions")


class HTTPConnectionToRuntastic:
    """
    Class handling connection over HTTP to Runtastic. Response retrieved in raw format is returned to the invoker
    """

    def __init__(self, configuration):
        """

        :param configuration: ConfigurationObject.
        :return:
        """
        self.config = configuration
        self.post_data = ""
        self.conn = httplib.HTTPSConnection(self.config.RUNTASTIC_URL)
        self.sportUrl = self.config.RUNTASTIC_URL_USER
        self.headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        self.username = ""
        self.userid = ""
        self.token = ""
        self.activities_list = ""
        self.url_picker = {
            self.config.RUNTASTIC_URL_LOGIN: self.connect_to_login_url,
            self.config.RUNTASTIC_URL_LOGOUT: self.connect_to_logout_url,
            self.config.RUNTASTIC_URL_SPORT_SESSION: self.connect_to_sport_session_url,
            self.config.RUNTASTIC_URL_SESSIONS_API: self.connect_to_sport_session_api
        }

    def connect_to_login_url(self):
        self.post_data = urllib.urlencode({self.config.RUNTASTIC_HDR_USERNAME: self.config.RUNTASTIC_USR_USERNAME,
                                           self.config.RUNTASTIC_HDR_PASSWORD: self.config.RUNTASTIC_USR_PASSWORD,
                                           self.config.RUNTASTIC_HDR_TOKEN: ""})
        self.conn.request("POST", self.config.RUNTASTIC_URL_LOGIN, self.post_data, self.headers)
        return self.conn.getresponse()

    def connect_to_logout_url(self):
        self.conn.request("GET", self.config.RUNTASTIC_URL_LOGOUT)
        return self.conn.getresponse()

    def connect_to_sport_session_url(self):
        self.sportUrl = self.sportUrl + self.username + self.config.RUNTASTIC_URL_SPORT_SESSION
        self.conn.request("GET", self.sportUrl)
        return self.conn.getresponse()

    def connect_to_sport_session_api(self):
        self.post_data = urllib.urlencode({self.config.RUNTASTIC_HDR_UID: self.userid,
                                           self.config.RUNTASTIC_HDR_TOKEN: self.token,
                                           self.config.RUNTASTIC_HDR_ITEMS: self.activities_list})
        self.conn.request("POST", self.config.RUNTASTIC_URL_SESSIONS_API, self.post_data, self.headers)
        return self.conn.getresponse()

    def submit_request(self, target_url, *args):
        """
        :param target_url: String
        :param args: Not required for login/logout,
                        username only for retrieving sport session ids,
                        username, user_id, token, activities_list for retrieving complete session information
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
    __sessions = {}

    def __init__(self):
        self.config = ConfigurationObject("python-runtastic.local")
        self.runtastic_connection = HTTPConnectionToRuntastic(self.config)
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
        return ",".join(str(self.keys[0]) for self.keys in self.tmp)

    def login(self, session_uuid):
        if session_uuid in Runtastic.__sessions:
            return session_uuid
        else:
            self.runtastic_response = self.runtastic_connection.submit_request(self.config.RUNTASTIC_URL_LOGIN)
            if self.runtastic_response.status == 200:
                self.runtastic_response_json = json.loads(self.runtastic_response.read())
                self.session_details = {
                    self.config.RUNTASTIC_FLD_USERNAME: self.runtastic_response_json['current_user']['slug'],
                    self.config.RUNTASTIC_FLD_UID: self.runtastic_response_json['current_user']['id'],
                    self.config.RUNTASTIC_FLD_TOKEN: self.parse_for_authenticity_token(self.runtastic_response_json)}
                self.tmp = str(uuid.uuid4())
                Runtastic.__sessions[self.tmp] = self.session_details
                return self.tmp
            else:
                print ("Error:" + self.runtastic_response.reason)
                return 0

    def logout(self, session_uuid):
        if session_uuid in Runtastic.__sessions:
            self.runtastic_response = self.runtastic_connection.submit_request(self.config.RUNTASTIC_URL_LOGOUT)
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
        if session_uuid in Runtastic.__sessions:
            self.runtastic_response = self.runtastic_connection.submit_request(self.config.RUNTASTIC_URL_SPORT_SESSION,
                                                                               (Runtastic.__sessions[session_uuid])
                                                                               [self.config.RUNTASTIC_FLD_USERNAME])
            if self.runtastic_response.status == 200:
                self.runtastic_response = \
                    self.runtastic_connection.submit_request(self.config.RUNTASTIC_URL_SESSIONS_API,
                                                             (Runtastic.__sessions[session_uuid])
                                                             [self.config.RUNTASTIC_FLD_USERNAME],
                                                             (Runtastic.__sessions[session_uuid])
                                                             [self.config.RUNTASTIC_FLD_UID],
                                                             (Runtastic.__sessions[session_uuid])
                                                             [self.config.RUNTASTIC_FLD_TOKEN],
                                                             self.parse_for_list_of_sessions(
                                                                 self.runtastic_response.read()))
                if self.runtastic_response.status == 200:
                    self.runtastic_response_json = json.loads(self.runtastic_response.read())
                    for self.session in self.runtastic_response_json:
                        self.all_sport_sessions[self.session['id']] = self.session
                        (Runtastic.__sessions[session_uuid])[self.config.RUNTASTIC_FLD_SPORT_SESSIONS] = \
                            self.all_sport_sessions
        else:
            print ("Error")


myConnection = Runtastic()
mySessionId = myConnection.login('')
myConnection.retrieve_all_sessions(mySessionId)
myConnection.logout(mySessionId)
