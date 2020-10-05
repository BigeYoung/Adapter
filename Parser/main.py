# -*- coding: UTF-8 -*-
from Parser import Parser

mypath = "/home/pi/aml2ua/model_generation/"
from os import listdir
from os.path import isfile, join
files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
print("Found AML file: ", files)
aml = mypath + files[0]

parser = Parser()
parser.parse(aml, "http://www.itdili.cn/UA/"+aml)
parser.export("opcua.xml")
parser.server.start()