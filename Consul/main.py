# -*- coding: UTF-8 -*-
from Consul import Consul

mypath = "/AML/"
from os import listdir
from os.path import isfile, join
files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
print("Found AML file: ", files)
aml = mypath + files[0]

consul = Consul(aml)
consul.dumpJson()

import os
os.system("consul agent -config-dir=/consul.d -data-dir=/tmp/consul")

