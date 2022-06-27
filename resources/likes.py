from flask import request
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity, jwt_required
import mysql.connector
from ref.mysql_connection import get_connection

class LikesResource(Resource) :
    # like
    @jwt_required()
    def post(self, post_id) :
        try :
            user_id = get_jwt_identity()
            connection = get_connection()
            query = '''select * from likes where userId=%s and postingId=%s;'''
            record = (user_id, post_id )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()  
            if result_list :
                return { "알림" : "이미 좋아요를 하였습니다."}, 500

            query = '''insert into likes (userId, postingId) values (%s, %s);'''
            record = (user_id, post_id )
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()
            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 503 #HTTPStatus.SERVICE_UNAVAILABLE

        post_id = str(post_id)
        return{
            "알림" : post_id + "의 포스팅 좋아요."
        }, 200

    # unlike
    @jwt_required()
    def delete(self, post_id) :
        try :
            connection = get_connection()

            # 이메일이 존재하면 해당 유저의 id를 팔로우 해제
            user_id = get_jwt_identity()
            query = '''delete from likes where userId = %s and postingId = %s;'''                 
            record = (user_id, post_id)

            record = (user_id, post_id)
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()
            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 503 #HTTPStatus.SERVICE_UNAVAILABLE

        post_id = str(post_id)
        return{
            "알림" : post_id +"의 포스팅 좋아요 해제." }, 200