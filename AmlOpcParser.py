# -*- coding: UTF-8 -*-
from Parser import Parser

aml = "cpps@scut-example-0819.aml"
parser = Parser()
parser.parse(aml, "http://www.itdili.cn/UA/"+aml)
parser.export("a.xml")
parser.server.start()
