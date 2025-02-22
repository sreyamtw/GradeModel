from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL

app = Flask(__name__)

# Database Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '****'
app.config['MYSQL_DB'] = 'student_db'

app.secret_key = 'hello'

mysql = MySQL(app)

@app.route('/')
def home():
    if 'username' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM students WHERE admission_no = %s", (session['admission_no'],))
        student = cur.fetchone()
        cur.close()
        return render_template('home.html', student=student)
    return render_template('home.html', student=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        admission_no = data['admission_no']
        username = data['username']
        password = data['password'] 

        cur = mysql.connection.cursor()

        # Check if student exists in students table
        cur.execute("SELECT * FROM students WHERE admission_no = %s", (admission_no,))
        student = cur.fetchone()

        if not student:
            cur.close()
            return render_template('register.html', error="Admission number not found!")

        # Check if user already exists
        cur.execute("SELECT * FROM users WHERE username = %s OR admission_no = %s", (username, admission_no))
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            return render_template('register.html', error="User already exists!")

        # Insert into users table
        cur.execute("INSERT INTO users (admission_no, username, password) VALUES (%s, %s, %s)",
                    (admission_no, username, password))

        mysql.connection.commit()
        cur.close()
        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'] 

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['username'] = username
            session['admission_no'] = user[0]  # Admission number
            return redirect('/')
        return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

@app.route('/exam', methods=['GET', 'POST'])
def exam():
    if 'username' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # Check if the student already has a score
    cur.execute("SELECT score FROM scores WHERE admission_no = %s", (session['admission_no'],))
    existing_score = cur.fetchone()

    if existing_score:
        cur.close()
        return render_template('result.html', score=existing_score[0], attempted=True)  # Show existing score

    if request.method == 'POST':
        score = 0
        if request.form.get('q1') == '4': score += 1
        if request.form.get('q2') == 'Paris': score += 1

        # Save the score in the database
        cur.execute("INSERT INTO scores (admission_no, score) VALUES (%s, %s)",
                    (session['admission_no'], score))
        mysql.connection.commit()
        cur.close()

        return render_template('result.html', score=score, attempted=False)  # Show new score

    cur.close()
    return render_template('exam.html')
@app.route('/view_result')
def view_result():
    if 'username' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()
    cur.execute("SELECT score FROM scores WHERE admission_no = %s", (session['admission_no'],))
    score = cur.fetchone()
    cur.close()

    if score:
        return render_template('result.html', score=score[0], attempted=True)
    else:
        return render_template('result.html', score=None, attempted=False)


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('admission_no', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
