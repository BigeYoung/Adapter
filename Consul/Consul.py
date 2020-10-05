# -*- coding: UTF-8 -*-
import sys
import json
import logging
import xml.etree.ElementTree as ET
import requests
import socket

SERVER_IP = '192.168.137.121'
SERVER_PORT = '30201'

class Consul:
    def __init__(self, aml_file):
        tree = ET.parse(aml_file)
        root = tree.getroot()
        assert root.tag == "CAEXFile"
        IE = root.find(
            "./*[@Name='AssetAdministrationShellInstanceHierarchy']/*[@Name='Resource']/InternalElement")
        self.GUID = IE.get('ID')
        ASS_Static = IE.find("./*[@Name='AAS']/*[@Name='Static']")
        self.Name = ASS_Static.find(
            "./*[@Name='Asset_Name']/*[@Name='value']/Value").text
        self.Type = ASS_Static.find(
            "./*[@Name='Asset_Type']/*[@Name='value']/Value").text

    def Regist(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((SERVER_IP, SERVER_PORT))
        MY_IP = s.getsockname()[0]
        s.close()

        url = 'http://'+SERVER_IP+':'+SERVER_PORT+'/v1/agent/service/register'
        payload = {
            "id": "uaserver-ababa",
            "name": "uaserver-ababa",
            "address": MY_IP,
            "port": 8080,
            "tags": [
                "uaserver"
            ],
            "checks": [
                {
                    "http": "http://"+MY_IP+":9020/health",
                    "interval": "5s"
                }
            ]
        }
        print(json.dumps(payload))
        headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
        r = requests.put(url, data=json.dumps(payload), headers=headers)
        print(r)
