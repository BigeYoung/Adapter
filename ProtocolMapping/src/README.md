## 协议映射模块
> SET(string protocol, string config, string value);
> GET(string protocol, string config);
> 记得要输出日志（超时不输出）

<br />

### Modbus-RTU:
**先自动建立Modbus-RTU连接([COM,Parity,Baudrate,DataBit,StopBit,SlaveId])**
> SET("Modbus-RTU",[RegisterAddr],Value);
> GET("Modbus-RTU",[RegisterAddr]);

<br />
### TCP:
> SET("TCP",[Ip:Port],Value);
> GET("TCP",[Ip:Port])

<br />
### GPIO:
> SET("GPIO",[PinIndex],Value);
> GET("GPIO",[PinIndex]);

<br />
### RFID(RS232):
**先自动建立RFID连接**
> SET("RFID",[NULL],Value);
> GET("RFID",[NULL]);
