from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
import re
import md5

app = Flask(__name__)
app.secret_key = 'root'
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
mysql = MySQLConnector(app,'the_wall')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def create():
    query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :password, NOW(), NOW())"
    data = {
        'first_name': request.form['first_name'],
        'last_name': request.form['last_name'],
        'email': request.form['email'],
        'password': md5.new(request.form['password']).hexdigest()
    }

    check = "SELECT email FROM users"
    
    email = request.form['email']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    for i in (mysql.query_db(check)):
        if i['email'] == email:
            flash("Email already in database")
            return redirect('/')
    if len(email) < 1:
        flash("Email cannot be empty!")
        return redirect('/')
    elif not EMAIL_REGEX.match(email):
        flash("Invalid Email Address!")
        return redirect('/')
    elif len(first_name) < 1:
        flash("First name cannot be empty!")
        return redirect('/')
    elif any(i.isdigit() for i in first_name) == True:
        flash("Invalid first name!")
        return redirect('/')
    elif len(last_name) < 1:
        flash("Last name cannot be empty!")
        return redirect('/')
    elif any(i.isdigit() for i in last_name) == True:
        flash("Invalid last name!")
        return redirect('/')
    elif len(password) < 8:
        flash("Password must contain at least eight characters!")
        return redirect('/')
    elif confirm_password != password:
        flash("Passwords must match!")
        return redirect('/')
    else:
        flash("Successfully Registered!")
        mysql.query_db(query, data)
        return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    query = "SELECT * FROM users WHERE email = :email"
    data = {
        'email': request.form['email']
    }
    users = mysql.query_db(query, data)

    if len(users) > 0:
        user = users[0]
        if user['password'] == md5.new(request.form['password']).hexdigest():
            session['logged_id'] = user['id']
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            return redirect("/wall")
        else:
            flash("Password doesn't match")
            return redirect('/')
    else: 
        flash ('No username found')
        return redirect('/')

@app.route("/wall")
def wall():
    message_query = "SELECT messages.id, messages.user_id, messages.message, messages.created_at, CONCAT(first_name, ' ', last_name) AS full_name FROM messages JOIN users ON messages.user_id = users.id ORDER BY messages.id DESC"
    messages = mysql.query_db(message_query)
    comment_query = "SELECT comments.id, comments.message_id, comments.user_id, comments.comment, comments.created_at, CONCAT(first_name, ' ', last_name) AS full_name FROM comments JOIN users ON comments.user_id = users.id JOIN messages ON comments.message_id = messages.id ORDER BY comments.id DESC"
    comments = mysql.query_db(comment_query)
    return render_template('wall.html', all_messages = messages, all_comments = comments)

@app.route('/clear')
def clear():
    session.clear()
    return redirect('/')

@app.route('/post_message', methods=['GET', 'POST'])
def post_message():
    query = "INSERT INTO messages (user_id, message, created_at, updated_at) VALUES (:user_id, :message, NOW(), NOW())"
    data = {
        'message': request.form['message_input'],
        'user_id': session['logged_id']
    }
    mysql.query_db(query, data)
    return redirect('/wall')

@app.route('/remove_message', methods=['GET', 'POST'])
def delete_message():
    comments_query = "DELETE FROM comments WHERE comments.message_id = :message_id"
    message_query = "DELETE FROM messages WHERE messages.id = :message_id"
    data = {
        'message_id': int(request.form['get_m_id'])
    }
    mysql.query_db(comments_query, data)
    mysql.query_db(message_query, data)
    return redirect('/wall')

@app.route('/post_comment', methods=['GET', 'POST'])
def post_comment():
    query = "INSERT INTO comments (message_id, user_id, comment, created_at, updated_at) VALUES (:message_id, :user_id, :comment, NOW(), NOW())"
    data = {
        'comment': request.form['comment_input'],
        'message_id': request.form['get_m_id'],
        'user_id': session['logged_id']
    }
    mysql.query_db(query, data)
    return redirect('/wall')

app.run(debug=True)