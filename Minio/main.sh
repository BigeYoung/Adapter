mc config host add minio_server http://116.62.166.181:9000/ minioadmin minioadmin --api s3v4
mc cp /AML/* minio_server/aml