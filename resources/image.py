from flask import request
from flask_restful import Resource
from datetime import datetime
import boto3
from ref.config import Config

class FileUploadResource(Resource) :
    def post(selft) :
        # 1. request.files : 클라이언트로부터 파일 받기
        # 파일이 없는 상태로 호출되면 유저에게 에러 메시지 출력

        # photo는 클라이언트에서 보내는 파일의 key 값
        if 'photo' not in request.files :
            return { "error" : "파일을 업로드 해주세요."}, 400

        # 클라이언트로부터 파일 받기
        file = request.files['photo']

        # 파일명 변경, 파일명은 유니크 (중복이 없도록)
        current_time = datetime.now()
        new_file_name = current_time.isoformat().replace(':', '_') + '.png'

        # 클라이언트에서 받은 파일의 이름 변경
        file.filename = new_file_name

        # S3에 업로드
        # AWS 라이브러리 사용 (boto3)
        s3 = boto3.client('s3', aws_access_key_id = Config.ACCESS_KEY, \
                    aws_secret_access_key = Config.SECRET_ACCESS)

        try :
            s3.upload_fileobj(file, Config.S3_BUCKET, file.filename, \
                ExtraArgs={'ACL':'public-read', 'ContentType':file.content_type})
        except Exception as e :
            return {'error' : str(e)}, 500
        
        return {'result' : 'success',
                'image_url' : Config.S3_LOCATION + file.filename}