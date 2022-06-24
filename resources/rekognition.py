from flask import request
from flask_restful import Resource
from datetime import datetime
import boto3
from ref.config import Config

class ObjectDetectionResource(Resource) :
    # 객체 탐지 API
    def get(selft) :
        # 1. 클라이언트로부터 데이터 받기
        filename = request.args['filename']

        # 2. 인공지능 rekognition을 이용하여 object detection
        client = boto3.client('rekognition', 'ap-northeast-2',
                            aws_access_key_id = Config.ACCESS_KEY,
                            aws_secret_access_key = Config.SECRET_ACCESS)
        response = client.detect_labels(Image= {'S3Object': {
                                                        'Bucket' : Config.S3_BUCKET,
                                                        'Name' : filename
                                                            }}, MaxLabels=10)
        return {
                "result" : "success",
                "label" : response["Labels"]
        }, 200