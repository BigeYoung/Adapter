# -*- coding: UTF-8 -*-
import sys
import json
import logging
import xml.etree.ElementTree as ET


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

    def dumpJson(self):
        with open("mobos.json", "w") as outfile:
            json.dump({"service": {
                "ID": self.GUID,
                "Name": self.Name,
                "Meta": {"Type": self.Type},
                "Port": 4844
            }}, outfile)


if __name__ == "__main__":
    consul = Consul("CPPS_5.aml")
    consul.dumpJson()
