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
import json
import re
import urllib
import uuid
import xml.etree.ElementTree

import requests


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
        self.RUNTASTIC_HDR_COOKIE = "cookies"
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
        :return HTTPConnectionToRuntastic class object
        """
        self.config = configuration
        self.post_data = ""
        self.conn = ""
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
        """
        Connects to runtastic and performs authentication. Returns raw response from the authentication
        :return: HTTPResponse
        """
        self.post_data = urllib.urlencode({self.config.RUNTASTIC_HDR_USERNAME: self.config.RUNTASTIC_USR_USERNAME,
                                           self.config.RUNTASTIC_HDR_PASSWORD: self.config.RUNTASTIC_USR_PASSWORD,
                                           self.config.RUNTASTIC_HDR_TOKEN: ""})
        self.conn = requests.post(self.config.RUNTASTIC_URL + self.config.RUNTASTIC_URL_LOGIN, self.post_data,
                                  headers=self.headers)
        return self.conn

    def connect_to_logout_url(self):
        """
        Performs logout from runtastic
        :return: HTTPResponse
        """
        self.conn = requests.get(self.config.RUNTASTIC_URL + self.config.RUNTASTIC_URL_LOGOUT)
        return self.conn

    def connect_to_sport_session_url(self):
        """
        Performs connection to the sports url to retrieve session ids
        :return: HTTPResponse
        """
        self.sportUrl = self.sportUrl + self.username + self.config.RUNTASTIC_URL_SPORT_SESSION
        self.conn = requests.get(self.config.RUNTASTIC_URL + self.sportUrl, headers=self.headers,
                                 cookies=self.hdr_cookies)
        return self.conn

    def connect_to_sport_session_api(self):
        """
        Performs connection to the sports API to retrieve details for each session
        :return: HTTPResponse
        """
        self.post_data = urllib.urlencode({self.config.RUNTASTIC_HDR_UID: self.userid,
                                           self.config.RUNTASTIC_HDR_TOKEN: self.token,
                                           self.config.RUNTASTIC_HDR_ITEMS: self.activities_list})
        self.conn = requests.post(self.config.RUNTASTIC_URL + self.config.RUNTASTIC_URL_SESSIONS_API, self.post_data,
                                  headers=self.headers, cookies=self.hdr_cookies)
        return self.conn

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
        if args.__len__() == 2:
            self.hdr_cookies = args[1]
        else:
            if args.__len__() > 1:
                self.userid = args[1]
                self.token = args[2]
                self.activities_list = args[3]
        target_url_function = self.url_picker.get(target_url)
        return target_url_function()


class Runtastic:
    """
    Class containing all logic.
    __sessions is a dictionary maintaining all available sessions
    """
    __sessions = {}

    def __init__(self):
        """
        Initialization
        :return: Runtastic class object
        """
        self.config = ConfigurationObject("python-runtastic.local")
        self.runtastic_connection = HTTPConnectionToRuntastic(self.config)
        self.runtastic_response = ""
        self.runtastic_response_json = ""
        self.runtastic_response_xml = ""
        self.session_details = ""
        self.tmp = ""
        self.all_sport_sessions = {}

    def parse_for_authenticity_token(self, json_message):
        """
        :param json_message: the HTTPResponse message in JSON format to parse
        :return: String which is the token value
        """
        self.runtastic_response_xml = xml.etree.ElementTree.fromstring(json_message['update'].
                                                                       replace("last_name}}}'>", "last_name}}}' />"))
        return (self.runtastic_response_xml.findall(
            "./*/*/*/*/*/*/*/*[@method='post']/*/input[@name='authenticity_token']"))[0].get('value')

    def parse_for_list_of_sessions(self, raw_message):
        """

        :param raw_message: HTTPResponse in String format
        :return: the list of session ids concatenated with ',' (ie 1234,12345,565656,etc...)
        """
        self.tmp = re.search("var index_data = (.*);", raw_message).group()
        self.tmp = re.search("\[\[.*\]\]", self.tmp).group()
        self.tmp = json.loads(self.tmp)
        return ",".join(str(self.keys[0]) for self.keys in self.tmp)

    def login(self, session_uuid):
        """

        :param session_uuid: UUID defining uniquely the session
        :return: String, denoting the session id of the the logged session
        """
        if session_uuid in Runtastic.__sessions:
            return session_uuid
        else:
            self.runtastic_response = self.runtastic_connection.submit_request(self.config.RUNTASTIC_URL_LOGIN)
            if self.runtastic_response.status_code == 200:
                self.runtastic_response_json = self.runtastic_response.json()
                self.session_details = {
                    self.config.RUNTASTIC_FLD_USERNAME: self.runtastic_response_json['current_user']['slug'],
                    self.config.RUNTASTIC_FLD_UID: self.runtastic_response_json['current_user']['id'],
                    self.config.RUNTASTIC_FLD_TOKEN: self.parse_for_authenticity_token(self.runtastic_response_json),
                    self.config.RUNTASTIC_HDR_COOKIE: dict(self.runtastic_response.cookies)}
                self.tmp = str(uuid.uuid4())
                Runtastic.__sessions[self.tmp] = self.session_details
                return self.tmp
            else:
                print ("Error:" + self.runtastic_response.reason)
                return 0

    def logout(self, session_uuid):
        """

        :param session_uuid: String denoting which session to disconnect
        :return: Boolean
        """
        if session_uuid in Runtastic.__sessions:
            self.runtastic_response = self.runtastic_connection.submit_request(self.config.RUNTASTIC_URL_LOGOUT)
            if self.runtastic_response.status_code == 200 or self.runtastic_response.status_code == 302:
                del Runtastic.__sessions[session_uuid]
                print "Signed out"
                return True
            else:
                print (str(self.runtastic_response.status_code) + "   " + str(self.runtastic_response.reason) + str(
                    self.runtastic_response.getheader("Location")))
                return False
        else:
            return True

    def retrieve_all_sessions(self, session_uuid):
        """

        :param session_uuid: String denoting which session to look for recorded runtastic sessions
        :return:
        """
        if session_uuid in Runtastic.__sessions:
            self.runtastic_response = self.runtastic_connection.submit_request(self.config.RUNTASTIC_URL_SPORT_SESSION,
                                                                               (Runtastic.__sessions[session_uuid])
                                                                               [self.config.RUNTASTIC_FLD_USERNAME],
                                                                               (Runtastic.__sessions[session_uuid])
                                                                               [self.config.RUNTASTIC_HDR_COOKIE])
            if self.runtastic_response.status_code == 200:
                self.runtastic_response = \
                    self.runtastic_connection.submit_request(self.config.RUNTASTIC_URL_SESSIONS_API,
                                                             (Runtastic.__sessions[session_uuid])
                                                             [self.config.RUNTASTIC_FLD_USERNAME],
                                                             (Runtastic.__sessions[session_uuid])
                                                             [self.config.RUNTASTIC_FLD_UID],
                                                             (Runtastic.__sessions[session_uuid])
                                                             [self.config.RUNTASTIC_FLD_TOKEN],
                                                             self.parse_for_list_of_sessions(
                                                                 self.runtastic_response.text))
                if self.runtastic_response.status_code == 200:
                    self.runtastic_response_json = self.runtastic_response.json()
                    for self.session in self.runtastic_response_json:
                        self.all_sport_sessions[self.session['id']] = self.session
                        (Runtastic.__sessions[session_uuid])[self.config.RUNTASTIC_FLD_SPORT_SESSIONS] = \
                            self.all_sport_sessions
                    return (Runtastic.__sessions[session_uuid])[self.config.RUNTASTIC_FLD_SPORT_SESSIONS]
        else:
            print ("Error")
            return 0

    def numberOfSessions(self, session_uid):
        if session_uid in Runtastic.__sessions:
            print "Number of sessions: " + str(
                len(Runtastic.__sessions[session_uid][self.config.RUNTASTIC_FLD_SPORT_SESSIONS]))

myConnection = Runtastic()
mySessionId = myConnection.login('')
myConnection.retrieve_all_sessions(mySessionId)
myConnection.numberOfSessions(mySessionId)
myConnection.logout(mySessionId)
