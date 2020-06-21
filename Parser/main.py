# -*- coding: UTF-8 -*-
from Parser import Parser

aml = "/AML/CPPS_5.aml"
parser = Parser()
parser.parse(aml, "http://www.itdili.cn/UA/"+aml)
parser.export("opcua.xml")