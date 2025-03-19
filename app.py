from flask import Flask, render_template, request, redirect, session
import mysql.connector
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch

app = Flask(__name__)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'pwd',
    'database': 'student_db'
}

app.secret_key = 'hello'

def get_db_connection():
    return mysql.connector.connect(**db_config)

MODEL_PATH = "t5_finetuned_grading"
tokenizer = T5Tokenizer.from_pretrained(MODEL_PATH)
model = T5ForConditionalGeneration.from_pretrained(MODEL_PATH)

# Define multiple exam questions
QUESTIONS = [
    "What is k-means clustering?",
    "Explain the concept of inheritance in Object-Oriented Programming."
]

def grade_answer(question, student_answer):
    """Generates a score and feedback for a given student answer."""
    input_text = f"Grade the following answer like a data science teacher grading an exam:\nQuestion: {question}\nStudent Answer: {student_answer}"

    print("📌 Model Input:", input_text)  # Debugging line
    
    inputs = tokenizer(input_text, return_tensors="pt", padding=True, truncation=True)
    
    with torch.no_grad():
        outputs = model.generate(**inputs, max_length=100)  # Adjusted length for better responses
    
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return result

@app.route('/')
def home():
    if 'username' in session:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE admission_no = %s", (session['admission_no'],))
        student = cur.fetchone()
        cur.close()
        conn.close()
        return render_template('home.html', student=student)
    return render_template('home.html', student=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        admission_no = data['admission_no']
        username = data['username']
        password = data['password']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM students WHERE admission_no = %s", (admission_no,))
        student = cur.fetchone()

        if not student:
            cur.close()
            conn.close()
            return render_template('register.html', error="Admission number not found!")

        cur.execute("SELECT * FROM users WHERE username = %s OR admission_no = %s", (username, admission_no))
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            conn.close()
            return render_template('register.html', error="User already exists!")

        cur.execute("INSERT INTO users (admission_no, username, password) VALUES (%s, %s, %s)",
                    (admission_no, username, password))

        conn.commit()
        cur.close()
        conn.close()
        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session['username'] = username
            session['admission_no'] = user[0]
            return redirect('/')
        return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

@app.route('/exam', methods=['GET', 'POST'])
def exam():
    if 'username' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT score FROM scores WHERE admission_no = %s", (session['admission_no'],))
    existing_score = cur.fetchone()

    if existing_score:
        cur.close()
        conn.close()
        return render_template('result.html', score=existing_score[0], attempted=True)

    if request.method == 'POST':
        score = 0
        if request.form.get('q1') == 'A location in memory to store data': score += 1
        if request.form.get('q2') == 'x = 4': score += 1
        if request.form.get('q3') == '#': score += 1
        if request.form.get('q4') == 'Blueprint for creating objects': score += 1
        if request.form.get('q5') == 'Improved code organization': score += 1

        cur.execute("INSERT INTO scores (admission_no, score) VALUES (%s, %s)",
                    (session['admission_no'], score))
        conn.commit()
        cur.close()
        conn.close()

        return render_template('result.html', score=score, attempted=False)

    cur.close()
    conn.close()
    return render_template('exam.html')

@app.route('/exam1')
def exam1():
    return render_template('exam1.html', questions=QUESTIONS)

@app.route('/submit', methods=['POST'])
def submit():
    student_answers = [request.form.get(f'answer_{i}') for i in range(len(QUESTIONS))]

    print("🔍 Collected Answers:", student_answers)  # Debugging line
    conn = get_db_connection()
    cur = conn.cursor()

    results = []
    for i, answer in enumerate(student_answers):
        conn = get_db_connection()
        cur = conn.cursor()
        if not answer or answer.strip() == "":
            score, feedback_text = "N/A", "No answer provided."
        else:
            feedback = grade_answer(QUESTIONS[i], answer)
            print(f"🔹 Model Raw Output (Q{i+1}): {feedback}")  # Debugging line
            score, feedback_text = feedback.split('|', 1) if '|' in feedback else ("N/A", feedback)

        results.append({"question": QUESTIONS[i], "answer": answer, "score": score.strip(), "feedback": feedback_text.strip()})

        cur.execute(
            "INSERT INTO subjective_scores (admission_no, question, answer, score, feedback) VALUES (%s, %s, %s, %s, %s)",
            (session['admission_no'], QUESTIONS[i], answer, score.strip(), feedback_text.strip())
        )

        conn.commit()
        cur.close()
        conn.close()
    return render_template('result1.html', results=results)


@app.route('/view_result')
def view_result():
    if 'username' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT score FROM scores WHERE admission_no = %s", (session['admission_no'],))
    score = cur.fetchone()
    cur.close()
    conn.close()

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
    app.run()

