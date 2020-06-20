# -*- coding: UTF-8 -*-
from Parser import Parser
from Consul import Consul

aml = "CPPS_5.aml.xml"
parser = Parser()
parser.parse(aml, "http://www.itdili.cn/UA/"+aml)
parser.export("opcua.xml")
consul = Consul(aml)
consul.dumpJson()
# parser.server.start()
