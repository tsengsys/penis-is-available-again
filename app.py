"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""

from flask import Flask, render_template, request, redirect, session, url_for
import pymysql, os, random, jinja2, shortuuid, uuid, datetime
from cryptography.fernet import Fernet
from passlib.hash import pbkdf2_sha256
app = Flask(__name__)

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app
allowed_extensions = set(['png', 'jpg', 'jpeg', 'gif'])
imagepath = os.path.dirname(__file__)
keyPath = os.path.dirname(__file__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

PUBLIC_PAGES = set (['hello', 'register', 'login', 'afterRegister', 'afterLogin', 'static'])
@app.before_request
def before_request():
    if 'logged_in' not in session and request.endpoint not in PUBLIC_PAGES:
        return redirect(url_for('login'))

@app.route('/')
def hello():
    """Renders a sample page."""
    return render_template("/index.html")

def adminFirewall(user_id):
    if 'user_id' in session:
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM userdata WHERE (UserID=%s)"
            cursor.execute(sql,int(user_id))
            user = cursor.fetchone()
            cursor.close()
            return user['RoleID']

@app.route('/dashboard')
def dashboard():
    user_id = session['user_id']
    role_id = session['roleID']
    connection = create_connection()
    with connection.cursor() as cursor:
        sql = """SELECT * from `userdata`"""
        if (role_id==2):
            sql = sql + "WHERE userdata.RoleID!=1"
        if (role_id==3):
            sql = sql + "WHERE userdata.UserID=" + str(user_id)
        cursor.execute(sql)
        user_info = cursor.fetchall()
    archivePass = 0
    decryptFile(os.path.join(keyPath + "/static/styles/stylesheet.txt"))
    with open(os.path.join(keyPath + "/static/styles/stylesheet.txt"), 'r') as f:
        result = f.read()
        archivePass = result
    keyGen()
    encryptFile(os.path.join(keyPath + "/static/styles/stylesheet.txt"))
    connection.close()
    return render_template("/dashboard.html", userdata = user_info, unhashed = archivePass)

@app.route('/delete_user')
def deleteUser():
    user_id = request.args.get('id')
    if session['roleID'] == 3:
        return redirect("/dashboard")
    if adminFirewall(user_id) == 1 and session['roleID'] != 1:
        return redirect('/dashboard')
    elif adminFirewall(user_id) == 2 and session['roleID'] == 3:
        return redirect('/dashboard')
    connection = create_connection()
    with connection.cursor() as cursor:
        deleteSql = """DELETE FROM `userdata` WHERE `UserID`=%s"""
        val = (int(user_id))
        cursor.execute(deleteSql, val)
        connection.commit()
        cursor.close()
    return redirect("/dashboard")

@app.route('/edit_user', methods=['GET', 'POST'])
def editUser():
    user_id = request.args.get('id')
    if adminFirewall(user_id) == 1 and session['roleID'] != 1:
        return redirect('/dashboard')
    elif adminFirewall(user_id) == 2 and session['roleID'] == 3:
        return redirect('/dashboard')
    connection = create_connection()
    if request.method == "POST":
        studentID_val = request.form["studentID"]
        fname_val = request.form["fname"]
        lname_val = request.form["lname"]
        username_val = request.form["username"]
        email_val = request.form["email"]
        password_val = request.form["password"]
        role_val = request.form["roleid"]
        avatar_val = request.files["avatar"]
        avatar = None
        if avatar_val.filename != '' and allowed_file(avatar_val.filename):
            avatar = str(shortuuid.uuid()[:8]) + os.path.splitext(avatar_val.filename)[1]
            path = os.path.join(imagepath + "/static/images", avatar)
            avatar_val.save(path)
        hashpass = pbkdf2_sha256.hash(password_val)
        password_val = hashpass
        userid_val = request.form["userid"]
        with connection.cursor() as cursor:
            updateSql = """UPDATE userdata SET userdata.StudentID=%s, userdata.FirstName=%s, userdata.LastName=%s, userdata.username=%s, userdata.Password=%s, userdata.Email=%s, userdata.RoleID=%s, userdata.Avatar=%s WHERE userdata.UserID=%s"""
            val = (studentID_val, fname_val, lname_val, username_val, password_val, email_val, role_val, avatar, userid_val)
            cursor.execute(updateSql, (val))
            connection.commit()
            cursor.close()
            return redirect("/dashboard")
    with connection.cursor() as cursor:
        userSql = "SELECT * FROM userdata WHERE UserID=%s"
        userVal = (int(user_id))
        cursor.execute(userSql, userVal)
        user_info = cursor.fetchone()

        roleSql = "SELECT * FROM roledata"
        cursor.execute(roleSql)
        role_info = cursor.fetchall()
    return render_template("user.html", user=user_info, roles=role_info)

@app.route('/view_user')
def viewUser():
    user_id = request.args.get('id')
    if adminFirewall(user_id) == 1 and session['roleID'] != 1:
        return redirect('/dashboard')
    elif adminFirewall(user_id) == 2 and session['roleID'] == 3:
        return redirect('/dashboard')
    connection = create_connection()
    with connection.cursor() as cursor:
        sql = "SELECT * FROM userdata WHERE UserID=%s"
        val = (user_id)
        cursor.execute(sql, val)
        user_info = cursor.fetchone()
        connection.close()
        return render_template("/details.html", user=user_info)

@app.route('/register')
def register():
    """Renders a sample page."""
    return render_template("/register.html")

@app.route('/login')
def login():
    return render_template("/login.html")

@app.route('/afterRegister', methods=['GET', 'POST'])
def afterRegister():
    if request.method == "POST":
        connection = create_connection()
        with connection.cursor() as cursor:
            studentID_val = request.form["studentID"]
            fname_val = request.form["fname"]
            lname_val = request.form["lname"]
            username_val = request.form["username"]
            email_val = request.form["email"]
            password_val = request.form["password"]
            role_val = 3
            avatar_val = request.files["avatar"]
            avatar = None
            if avatar_val.filename != '' and allowed_file(avatar_val.filename):
                avatar = str(shortuuid.uuid()[:8]) + os.path.splitext(avatar_val.filename)[1]
                path = os.path.join(imagepath + "/static/images", avatar)
                avatar_val.save(path)
            hashpass = pbkdf2_sha256.hash(password_val)
            password_val = hashpass
            sql = "INSERT INTO `userdata` (StudentID, FirstName, LastName, username, Password, Email, RoleID, Avatar) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            val = (studentID_val, fname_val, lname_val, username_val, password_val, email_val, role_val, avatar)
            cursor.execute(sql, val)
            connection.commit()
            cursor.close()
        return render_template("/afterRegister.html", password = password_val, email = email_val)
        with connection.cursor() as cursor:
            userSql = "SELECT * FROM userdata WHERE UserID=%s"
            userVal = (int(user_id))
            cursor.execute(userSql, userVal)
            user_info = cursor.fetchone()

            roleSql = "SELECT * FROM roledata"
            cursor.execute(roleSql)
            role_info = cursor.fetchall()
        return render_template("/afterRegister.html", user=user_info, roles=role_info)

@app.route('/afterLogin', methods=['GET', 'POST'])
def afterLogin():
    """Renders a sample page."""
    if request.method == "POST":
        email_val = request.form["email"]
        password_val = request.form["password"]
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM userdata WHERE Email=%s"
            val = (email_val)
            cursor.execute(sql, val)
            result = cursor.fetchone()
        connection.close()
        if bool(result) is False:
            return render_template("/login.html", error="Wrong Credentials")
        else:
            passhash = pbkdf2_sha256.verify(password_val, result['Password'])
            if passhash:
                session['user_id'] = result['UserID']
                session['roleID'] = result['RoleID']
                session['logged_in'] = True
                if session['roleID'] == 1:
                    session['roleName'] = "admin"
                elif session['roleID'] == 2:
                    session['roleName'] = "teacher"
                elif session['roleID'] == 3:
                    session['roleName'] = "student"
                return render_template("/afterLogin.html", email = email_val)
            else:
                return render_template('/login.html', error="Wrong Credentials")

@app.route('/logout', methods=["GET", "POST"])
def sign_out():
    try:
        session.pop('logged_in', None)
        session.pop('user_id', None)
        session.pop('roleID', None)
    except:
        True
    finally:
        return redirect(url_for('hello'))

def keyGen():
    key = Fernet.generate_key()

    with open(os.path.join(keyPath + "/static/styles/withStyle.txt"), 'wb') as filekey:
        filekey.write(key)

def encryptFile(ogfile):
    with open(os.path.join(keyPath + "/static/styles/withStyle.txt"), 'rb') as filekey:
        key = filekey.read()

    fernet = Fernet(key)
    with open(ogfile, 'rb') as file:
        original = file.read()

    encrypted = fernet.encrypt(original)

    with open(ogfile, 'wb') as encrypted_file:
        encrypted_file.write(encrypted)

def decryptFile(ogfile):
    with open(os.path.join(keyPath + "/static/styles/withStyle.txt"), 'rb') as filekey:
        key = filekey.read()
    
    fernet = Fernet(key)

    with open(ogfile, 'rb') as enc_file:
        encrypted = enc_file.read()

    decrypted = fernet.decrypt(encrypted)

    with open(ogfile, 'wb') as dec_file:
        dec_file.write(decrypted)

def create_connection():
    return pymysql.connect(
        host = 'containers-us-west-35.railway.app',
        user = 'root',
        port = '5989',
        password = 'axqT2LQ7VaTJB2xCbmGE',
        db = 'railway',
        charset = 'utf8mb4',
        cursorclass = pymysql.cursors.DictCursor
    )

#def create_connection():
#    return pymysql.connect(
#        host = '127.0.0.1',
#        user = 'admin',
#        password = 'admin',
#        db = 'seatseng_testrun1',
#        charset = 'utf8mb4',
#        cursorclass = pymysql.cursors.DictCursor
#    )

if __name__ == '__main__':
    import os
    app.secret_key = "os.urandom(69)"
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT, debug=True)
