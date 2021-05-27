from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import pickle

app = Flask(__name__)
model = pickle.load(open('model.pkl', 'rb'))

app.secret_key = 'rfgfsfafadfddsfsdf'

# localhost connection
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = 'arnab'
# app.config['MYSQL_DB'] = 'flaskapp'

#remote database connection
app.config['MYSQL_HOST'] = 'remotemysql.com'
app.config['MYSQL_USER'] = 'wVPpRv4UYH'
app.config['MYSQL_PASSWORD'] = 'olIen1Mv3P'
app.config['MYSQL_DB'] = 'wVPpRv4UYH'

mysql = MySQL(app)


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        # Checking sql injection
        name = username

        # Finding the length of name and password
        len_name = len(str(name))
        len_password = len(str(password))

        # Finding the number of punctuations
        punctuation_array = ["<", ">", "<=", ">=", "=", "==", "!=", "<<", ">>", "|", "&", "-", "+", "%", "^", "*"]
        cpunctuation_name = 0
        cpunctuation_password = 0
        for ch in name:
            if ch in punctuation_array:
                cpunctuation_name += 1
        for ch in password:
            if ch in punctuation_array:
                cpunctuation_password += 1

        # Finding the number of keywords
        keywords_array = ["select", "update", "insert", "create", "drop", "alter", "rename", "exec", "order", "group",
                          "sleep", "count", "where"]
        ckeywords_name = 0
        ckeywords_password = 0
        for ch in name:
            if ch in keywords_array:
                ckeywords_name += 1
        for ch in password:
            if ch in keywords_array:
                ckeywords_password += 1

        # Displaying the output
        prediction_name = model.predict([[len_name, cpunctuation_name, ckeywords_name]])
        prediction_password = model.predict([[len_password, cpunctuation_password, ckeywords_password]])
        if prediction_name == 1 or prediction_password == 1:
            msg = "You are trying sql injection attack"
            return render_template('login.html', msg=msg)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM accounts WHERE username = '" + username + "' AND password = '" + password + "';")
        # cursor.execute('SELECT * FROM accounts WHERE username = % s AND password = % s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = 'Logged in successfully !'
            cursor2 = mysql.connection.cursor()
            cursor2.execute('SELECT * FROM accounts')
            details = cursor2.fetchall()
            # print(details)
            return render_template('index.html', msg=msg, details=details)
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg=msg)


if __name__ == '__main__':
    app.run(debug=True)
