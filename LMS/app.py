from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
#                플라스크   프론트 연결    요청, 응답 / 주소 전달 / 주소 생성 / 상태 저장소

import os
from LMS.common import Session
from LMS.service.PostService import PostService

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

@app.route('/login', methods=['GET','POST'])

# ----------------------------------------------------------------------------------------------------------------------
#                                                 회원 CRUD
# ----------------------------------------------------------------------------------------------------------------------

# 로그인
def login() :

    if request.method == 'GET' :
        return render_template('login.html')

    uid = request.form.get('uid')
    upw = request.form.get('upw')

    conn = Session.get_connection()

    try :
        with conn.cursor() as cursor :

            # 회원 정보 조회
            sql = "SELECT id, name, uid, role  \
            FROM members WHERE uid = %s AND password = %s"
            cursor.execute(sql, (uid, upw))
            user = cursor.fetchone()

            if user :
                session['user_id'] = user['id'] # 계정 일련번호 (회원번호)
                session['user_name'] = user['name'] # 계정 이름
                session['user_uid'] = user['uid']  # 계정 로그인명
                session['user_role'] = user['role']  # 계정 권한

                return redirect(url_for('index'))

            else :
                return "<script>alert('아이디 혹은 비번이 틀렸습니다.');history.back();</script>"

    finally :
        conn.close()

# 로그아웃
@app.route('/logout')
def logout() :

    session.clear()
    return redirect(url_for('login'))

# 회원가입
@app.route('/join', methods=['GET','POST'])
def join() :

    if request.method == 'GET' :
        return render_template('join.html')

    uid = request.form.get('uid')
    password = request.form.get('password')
    name = request.form.get('name')

    conn = Session.get_connection()
    try :
        with conn.cursor() as cursor :
            cursor.execute("SELECT id FROM members WHERE Uid = %s", (uid,))

            if cursor.fetchone() :
                return "<script>alert('이미 존재하는 아이디입니다.'); history.back();</script>"

            sql = "INSERT INTO members (uid, password, name) VALUES (%s, %s, %s)"
            cursor.execute(sql, (uid, password, name))
            conn.commit()

            return "<script>alert('회원가입이 완료되었습니다!');location.href='/login';</script>"

    except Exception as e :
        print(f"회원가입 에러: {e}")
        return "회원가입 도중 오류가 발생했습니다. /n join 매서드를 확인하세요."

    finally :
        conn.close()

# 회원 정보 수정
@app.route('/member/edit', methods = ['GET', 'POST'])
def member_edit() :

    if 'user_id' not in session :
        return redirect(url_for('login'))

    conn = Session.get_connection()

    try :
        with conn.cursor() as cursor :

            if request.method == 'GET' :
                # 기존 정보 불러오기
                cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
                user_info = cursor.fetchone()
                return render_template('member_edit.html', user = user_info)

            new_name = request.form.get('name')
            new_pw = request.form.get('password')

            if new_pw :
                sql = "UPDATE members SET name = %s, password = %s WHERE id = %s"
                cursor.execute(sql, (new_name, new_pw, session['user_id']))

            else :
                sql = "UPDATE members SET name = %s WHERE id = %s"
                cursor.execute(sql, (new_name, session['user_id']))

            conn.commit()
            session['user_name'] = new_name
            return "<script>alert('정보가 수정되었습니다.');location.href='/mypage';</script>"

    except Exception as e :
        print(f"회원 정보 수정 에러 : {e}")
        return "회원 정보 수정 도중 오류가 발생하였습니다. /n member_edit 매서드를 확인하세요."

    finally :
        conn.close()

# 마이페이지
@app.route('/mypage')
def mypage() :

    if 'user_id' not in session :
        return redirect(url_for('login'))

    conn = Session.get_connection()

    try :
        with conn.cursor() as cursor :

            # 1. 내 상세 정보 조회
            cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
            user_info = cursor.fetchone()

            # 2. 내가 쓴 게시물 갯수 조회 (작성한 boards 테이블 활용)
            cursor.execute("SELECT COUNT(*) as board_count FROM boards WHERE member_id = %s", (session['user_id'],))
            board_count = cursor.fetchone()['board_count']

            return render_template('mypage.html', user = user_info, board_count = board_count)

    finally :
        conn.close()

# ----------------------------------------------------------------------------------------------------------------------
#                                              자료실 (파일 업로드)
# ----------------------------------------------------------------------------------------------------------------------

# 파일 처리 경로
UPLOAD_FOLDER = 'uploads/'
# 폴더 부재 시 자동 생성
if not os.path.exists(UPLOAD_FOLDER) :
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# 최대 용량 제한 (e.g. 16MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# 파일 게시판 - 작성
@app.route('/filesboard/write', methods = ['GET', 'POST'])
def filesboard_write() :

    if 'user_id' not in session :
        return redirect(url_for('login'))

    if request.method == 'POST' :

        title = request.form.get('title')
        content = request.form.get('content')
        files = request.files.getlist('files')

        if PostService.save_post(session['user_id'], title, content, files) :
            return "<script>alert('게시물이 등록되었습니다.');location.href='/filesboard';</script>"

        else :
            return "<script>alert('등록 실패');history.back();</script>"

    return render_template('filesboard_write.html')

# 파일 게시판 - 목록
@app.route('/filesboard')
def filesboard_list() :

    posts = PostService.get_posts()
    return render_template('filesboard_list.html', posts=posts)

# 파일 게시판 - 자세히 보기
@app.route('/filesboard/view/<int:post_id>')
def filesboard_view(post_id) :
    post, files = PostService.get_post_detail(post_id)

    if not post :
        return "<script>alert('해당 게시글이 없습니다.'); location.href='/filesboard';</script>"

    return render_template('filesboard_view.html', post=post, files=files)

# 파일 게시판 - 자료 다운로드
@app.route('/download/<path:filename>')
def download_file(filename) :

    origin_name = request.args.get('origin_name')
    return send_from_directory('uploads/', filename, as_attachment = True, download_name = origin_name)
    # from flask import send_from_directory 필수

# 파일 게시판 - 삭제
@app.route('/filesboard/delete/<int:post_id>')
def filesboard_delete(post_id) :

    if 'user_id' not in session :
        return redirect(url_for('login'))

    # 삭제 전 작성자 확인을 위해 정보 조회
    post, _ = PostService.get_post_detail(post_id)

    if not post :
        return "<script>alert('이미 삭제된 게시글입니다.'); location.href='/filesboard';</script>"

    # 본인 확인 (또는 관리자 권한)
    if post['member_id'] != session['user_id'] and session.get('user_role') != 'admin' :
        return "<script>alert('삭제 권한이 없습니다.'); history.back();</script>"

    if PostService.delete_post(post_id) :
        return "<script>alert('성공적으로 삭제되었습니다.'); location.href='/filesboard';</script>"

    else :
        return "<script>alert('삭제 중 오류가 발생했습니다.'); history.back();</script>"

# 파일 게시판 - 수정
@app.route('/filesboard/edit/<int:post_id>', methods=['GET', 'POST'])
def filesboard_edit(post_id) :

    if 'user_id' not in session :
        return redirect(url_for('login'))

    if request.method == 'POST' :

        title = request.form.get('title')
        content = request.form.get('content')
        files = request.files.getlist('files')  # 다중 파일 가져오기

        if PostService.update_post(post_id, title, content, files) :
            return f"<script>alert('수정되었습니다.'); location.href='/filesboard/view/{post_id}';</script>"

        return "<script>alert('수정 실패'); history.back();</script>"

    # GET 요청 시 기존 데이터 로드
    post, files = PostService.get_post_detail(post_id)
    if post['member_id'] != session['user_id']:
        return "<script>alert('권한이 없습니다.'); history.back();</script>"

    return render_template('filesboard_edit.html', post=post, files=files)

# ----------------------------------------------------------------------------------------------------------------------
#                                                플라스크 실행
# ----------------------------------------------------------------------------------------------------------------------

@app.route('/') # url 생성용 코드
def index() :
    return render_template('main.html')

if __name__ == '__main__' :

    app.run(host='0.0.0.0', port=5005, debug=True)
