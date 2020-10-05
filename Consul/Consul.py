# -*- coding: UTF-8 -*-
import sys
import json
import logging
import xml.etree.ElementTree as ET
import requests
import socket

SERVER_IP = '192.168.137.121'
SERVER_PORT = 30301

class Consul:
    def __init__(self, aml_file):
        tree = ET.parse(aml_file)
        root = tree.getroot()
        assert root.tag == "CAEXFile"
        IE = root.find(
            "./*[@Name='AssetAdministrationShellInstanceHierarchy']/InternalElement")
        self.GUID = IE.get('ID')
        AAS_Static = IE.find("./*[@Name='AAS']/*[@Name='Static']")
        self.Name = AAS_Static.find(
            "./*[@Name='Asset_Name']/*[@Name='value']/Value").text
        self.Type = AAS_Static.find(
            "./*[@Name='Asset_Type']/*[@Name='value']/Value").text

    def Regist(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((SERVER_IP, SERVER_PORT))
        MY_IP = s.getsockname()[0]
        s.close()

        url = 'http://'+SERVER_IP+':'+str(SERVER_PORT)+'/v1/agent/service/register'
        payload = {
            "id": "uaserver-"+self.GUID,
            "name": "uaserver-"+self.Name,
            "address": MY_IP,
            "port": 4844,
            "tags": [
                "uaserver",
                self.Type
            ]
        }
        print(json.dumps(payload))
        print(url)
        headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
        r = requests.put(url, data=json.dumps(payload), headers=headers)
        print(r)
