from flask import request
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity, jwt_required
import mysql.connector
from ref.mysql_connection import get_connection
from ref.config import Config
from datetime import datetime
import boto3

class PostingInsertListResource(Resource) :
	# 이미지와 내용 포스팅
    @jwt_required()
    def post(self) :
        # 클라이언트로부터 데이터 받기
        # photo(file), content(text)
        if 'photo' not in request.files :
            return {"error" : "파일을 업로드해주세요."}, 400

        file = request.files['photo']
        content = request.form['content']
        userId = get_jwt_identity()

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
        
        # RDS DB에 이미지 주소, 내용 저장
        try :
            connection = get_connection()
            query = '''
                    insert into posting
                        (imageUrl, content, userId)
                    values
                        (%s ,%s, %s);
                    '''

            record = (new_file_name, content, userId)
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()
            posting_id = cursor.lastrowid
            cursor.close()
            connection.close()

        except Exception as e :
            return {'error' : str(e)}, 500

        client = boto3.client('rekognition', 'ap-northeast-2',
            aws_access_key_id = Config.ACCESS_KEY,
            aws_secret_access_key = Config.SECRET_ACCESS)
        response = client.detect_labels(Image= {'S3Object': {
                                                        'Bucket' : Config.S3_BUCKET,
                                                        'Name' : new_file_name
                                                            }}, MaxLabels=5)      

        # 4. 레이블의 Name을 가지고, 태그를 만든다!!!!!!!

        # 4-1. label['Name'] 의 문자열을 tag_name 테이블에서 찾는다.
        #      테이블에 이 태그가 있으면, id 를 가져온다.
        #      이 태그 id와 위의 postingId 를 가지고, 
        #      tag 테이블에 저장한다.

        # 4-2. 만약 tag_name 테이블에 이 태그가 없으면, 
        #      tag_name  테이블에, 이 태그이름을 저장하고, 
        #      저장된 id 값과 위의 postingId 를 가지고,
        #      tag  테이블에 저장한다. 

        for label in response['Labels'] :
            # label['Name'] 이 값을 우리는 태그 이름으로 사용할것.
            try :
                connection = get_connection()
                query = '''select * from tag_name where name = %s;'''
                record = (label['Name'],)
                cursor = connection.cursor(dictionary = True)
                cursor.execute(query, record)
                result_list = cursor.fetchall()

                if len(result_list) == 0 :
                    # 태그이름을 insert 해준다.
                    query = '''insert into tag_name (name)
                                values (%s );'''
                    record = (label['Name'],  )
                    # 3. 커서를 가져온다.
                    cursor = connection.cursor()
                    # 4. 쿼리문을 커서를 이용해서 실행한다.
                    cursor.execute(query, record)
                    # 5. 커넥션을 커밋해줘야 한다 => 디비에 영구적으로 반영하라는 뜻
                    connection.commit()
                    # 태그아이디를 가져온다.
                    tag_name_id = cursor.lastrowid
                else :
                    tag_name_id = result_list[0]['id']

                # posting_id 와 tag_name_id 가 준비되었으니
                # tag 테이블에 insert 한다.
                query = '''insert into tag (tagId, postingId)
                            values (%s, %s );'''
                record = (tag_name_id, posting_id )
                cursor = connection.cursor()
                cursor.execute(query, record)
                connection.commit()
                cursor.close()
                connection.close()

            except Exception as e :
                return {'error' : str(e)}, 500

        return {'알림' : '포스팅이 작성되었습니다.',
                'image_url' : Config.S3_LOCATION + file.filename,
                "label" : response["Labels"] }

    # 포스팅 목록 보기
    @jwt_required()
    def get(self) :
        try :
            connection = get_connection()
            userId = get_jwt_identity()
            page = request.args.get('page')
            page = str((int(page)-1)*25)
            query = ''' select p.*, count(l.postingId) as '좋아요' from posting p
                        left join likes l on l.postingId=p.id
                        where p.userId = %s group by p.id
                        limit ''' + page + ''', 25;'''
            record = (userId, ) # tuple
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()

            if len(result_list) == 0 :
                return { "알림" : "포스팅이 없습니다."}

            i = 0
            for record in result_list :
                result_list[i]['createdAt'] = record['createdAt'].isoformat()
                result_list[i]['updatedAt'] = record['updatedAt'].isoformat()
                i += 1
            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 503 #HTTPStatus.SERVICE_UNAVAILABLE

        return{ "포스팅 내용 : " : result_list 
        # return{ "포스팅 내용" : [(lambda x: "{}\n작성일 : {} / 수정일 : {} \n{}\n내용 : {}"\
        #     .format(result_list[x]['name'], result_list[x]['createdAt'], \
        #         result_list[x]['updatedAt'], result_list[x]['imageUrl'], result_list[x]['content']))\
        #         (x) for x in range(int(len(result_list)))]
        
        }, 200

class FollowPostingListResource(Resource) :
    # 팔로우한 친구의 메모 함께 보기
    @jwt_required()
    def get(self) :
        try :
            connection = get_connection()
            user_id = get_jwt_identity()
            page = request.args.get('page')
            page = str((int(page)-1)*25)
            
            query = '''
                        select  u.name as '작성자', p.imageUrl as '사진', p.content as '포스팅 내용',
                        p.createdAt as '작성일', p.updatedAt as '수정일',
                        if(l.userId is null, 0,1) as '나의 좋아요 여부',
                        count(l2.postingId) as '좋아요'
                        from posting p
                        join follow f on p.userId = f.followeeId
                        join users u on u.id=p.userId
                        left join likes l on l.postingId=p.id and l.userId = %s
                        left join likes l2 on l2.postingId=p.id
                        where f.followerId = %s group by p.id
                        limit ''' + page + ''', 25;'''

            record = (user_id, user_id)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()
            if len(result_list) == 0 :
                return { "알림" : "팔로우한 친구가 없습니다."}
            i = 0
            for record in result_list :
                result_list[i]['작성일'] = record['작성일'].isoformat()
                result_list[i]['수정일'] = record['수정일'].isoformat()
                i += 1
            cursor.close()
            connection.close()
        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 503 #HTTPStatus.SERVICE_UNAVAILABLE

        return{
            "메모 내용" : result_list
        }, 200

class PostingReadUpdateDeleteResource(Resource) :
    # 포스팅 상세 보기
    @jwt_required()
    def get(self, post_id) :
        userId = get_jwt_identity()
        try :
            # 클라이언트로부터 데이터 받기
            connection = get_connection()
            query = '''select p.*, u.email, u.name, count(l.postingId) as '좋아요' from posting p
                        join users u on p.userId=u.id
                        left join likes l on p.id= l.postingId
                        where p.userId=%s and p.id=%s group by p.id;'''
            record = (userId, post_id)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()  
            if len(result_list) < 1 :  
                return { "알림" : "포스팅의 권한이 없습니다."}
            connection.commit()
            cursor.close()
            connection.close()
            i = 0
            for record in result_list :
                result_list[i]['createdAt'] = record['createdAt'].isoformat()
                result_list[i]['updatedAt'] = record['updatedAt'].isoformat()
                i += 1
        except Exception as e :
            return {'error' : str(e)}, 500
        return { "포스팅 상세 보기" : result_list}

	# 포스팅 수정
    @jwt_required()
    def put(self, post_id) :
        userId = get_jwt_identity()
        # 클라이언트로부터 데이터 받기
        # photo(file), content(text)
        content = request.form['content']

        # 소유자 권한 설정 (소유자이면 아래 코드 실행)
        connection = get_connection()
        query = '''select id, userId from posting where userId=%s and id=%s;'''
        record = (userId, post_id)
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, record)
        result_list = cursor.fetchall()

        if len(result_list) :
            if 'photo' not in request.files :
                try :
                    query = '''update posting set content=%s where userId=%s and id=%s;'''
                    record = (content, userId, post_id)
                    cursor = connection.cursor()
                    cursor.execute(query, record)
                    connection.commit()
                    cursor.close()
                    connection.close()
                except Exception as e :
                    return {'error' : str(e)}, 500
            else :
                # 파일명 변경, 파일명은 유니크 (중복이 없도록)
                file = request.files['photo']
                current_time = datetime.now()
                new_file_name = current_time.isoformat().replace(':', '_') + '.png'
                file.filename = new_file_name

                # S3에 업로드, AWS 라이브러리 사용 (boto3)
                s3 = boto3.client('s3', aws_access_key_id = Config.ACCESS_KEY, \
                            aws_secret_access_key = Config.SECRET_ACCESS)
                try :
                    s3.upload_fileobj(file, Config.S3_BUCKET, file.filename, \
                        ExtraArgs={'ACL':'public-read', 'ContentType':file.content_type})
                except Exception as e :
                    return {'error' : str(e)}, 500
            
                # DB 수정
                try :
                    connection = get_connection()
                    query = '''update posting set imageUrl=%s, content=%s where userId=%s and id=%s;'''
                    record = (new_file_name, content, userId, post_id)
                    cursor = connection.cursor()
                    cursor.execute(query, record)
                    posting_id = cursor.lastrowid

                    # 태그 삭제
                    query = '''delete from tag where postingId = %s'''
                    record = (posting_id, )
                    cursor = connection.cursor()
                    cursor.execute(query, record)
                    connection.commit()
                    cursor.close()
                    connection.close()

                    # 객체 탐지
                    client = boto3.client('rekognition', 'ap-northeast-2',
                        aws_access_key_id = Config.ACCESS_KEY,
                        aws_secret_access_key = Config.SECRET_ACCESS)
                    response = client.detect_labels(\
                        Image= {'S3Object': {
                                            'Bucket' : Config.S3_BUCKET,
                                            'Name' : new_file_name
                                            }}, MaxLabels=5)  
                except Exception as e :
                    return {'error' : str(e)}, 500

                client = boto3.client('rekognition', 'ap-northeast-2',
                aws_access_key_id = Config.ACCESS_KEY,
                aws_secret_access_key = Config.SECRET_ACCESS)
                response = client.detect_labels(Image= {'S3Object': {
                                                            'Bucket' : Config.S3_BUCKET,
                                                            'Name' : new_file_name
                                                                }}, MaxLabels=5)      

                for label in response['Labels'] :
                    # label['Name'] 이 값을 우리는 태그 이름으로 사용할것.
                    try :
                        query = '''select * from tag_name where name = %s;'''
                        record = (label['Name'],)
                        connection = get_connection()
                        cursor = connection.cursor(dictionary = True)
                        cursor.execute(query, record)
                        result_list = cursor.fetchall()

                        if len(result_list) == 0 :
                            # 태그이름을 insert 해준다.
                            query = '''insert into tag_name (name)
                                        values (%s );'''
                            record = (label['Name'],  )
                            # 3. 커서를 가져온다.
                            cursor = connection.cursor()
                            # 4. 쿼리문을 커서를 이용해서 실행한다.
                            cursor.execute(query, record)
                            # 5. 커넥션을 커밋해줘야 한다 => 디비에 영구적으로 반영하라는 뜻
                            connection.commit()
                            # 태그아이디를 가져온다.
                            tag_name_id = cursor.lastrowid
                        else :
                            tag_name_id = result_list[0]['id']

                        # posting_id 와 tag_name_id 가 준비되었으니
                        # tag 테이블에 insert 한다.
                        query = '''insert into tag (tagId, postingId)
                                    values (%s, %s );'''
                        record = (tag_name_id, posting_id )
                        cursor = connection.cursor()
                        cursor.execute(query, record)
                        connection.commit()
                        cursor.close()
                        connection.close()

                    except Exception as e :
                        return {'error' : str(e)}, 500
        else :
            return { "알림" : "수정 권한이 없습니다."}

        return {'알림' : '포스팅이 수정되었습니다.' }

	# 포스팅 삭제
    @jwt_required()
    def delete(self, post_id) :
        try :
            userId = get_jwt_identity()

            # 소유자 권한 설정 (소유자이면 아래 코드 실행)
            connection = get_connection()
            query = '''select id, userId from posting where userId=%s and id=%s;'''
            record = (userId, post_id)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()

            if len(result_list) :
                connection = get_connection()
                query = '''delete from posting where userId = %s and id = %s;'''
                record = (userId, post_id)
                cursor = connection.cursor()
                cursor.execute(query, record)

                query = '''delete from tag where postingId = %s;'''
                record = (post_id,)
                cursor = connection.cursor()
                cursor.execute(query, record)
                connection.commit()
            else :
                return { "알림" : "삭제 권한이 없습니다."}, 500

            connection.commit()
            cursor.close()
            connection.close()
        except Exception as e :
            return {'error' : str(e)}, 500

        return { '알림' : '포스팅이 삭제되었습니다.' }