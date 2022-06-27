from unittest import result
from flask import request
from flask_restful import Resource
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
import mysql.connector
from ref.mysql_connection import get_connection
from ref.config import Config
import boto3

class TagSearchResource(Resource) :
    # 태그 검색, 페이지당 25개씩 출력
    def get(self) :
        keyword = request.args['keyword']
        page = request.args['page']
        page = str((int(page)-1)*25)        
        connection = get_connection()
        print(keyword, page)
        try : 
            query = '''
                        select p.* from tag_name tn
                        join tag t on tn.id = t.tagId
                        join posting p on p.id = t.postingId
                        where tn.name like '%'''+keyword+'''%'
                        group by t.postingId
                        limit ''' + page + ''', 25;'''
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            result_list = cursor.fetchall()
            i = 0
            for record in result_list :
                result_list[i]['createdAt'] = record['createdAt'].isoformat()
                result_list[i]['updatedAt'] = record['updatedAt'].isoformat()
                i += 1
            cursor.close()
            connection.close()
            print(result_list)

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 503 #HTTPStatus.SERVICE_UNAVAILABLE

        return {"검색 결과" : result_list}, 200