from minio import Minio
from minio import error

minioClient = Minio('192.168.137.121:30002',
                    access_key='YOURACCESSKEY',
                    secret_key='YOURSECRETKEY',
                    secure=False)

try:
    mypath = "/home/pi/aml2ua/model_generation/aml/"
    from os import listdir
    from os.path import isfile, join
    files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    print("Found AML file: ", files)
    aml = mypath + files[0]
    minioClient.fput_object(
        'aml', files[0], aml)
except error.ResponseError as err:
    print(err)
