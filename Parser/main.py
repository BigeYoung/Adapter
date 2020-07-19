# -*- coding: UTF-8 -*-
import os
from Parser import Parser
from os import listdir
from os.path import isfile, join

print("Parser Started.")

amlpath = "/volume/AML/"
files = [f for f in listdir(amlpath) if isfile(join(amlpath, f))]
print("Found AML file: ", files)
aml = amlpath + files[0]

md5sum = os.popen("md5sum "+aml).read().split()[0]
print("AML MD5", md5sum)

xmlpath = "/volume/XML/"
files = [f for f in listdir(xmlpath) if isfile(join(xmlpath, f))]
print("Found XML file: ", files)
found_xml = False
for file_name in files:
    if file_name == md5sum+".xml":
        found_xml = file_name
        break

parser = Parser()
if found_xml:
    print("XML Matched.")
    parser.import_xml(xmlpath+file_name)
else:
    print("XML Unmatched.")
    parser.parse(aml, "http://www.itdili.cn/UA/"+aml)
    parser.export(xmlpath+file_name)

print("OPC UA Server started")
parser.server.start()
