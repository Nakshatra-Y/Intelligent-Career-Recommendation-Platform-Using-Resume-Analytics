from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'super-secret-key-for-resume-analyzer'

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Middlewear to protect routes
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('upload'))
    return redirect(url_for('auth'))

@app.route('/auth')
def auth():
    if 'user_id' in session:
        return redirect(url_for('upload'))
    return render_template('auth.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                     (username, email, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 400
    finally:
        conn.close()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['email'] = user['email']
        return jsonify({
            'message': 'Login successful',
            'user': {
                'email': user['email'],
                'username': user['username']
            }
        }), 200
    else:
        return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth'))

@app.route('/upload')
@login_required
def upload():
    return render_template('upload.html')

@app.route('/result')
@login_required
def result():
    return render_template('result.html')

@app.route('/insights')
@login_required
def insights():
    return render_template('insights.html')

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    from parser import extract_text
    
    resume_file = request.files.get('resume')
    if not resume_file or resume_file.filename == '':
        return jsonify({'error': 'No resume uploaded'}), 400

    # Extract text content from the uploaded file
    extracted_text = extract_text(resume_file)
    print(f"Extracted Text Snippet: {extracted_text[:200]}...") # Log snippet for testing
    
    import json
    import os
    from openai import OpenAI
    
    # We use the Groq API key you provided as default
    # You can move this to secrets.toml or environment variables later
    api_key = os.environ.get("GROQ_API_KEY", "YOUR KEY")
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        
        prompt = f"""
        Analyze this resume and extract the key information precisely in JSON format.
        The JSON object must have EXACTLY these keys and follow this structure:
        {{
            "candidate_name": "Full name of the candidate",
            "skills": ["List", "of", "all", "technical", "and", "soft", "skills"],
            "education": "Brief 1-sentence summary of highest education",
            "experience": "Brief 1-2 sentence summary of work experience and years",
            "ai_summary": "A short and professional 2-3 sentence summary of the candidate's profile",
            "job_roles": ["Top 3 suggested job roles ideal for this candidate"],
            "resume_score": 85, 
            "insights": {{
                "strengths": ["List of 2-3 key professional strengths"],
                "weaknesses": ["List of 1-2 weaknesses or areas where they lack experience"],
                "missing_skills": ["List of 1-3 skills often expected for their role but missing"],
                "improvement_areas": ["List of 1-2 actionable suggestions to improve the resume or profile"]
            }}
        }}

        Note: "resume_score" MUST be an integer out of 100 based on the resume quality.
        Return ONLY the JSON object, with no other text.

        Resume text:
        {extracted_text}
        """

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Updated to current supported Groq model
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        analysis_data = json.loads(response.choices[0].message.content)
        analysis_data['extracted_text'] = extracted_text
        
        # Ensure candidate_name has a fallback if the AI couldn't find one
        if not analysis_data.get('candidate_name') or str(analysis_data['candidate_name']).strip() == "":
            analysis_data['candidate_name'] = session.get('username', 'Unknown Candidate')
            
        return jsonify(analysis_data)
        
    except Exception as e:
        print(f"Error calling AI API: {e}")
        # Fallback to mock data if API fails or parsing error occurs
        fallback_data = {
            "candidate_name": session.get('username', 'Unknown Candidate'),
            "skills": ["Analysis failed..."],
            "education": "Analysis failed...",
            "experience": "Analysis failed...",
            "ai_summary": "We couldn't analyze the resume using AI. Please try again. Error: " + str(e),
            "job_roles": ["N/A"],
            "resume_score": 0,
            "insights": {
                "strengths": ["N/A"],
                "weaknesses": ["N/A"],
                "missing_skills": ["N/A"],
                "improvement_areas": ["Verify your API key and network connection."]
            },
            "extracted_text": extracted_text
        }
        return jsonify(fallback_data)

if __name__ == '__main__':
    app.run(debug=True)
