from minio import Minio
from minio import error

minioClient = Minio('116.62.166.181:9000',
                    access_key='minioadmin',
                    secret_key='minioadmin',
                    secure=False)

try:
    minioClient.make_bucket("aml")
except error.BucketAlreadyOwnedByYou as err:
    pass
except error.BucketAlreadyExists as err:
    pass
except error.ResponseError as err:
    raise

try:
    mypath = "/AML/"
    from os import listdir
    from os.path import isfile, join
    files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    print("Found AML file: ", files)
    aml = mypath + files[0]
    minioClient.fput_object(
        'aml', files[0], aml)
except error.ResponseError as err:
    print(err)
