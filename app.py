from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restful import Api
from ref.config import Config

from resources.tag import TagSearchResource

from resources.user import UserRegisterResource, UserLoginResource, UserLogoutResource, jwt_blocklist

from resources.image import FileUploadResource
from resources.posting import PostingInsertListResource, PostingUpdateDeleteResource
from resources.rekognition import ObjectDetectionResource
from resources.follow import followResource

# API 서버를 구축하기 위한 기본 구조
app = Flask(__name__)

# 환경변수 셋팅
app.config.from_object(Config) # 만들었던 Config.py의 Config 클래스 호출

# JWT 토큰 생성
jwt = JWTManager(app)

# 로그아웃 된 토큰이 들어있는 set을 jwt에게 알림
@jwt.token_in_blocklist_loader
def check_it_token_is_revoked(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return jti in jwt_blocklist

# restfulAPI 생성
api = Api(app)

# 경로와 리소스(api코드) 연결
api.add_resource(UserRegisterResource, '/users/register')
api.add_resource(UserLoginResource, '/users/login')
api.add_resource(UserLogoutResource, '/users/logout')

api.add_resource(FileUploadResource, '/upload')
api.add_resource(PostingInsertListResource, '/posting')
api.add_resource(PostingUpdateDeleteResource, '/posting/<int:post_id>')
api.add_resource(ObjectDetectionResource, '/object_detection')

api.add_resource(TagSearchResource, '/posting/search/tag')

api.add_resource(followResource, '/follow')

if __name__ == '__main__' :
    app.run()