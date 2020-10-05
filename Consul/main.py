# -*- coding: UTF-8 -*-
from Consul import Consul

mypath = "/home/pi/aml2ua/model_generation/aml/"
from os import listdir
from os.path import isfile, join
files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
print("Found AML file: ", files)
aml = mypath + files[0]

consul = Consul(aml)
consul.regist()

