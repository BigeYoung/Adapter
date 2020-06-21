# -*- coding: UTF-8 -*-
from Consul import Consul
aml = "/AML/CPPS_5.aml"
consul = Consul(aml)
consul.dumpJson()

import os
os.system("consul agent -config-dir=/consul.d -data-dir=/tmp/consul")

