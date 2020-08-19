//General
#include <stdio.h>
#include <memory>
#include <string>
#include <sstream>
#include <map>
#include <time.h>

//Modbus-RTU
#include <stdint.h>
#include "modbus.h"

//TCP
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <unistd.h>
#define MAX_BUFFER 768

//GPIO
#include "wiringPi.h"

//RFID(Serial port)
#include <stdlib.h>
#include <termios.h>

//gRPC
#include <grpcpp/grpcpp.h>
#include <grpcpp/health_check_service_interface.h>
#include <grpcpp/ext/proto_server_reflection_plugin.h>
#include "mapping.grpc.pb.h"

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;
// using mapping::Mapping;
// using mapping::Reply;
// using mapping::Request;

std::map<std::string, int> protocol_map = {
  {"Modbus-RTU", 1},
  {"TCP", 2},
  {"GPIO", 3},
  {"RFID", 4}
};

union order_crc
{
  unsigned int data;
  unsigned char buffer[2];
};


class MappingServiceImpl final : public Mapping::Service
{
  public:
  //Modbus-RTU:
  uint8_t tab_discrete[1];  //For "Coils" and "Discrete Inputs"
  uint16_t tab_register[1]; //For "Input Registers" and "Holding Registers"
  modbus_t *modbusContext = nullptr;

  //TCP:
  char tcp_buf[MAX_BUFFER];
  bool Init_Tcp(const std::string addr_port, int &cli_socket);

  //GPIO:
  int wiringPi_stat = 0; // 0:Completed, -1:Failed

  //RFID:
  int rfid_serial = -1; //-1:Failed, Others:Completed
  unsigned char hex[36] = {0};
  void str_hex(const std::string &str, unsigned char *hex);
  std::string hex_str(unsigned char *hex);
  void CRC16(unsigned char data[], int cnt, unsigned char *crc16);
  bool write_rfid(unsigned char *sourcedata);
  bool read_rfid(unsigned char *finaldata);

  MappingServiceImpl();
  ~MappingServiceImpl();

  Status SET(ServerContext *context, const Request *request,
             Reply *reply) override
  {
    //函数原型 SET(string protocol, string config, string value) -> string status;

    switch (protocol_map[request->protocol()])
    {
    case 1: //"Modbus-RTU"
    {
      //For convenience, define the following PLC address (*Different from protocol address*)
      //00000-09999 Coils
      //10000-19999 Discrete Inputs
      //30000-39999 Input Registers
      //40000-49999 Holding Registers

      std::string register_addr = request->config();
      if (register_addr.at(0) == '0')
      {
        if (modbusContext && modbus_write_bit(modbusContext, std::stoi(register_addr.substr(1)), std::stoi(request->value())) != -1)
        {
          return Status::OK;
        }
      }
      else if (register_addr.at(0) == '4')
      {
        if (modbusContext && modbus_write_register(modbusContext, std::stoi(register_addr.substr(1)), std::stoi(request->value())) != -1)
        {
          return Status::OK;
        }
      }
      return Status::CANCELLED;
    }
    break;
    case 2: //"TCP"
    {
      //Required format:
      //xxx.xxx.xxx.xxx:xxxx
      int cli_socket = 0;
      if (!Init_Tcp(request->config(), cli_socket))
        return Status::CANCELLED;

      memset(tcp_buf, 0, sizeof(tcp_buf));
      strcpy(tcp_buf, request->value().c_str());
      int stat = send(cli_socket, tcp_buf, strlen(tcp_buf), 0);
      close(cli_socket);

      if (stat < 0)
      {
        printf("[Error] Failed to send message in TCP. \n");
        return Status::CANCELLED;
      }
      else
      {
        printf("[Info] Message sent in TCP. \n");
        return Status::OK;
      }
    }
    break;
    case 3: //"GPIO"
    {
      if (wiringPi_stat == -1)
        return Status::CANCELLED;

      int pin_index = std::stoi(request->config());
      pinMode(pin_index, OUTPUT);
      pullUpDnControl(pin_index, PUD_UP);
      digitalWrite(pin_index, (std::stoi(request->value()) > 0 ? HIGH : LOW));
      return Status::OK;
    }
    break;
    case 4: //"RFID"(RS-232)
    {
      if (rfid_serial == -1 || request->value().size() != 36)
        return Status::CANCELLED;
      memset(hex, 0, sizeof(hex));
      str_hex(request->value(), hex);
      if (write_rfid(hex))
        return Status::OK;
      return Status::CANCELLED;
    }
    break;
    default:
      return Status::CANCELLED;
      break;
    }
  }

  Status GET(ServerContext *context, const Request *request,
             Reply *reply) override
  {
    //函数原型 GET(string protocol, string config) -> string value;

    switch (protocol_map[request->protocol()])
    {
    case 1: //"Modbus-RTU"
    {
      //For convenience, define the following PLC address (*Different from protocol address*)
      //00000-09999 Coils
      //10000-19999 Discrete Inputs
      //30000-39999 Input Registers
      //40000-49999 Holding Registers

      std::string register_addr = request->config();
      if (register_addr.at(0) == '0')
      {
        if (modbusContext && modbus_read_bits(modbusContext, std::stoi(register_addr.substr(1)), 1, tab_discrete) != -1)
        {
          reply->set_value(std::to_string(unsigned(tab_discrete[0])));
          return Status::OK;
        }
      }
      else if (register_addr.at(0) == '1')
      {
        if (modbusContext && modbus_read_input_bits(modbusContext, std::stoi(register_addr.substr(1)), 1, tab_discrete) != -1)
        {
          reply->set_value(std::to_string(unsigned(tab_discrete[0])));
          return Status::OK;
        }
      }
      else if (register_addr.at(0) == '3')
      {
        if (modbusContext && modbus_read_input_registers(modbusContext, std::stoi(register_addr.substr(1)), 1, tab_register) != -1)
        {
          reply->set_value(std::to_string(unsigned(tab_register[0])));
          return Status::OK;
        }
      }
      else if (register_addr.at(0) == '4')
      {
        if (modbusContext && modbus_read_registers(modbusContext, std::stoi(register_addr.substr(1)), 1, tab_register) != -1)
        {
          reply->set_value(std::to_string(unsigned(tab_register[0])));
          return Status::OK;
        }
      }
      return Status::CANCELLED;
    }
    break;
    case 2: //"TCP"
    {
      //Required format:
      //xxx.xxx.xxx.xxx:xxxx
      int cli_socket = 0;
      if (!Init_Tcp(request->config(), cli_socket))
        return Status::CANCELLED;

      memset(tcp_buf, 0, sizeof(tcp_buf));
      int stat = recv(cli_socket, tcp_buf, sizeof(tcp_buf), 0);
      close(cli_socket);

      if (stat >= 0)
      {
        reply->set_value(tcp_buf);
        return Status::OK;
      }
      else
      {
        printf("[Error] TCP communication broken. \n");
        return Status::CANCELLED;
      }
    }
    break;
    case 3: //"GPIO"
    {
      if (wiringPi_stat == -1)
        return Status::CANCELLED;

      int pin_index = std::stoi(request->config());
      pinMode(pin_index, INPUT);
      pullUpDnControl(pin_index, PUD_UP);
      reply->set_value(std::to_string(digitalRead(pin_index)));
      return Status::OK;
    }
    break;
    case 4: //"RFID"(RS-232)
    {
      if (rfid_serial == -1)
        return Status::CANCELLED;
      //bool read_rfid(unsigned char *finaldata);
      memset(hex, 0, sizeof(hex));
      if (read_rfid(hex))
      {
        reply->set_value(hex_str(hex));
        return Status::OK;
      }
      return Status::CANCELLED;
    }
    break;
    default:
      return Status::CANCELLED;
      break;
    }
  }
};

MappingServiceImpl::MappingServiceImpl()
{
  //Whether there needs or not, initialize it first to save time in operation.

  //Modbus-RTU:
  modbusContext = modbus_new_rtu("/dev/ttyPLC", 9600, 'E', 8, 1);
  if (modbusContext)
  {
    if (modbus_set_slave(modbusContext, 1) != -1 && modbus_connect(modbusContext) != -1)
    {
      printf("[Info] Modbus-RTU initialized. \n");
    }
    else
    {
      printf("[Error] Failed to connect in Modbus-RTU. \n");
      modbus_free(modbusContext);
      modbusContext = nullptr;
    }
  }
  else
  {
    printf("[Error] Failed to allocate a Modbus-RTU. \n");
  }

  //TCP:
  memset(tcp_buf, 0, sizeof(tcp_buf));

  //GPIO:
  if ((wiringPi_stat = wiringPiSetup()) == -1)
    printf("[Error] Failed to initialize GPIO. \n");

  //RFID(RS-232):
  if ((rfid_serial = open("/dev/ttyRFID", O_RDWR | O_NOCTTY | O_NDELAY)) != -1)
  {
    struct termios options;
    tcgetattr(rfid_serial, &options);
    tcflush(rfid_serial, TCIOFLUSH);
    cfsetispeed(&options, B38400);
    cfsetospeed(&options, B38400);
    options.c_cflag &= ~CSIZE;
    options.c_cflag |= CS8;     //8 databits
    options.c_cflag &= ~CSTOPB; //when set stopbits 2 use |= CSTOPB
    options.c_cflag |= PARENB;
    options.c_cflag &= ~PARODD;
    options.c_iflag |= INPCK; //even check

    options.c_iflag |= IGNBRK;
    options.c_iflag &= ~(BRKINT | ICRNL | IMAXBEL | ISTRIP | IXON);
    options.c_oflag &= ~(OPOST | ONLCR);
    options.c_lflag &= ~(ISIG | ICANON | IEXTEN | ECHO | ECHOE | ECHOK | ECHOKE | ECHOCTL);
    options.c_cc[VTIME] = 20; //5;
    options.c_cc[VMIN] = 1;

    if (tcsetattr(rfid_serial, TCSANOW, &options) != 0)
    {
      printf("[Error] Failed to set RFID COM. \n");
      close(rfid_serial);
      rfid_serial = -1;
    }
    else
    {
      printf("[Info] RFID initialized. \n");
    }
  }
  else
  {
    printf("[Error] Failed to open RFID serial port. \n");
  }
}

MappingServiceImpl::~MappingServiceImpl()
{
  //Free Modbus-RTU.
  if (modbusContext)
  {
    modbus_close(modbusContext);
    modbus_free(modbusContext);
    modbusContext = nullptr;
  }

  //Free RFID.
  if (rfid_serial != -1)
  {
    close(rfid_serial);
    rfid_serial = -1;
  }
}

bool MappingServiceImpl::Init_Tcp(const std::string addr_port, int &cli_socket)
{
  int pos = addr_port.find(":");
  std::string addr = addr_port.substr(0, pos);
  int port = std::stoi(addr_port.substr(pos + 1));

  struct sockaddr_in tcp_server;
  memset(&tcp_server, 0, sizeof(tcp_server));
  tcp_server.sin_family = AF_INET;
  tcp_server.sin_port = htons(port);
  tcp_server.sin_addr.s_addr = inet_addr(addr.c_str());

  if ((cli_socket = socket(AF_INET, SOCK_STREAM, 0)) >= 0)
  {
    if (connect(cli_socket, (struct sockaddr *)&tcp_server, sizeof(tcp_server)) >= 0)
    {
      printf("[Info] TCP communication established. \n");
    }
    else
    {
      printf("[Error] Failed to connect in TCP. \n");
      close(cli_socket);
      return false;
    }
  }
  else
  {
    printf("[Error] Failed to create a TCP socket. \n");
    return false;
  }
  return true;
}

void MappingServiceImpl::str_hex(const std::string &str, unsigned char *hex)
{
  const std::string HEX = "0123456789ABCDEF";
  std::stringstream ss;
  std::string _temp_str;
  for (int i = 0; i < str.size(); i++)
  {
    ss << HEX[(unsigned char)str[i] >> 4] << HEX[(unsigned char)str[i] & 0xf] << std::endl;
    ss >> _temp_str;
    hex[i] = strtol(_temp_str.c_str(), NULL, 16);
  }
}

std::string MappingServiceImpl::hex_str(unsigned char *hex)
{
  std::string str(36, 0);
  for (int i = 0; i < 36; i++)
  {
    sprintf(&str[i], "%c", hex[i]);
  }
  return str;
}

void MappingServiceImpl::CRC16(unsigned char data[], int cnt, unsigned char *crc16) //cnt == len-2
{
  unsigned int CRC_PRESET = 0xFFFF;
  unsigned int CRC_POLYNOM = 0x8408;
  union order_crc crc;

  int i, j;
  //unsigned char crc16[2];
  crc.data = CRC_PRESET;
  for (i = 0; i < cnt; i++)
  {
    crc.data ^= data[i];
    for (j = 0; j < 8; j++)
    {
      if (crc.data & 0x0001)
      {
        crc.data = (crc.data >> 1) ^ CRC_POLYNOM;
      }
      else
      {
        crc.data = (crc.data >> 1);
      }
    }
  }
  //printf("%x\n",crc);
  crc16[0] = crc.buffer[0];
  crc16[1] = crc.buffer[1];
}

bool MappingServiceImpl::write_rfid(unsigned char *sourcedata)
{
  //unsigned char data_write_guid[100] = {0x05, 0x29, 0xff, 0xf0, 0x24, 0x00, 0x00, 0x07};
  unsigned char data_write_guid_H8[100] = {0x05, 0x29, 0xff, 0xf0, 0x24, 0x00, 0x10, 0x07}; //GUID高32bytes（前8块的值）
  unsigned char data_write_guid_L1[100] = {0x05, 0x0d, 0xff, 0xf0, 0x24, 0x00, 0x18, 0x00}; //GUID低4bytes（后1块的值）
  //unsigned char data_write_negooutput[100] = {0x05, 0x29, 0xff, 0xf0, 0x24, 0x00, 0x08, 0x07};
  unsigned char read_buff[100] = {0};

  memcpy(&data_write_guid_H8[8], sourcedata, 32);
  CRC16(&data_write_guid_H8[1], 39, &data_write_guid_H8[40]);
  write(rfid_serial, data_write_guid_H8, 42);
  usleep(500000);
  if (read(rfid_serial, read_buff, 100) <= 0)
    return false;

  memset(read_buff, 0, sizeof(read_buff));
  memcpy(&data_write_guid_L1[8], &sourcedata[32], 4);
  CRC16(&data_write_guid_L1[1], 11, &data_write_guid_L1[12]);
  write(rfid_serial, data_write_guid_L1, 14);
  usleep(500000);
  if (read(rfid_serial, read_buff, 100) <= 0)
    return false;

  return true;
  /*
    memcpy(&data_write_negooutput[8], &sourcedata[32], 32);
    CRC16(&data_write_negooutput[1], 39, &data_write_negooutput[40]);

    write(rfid_serial, data_write_negooutput, 42);
    usleep(500000);

    if (read(rfid_serial, read_buff, 100) > 0) {
        printf("Write RFID negotiation output completely! \n");
    } else {
        printf("Failed to write RFID negotiation output! \n");
        return 0;
    }
    */
}

bool MappingServiceImpl::read_rfid(unsigned char *finaldata)
{
  int i = 0, j = 0;
  unsigned char read_buff[256] = {0};
  //unsigned char read_command_guid[50] = {0x05, 0x09, 0xFF, 0xF0, 0x23, 0x00, 0x00, 0x07, 0x1B, 0x8E};
  unsigned char read_command_guid_H8[100] = {0x05, 0x09, 0xFF, 0xF0, 0x23, 0x00, 0x10, 0x07, 0x8A, 0x1B}; //GUID高32bytes（前8块的值）
  unsigned char read_command_guid_L1[100] = {0x05, 0x09, 0xFF, 0xF0, 0x23, 0x00, 0x18, 0x00, 0xF5, 0xA1}; //GUID低4bytes（后1块的值）
  //unsigned char read_command_negotiation[50] = {0x05, 0x09, 0xFF, 0xF0, 0x23, 0x00, 0x08, 0x07, 0xDB, 0x40};
  unsigned char no_rfid_read[8] = {0x05, 0x07, 0x01, 0xF0, 0x23, 0x00, 0x80, 0x99};

  write(rfid_serial, read_command_guid_H8, 10);
  usleep(500000);
  if (read(rfid_serial, read_buff, 256) > 0)
  {
    if (memcmp(read_buff, no_rfid_read, 8) == 0)
      return false;
    for (i = 0, j = 0; i < 40; i++)
    {
      if (i % 5 != 0)
        finaldata[j++] = read_buff[16 + i];
    }
  }
  else
  {
    printf("[Error] Failed to read RFID! - Error: %s. \n", strerror(errno));
    return false;
  }

  memset(read_buff, 0, sizeof(read_buff));
  write(rfid_serial, read_command_guid_L1, 10);
  usleep(500000);
  if (read(rfid_serial, read_buff, 256) > 0)
  {
    if (memcmp(read_buff, no_rfid_read, 8) == 0)
      return false;
    for (i = 0, j = 0; i < 5; i++)
    {
      if (i % 5 != 0)
        finaldata[32 + j++] = read_buff[16 + i];
    }
  }
  else
  {
    printf("[Error] Failed to read RFID! - Error: %s. \n", strerror(errno));
    return false;
  }

  return true;
  /*
    memset(read_buff, 0, 256);
    write(rfid_serial, read_command_negotiation, 10);
    usleep(500000);
    if (read(rfid_serial, read_buff, 256) > 0) {
      for(i = 0, j = 0; i < 40; i++) {
          if(i % 5 != 0) finaldata[32 + j++] = read_buff[16 + i];
      }
    } else {
      printf("Failed to read RFID negotiation! \n");
      return 0;
    }
    */
}

void RunServer()
{
  std::string server_address("0.0.0.0:50051");
  MappingServiceImpl service;

  grpc::EnableDefaultHealthCheckService(true);
  grpc::reflection::InitProtoReflectionServerBuilderPlugin();

  ServerBuilder builder;
  builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
  builder.RegisterService(&service);
  std::unique_ptr<Server> server(builder.BuildAndStart());
  printf("Server listening on %s\n", server_address.c_str());

  server->Wait();
}

int main(int argc, char **argv)
{
  RunServer();
  return 0;
}
