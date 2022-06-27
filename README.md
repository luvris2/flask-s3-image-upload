# SNS API 
**기능 설명**
- 유저 관련
  - 회원가입, 로그인, 로그아웃 기능
- 포스팅 관련
  - 포스팅 작성, 수정, 삭제
  - 내 포스팅 보기, 포스팅 상세 보기, 친구들의 포스팅 보기
  - 이미지 포스팅시 이미지의 객체를 탐지하여 태그 자동 생성하기
  - 태그 검색하기
  - 좋아요 / 좋아요 해제
- 친구 관련
  - 친구 추가, 해제
---
# DB 구조
### Table : posting
- Columns
  - id : 기본 인덱스 (INT/ PK, NN, UN, AI)
  - imageUrl: 업로드한 이미지의 주소 (VARCHAR(500)
  - userId: 유저의 고유 ID (INT)
  - content : 포스팅 내용 (VARCHAR(500)
  - createdAt : 작성일 (TIMESTAMP)/ Default: now()
  - updatedAt : 수정일 (TIMESTAMP)/ Default: now() on update now()
- Foreign Keys
  - memo table : user_id -> user table : id
### Table : users
- Columns
  - id : 기본 인덱스 (INT/ PK, NN, UN, AI)
  - email : 이메일 (VARCHAR(45)/ NN, UQ)
  - password : 비밀번호 (VARCHAR200/ NN)
  - name : 사용자 이름 (VARCHAR45/ NN)
### Table : follow
- Columns
   - id : 기본 인덱스 (INT/ PK, NN, UN, AI)
   - followerId : 친구 추가를 건 사람의 식별 ID (INT/ UN)
   - followeeId : 친구 추가를 받은 사람의 식별 ID (INT/ UN)
   - createdAt : 친구 추가 신청일 (TIMESTAMP)/ Default=now()
### Table : tag_name
- Columns
   - id : 기본 인덱스 (INT/ PK, NN, UN, AI)
   - name : 태그 내용 (VARCHAR(100))
### Table : tag
- Columns
   - id : 기본 인덱스 (INT/ PK, NN, UN, AI)
   - tagId : 태그 식별 ID (INT/ UN)
   - postingId : 포스팅 식별 ID (INT/ UN)
### Table : likes
- Columns
   - id : 기본 인덱스 (INT/ PK, NN, UN, AI)
   - userId : 태그 식별 ID (INT/ UN)
   - postingId : 포스팅 식별 ID (INT/ UN)
---

# 파일 구조
- app.py : API 메인 파일
  - resources 폴더
    - follow.py : 친구 추가, 해제
    - image.py : 이미지 업로드 테스트 소스 코드
    - rekognition.py : 이미지 객체 탐지 테스트 소스 코드
    - posting.py : 포스팅 작성, 수정, 삭제, 내 포스팅 보기, 친구들의 포스팅 보기,이미지 업로드시 이미지 객체를 탐지하여 태그 자동 생성
    - tag.py : 태그 검색
    - user.py : 회원가입, 로그인, 로그아웃
    - likes.py : 좋아요 표시, 좋아요 해제
  - ref 폴더
    - config.py : 가상환경 설정 (토큰)
    - test.py : SQL Query 테스트 코드
    - mysql_connection.py : DB 연동 설정
    - utils.py : 비밀번호 암호화, 식별 ID 토큰화 설정
  - 참고 사항
    - ref폴더의 config, mysql_connection 파일은 보안을 위해 비공개
---
# 각 파일 설명
**app.py**
- API의 기본 틀이 되는 메인 파일
- 가상 환경 셋팅
- JWT 토큰을 생성과 파괴
- 리소스화 된 클래스들의 경로 설정 (API 기능)

---
**mysql_connection.py**
- DB 연동에 관련된 함수를 정의한 파일
  - 해당 코드는 개개인의 환경에 따라 다르므로 파일은 미첨부
  - 아래의 코드로 파일을 생성하여 자신의 환경에 맞게 코딩
``` python
import mysql.connector
def get_connection() :
    connection = mysql.connector.connect(
        host='hostname',
        database='databasename',
        user='username',
        password='password' )
    return connection
```
---
**config.py**
- 가상 환경의 값을 설정하는 파일
  - 토큰의 암호화 방식 설정
    - 토큰의 시크릿 키는 원래 비공개이나 테스트용이기 때문에 공개처리
    - 토큰은 유저의 개인 식별 ID를 암호화하여 사용

**utils.py**
- 사용자로부터 입력받은 비밀번호를 암호화하는 파일
  - 입력 받은 비밀번호를 해시로 매핑하여 암호화
  - 암호화된 비밀번호와 새로 입력 받은 값이 같은지 확인

---

**users.py**
- Class UserRegisterResource
  - POST
  - 회원가입을 하면 DB에 입력한 정보가 등록되는 기능
    - 이메일과 비밀번호 유효성 검사
    - 비밀번호 암호화, 식별 ID 토큰화
  - 테스트 경로 : http://127.0.0.1:5000/users/register
```python
{ # json으로 입력
"email": "test@naver.com",
"password": "test@1234",
"name" : "테스트용사용자"
}
```
- class UserLoginResource
  - POST
  - 로그인
    - DB에 입력한 이메일 존재 유무와 비밀번호 동일 유무 확인
    - 입력한 데이터가 DB의 정보와 일치하면 식별 ID 토큰 생성
  - 테스트 경로 : http://127.0.0.1:5000/users/login
``` python
{
"email": "test@naver.com",
"password": "test@1234"
}
```
- class UserLogoutResource
  - POST
  - 로그아웃
    - 생성된 토큰을 파괴  
  - 테스트 경로 : http://127.0.0.1:5000/users/logout
``` python
# Headers에 토큰 입력
"KEY" : "Authorization"
"VALUE" Bearer eyJ0eXAiO~생략
```

---
 **posting.py**
- class PostingInsertListResource(Resource)
  - POST
  - 이미지와 함께 포스팅 작성
    - 이미지는 AWS S3 드라이브에 저장
    - 이미지 객체를 탐지하여 자동으로 태그 생성
  - 테스트 경로 : http://127.0.0.1:5000/posting
``` python
# Headers에 토큰 입력
"KEY" : "Authorization"
"VALUE" Bearer eyJ0eXAiO~생략

# form-data으로 입력
photo : 이미지 파일 업로드
content : 작성내용 
```
- class PostingInsertListResource(Resource)
  - GET
  - 내 포스팅 보기
    - 페이지당 25개씩 출력
  - 테스트 경로 : http://127.0.0.1:5000/posting
``` python
# Headers에 토큰 입력
"KEY" : "Authorization"
"VALUE" Bearer eyJ0eXAiO~생략

# Params
"KEY" : page
"VALUE" : 페이지수
```

- class FollowPostingListResource(Resource)
  - GET
  - 친구들의 포스팅 보기
    - 페이지당 25개씩 출력
  - 테스트 경로 : http://127.0.0.1:5000/posting/follow
``` python
# Headers에 토큰 입력
"KEY" : "Authorization"
"VALUE" Bearer eyJ0eXAiO~생략

# Params
"KEY" : page
"VALUE" : 페이지수
```

- class PostingReadUpdateDeleteResource(Resource)
  - GET
  - 포스팅 상세 보기
    - 좋아요 수 표시
  - 테스트 경로 : http://127.0.0.1:5000/posting/<int:post_id>
``` python
# Headers에 토큰 입력
"KEY" : "Authorization"
"VALUE" Bearer eyJ0eXAiO~생략
```
- class PostingReadUpdateDeleteResource(Resource)
  - PUT
  - 포스팅 내용 수정
    - 포스팅의 소유자 일 경우에만 수정 소스코드 실행
    - 이미지가 없을 경우
        - 내용만 수정
    - 이미지가 있을 경우
        - 이미지와 내용 수정
        - 기존 태그 삭제 후 새로운 태그로 변경
        - DB에서의 기존 태그도 같이 삭제
  - 테스트 경로 : http://127.0.0.1:5000/posting/<int:post_id>
``` python
# Headers에 토큰 입력
"KEY" : "Authorization"
"VALUE" Bearer eyJ0eXAiO~생략

# form-data으로 입력
photo : 이미지 파일 업로드
content : 작성내용 
```
- class PostingReadUpdateDeleteResource(Resource)
  - DELETE
  - 포스팅 삭제
    - 포스팅의 소유자 일 경우에만 삭제 소스코드 실행
  - 테스트 경로 : http://127.0.0.1:5000/posting/<int:post_id>
``` python
# Headers에 토큰 입력
"KEY" : "Authorization"
"VALUE" Bearer eyJ0eXAiO~생략
```
---
**follow.py**
- class followResource(Resource)
  - POST
  - 친구 추가
  - 테스트 경로 : http://127.0.0.1:5000/follow
``` python
# Headers에 토큰 입력
"KEY" : "Authorization"
"VALUE" Bearer eyJ0eXAiO~생략

# json으로 입력
{  "email" : "친구추가 할 이메일" }
```
- class followResource(Resource)
  - DELETE
  - 친구 끊기
  - 테스트 경로 : http://127.0.0.1:5000/follow
``` python
# Headers에 토큰 입력
"KEY" : "Authorization"
"VALUE" Bearer eyJ0eXAiO~생략

# json으로 입력
{  "email" : "친구끊기 할 이메일" }
```
 ---
**tag.py**
- class TagSearchResource(Resource)
  - GET
  - 태그 검색
  - 테스트 경로 : http://127.0.0.1:5000/posting/search/tag
```
# Params
keyword : 검색어
page : 페이지 번호, 페이지당 25개씩 출력
```
**likes.py**
- class LikesResource(Resource)
  - POST
  - 좋아요 표시
    - 좋아요 중복 방지
  - 테스트 경로 : http://127.0.0.1:5000/likes/<int:post_id>
```
``` python
# Headers에 토큰 입력
"KEY" : "Authorization"
"VALUE" Bearer eyJ0eXAiO~생략
```
- class LikesResource(Resource)
  - DELETE
  - 좋아요 해제
  - 테스트 경로 : http://127.0.0.1:5000/likes/<int:post_id>
```
``` python
# Headers에 토큰 입력
"KEY" : "Authorization"
"VALUE" Bearer eyJ0eXAiO~생략
```