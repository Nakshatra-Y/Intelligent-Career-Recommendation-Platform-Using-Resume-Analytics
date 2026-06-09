from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

# Load secret environment variables
load_dotenv()

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
    show_upload = request.args.get('show_upload') == '1'
    is_logged_in = 'user_id' in session
    return render_template('index.html', is_logged_in=is_logged_in, show_upload=show_upload)

@app.route('/auth')
def auth():
    if 'user_id' in session:
        return redirect(url_for('index', show_upload=1))
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
        session['photo_filename'] = user['photo_filename'] if 'photo_filename' in user.keys() else None
        return jsonify({
            'message': 'Login successful',
            'user': {
                'email': user['email'],
                'username': user['username']
            }
        }), 200
    else:
        return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db_connection()
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        username = request.form.get('username')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        linkedin_url = request.form.get('linkedin_url')
        bio = request.form.get('bio')
        current_job_title = request.form.get('current_job_title')
        current_company = request.form.get('current_company')
        years_of_experience = request.form.get('years_of_experience')
        skills = request.form.get('skills')
        
        photo = request.files.get('photo')
        
        # Get existing photo from db if not uploading a new one
        existing_user = conn.execute('SELECT photo_filename FROM users WHERE id = ?', (user_id,)).fetchone()
        photo_filename = existing_user['photo_filename'] if existing_user else None
        
        if photo and photo.filename:
            import werkzeug.utils
            filename = werkzeug.utils.secure_filename(f"{user_id}_{photo.filename}")
            upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'profiles')
            os.makedirs(upload_folder, exist_ok=True)
            photo.save(os.path.join(upload_folder, filename))
            photo_filename = filename
        
        if username:
            conn.execute('''
                UPDATE users 
                SET username = ?, full_name = ?, phone = ?, linkedin_url = ?, bio = ?,
                    current_job_title = ?, current_company = ?, years_of_experience = ?, skills = ?, photo_filename = ?
                WHERE id = ?
            ''', (username, full_name, phone, linkedin_url, bio, current_job_title, current_company, years_of_experience, skills, photo_filename, user_id))
            conn.commit()
            session['username'] = username
            session['photo_filename'] = photo_filename
            
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    return render_template('profile.html', user=user, username=session.get('username'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth'))

@app.route('/upload')
@login_required
def upload():
    # Backwards compatibility: redirect any old links to the unified index page
    return redirect(url_for('index'))

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    from parser import extract_text
    
    resume_file = request.files.get('resume')
    if not resume_file or resume_file.filename == '':
        # If no file is uploaded, redirect back to upload page
        return redirect(url_for('upload'))

    # Extract text content from the uploaded file
    extracted_text = extract_text(resume_file)
    print(f"Extracted Text Snippet: {extracted_text[:200]}...") # Log snippet for testing
    
    import json
    import os
    from openai import OpenAI
    
    # We use the Groq API key you provided as default
    # You can move this to secrets.toml or environment variables later
    api_key = os.environ.get("GROQ_API_KEY", "your_groq_api_key_here")
    
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
            }},
            "recommended_jobs": [
                {{
                    "title": "Job Title 1",
                    "company": "Example Company",
                    "location": "City / Remote",
                    "apply_link": "https://example.com/apply-link"
                }}
            ]
        }}

        Notes:
        - "resume_score" MUST be an integer out of 100 based on the resume quality.
        - "recommended_jobs" MUST be a list of 3-6 realistic job objects tailored to the candidate.
        - Return ONLY the JSON object, with no other text.

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
        
    except Exception as e:
        print(f"Error calling AI API: {e}")
        # Fallback to mock data if API fails or parsing error occurs
        analysis_data = {
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
            "recommended_jobs": [
                {
                    "title": "Sample Role",
                    "company": "Demo Company",
                    "location": "Remote",
                    "apply_link": "https://www.linkedin.com/jobs"
                }
            ],
            "extracted_text": extracted_text
        }

    # Ensure candidate_name has a fallback if the AI couldn't find one
    if not analysis_data.get('candidate_name') or str(analysis_data['candidate_name']).strip() == "":
        analysis_data['candidate_name'] = session.get('username', 'Unknown Candidate')

    # Normalize insights structure
    insights = analysis_data.get('insights') or {}
    strengths = insights.get('strengths') or []
    weaknesses = insights.get('weaknesses') or []
    missing_skills = insights.get('missing_skills') or []
    improvement_areas = insights.get('improvement_areas') or []

    # Save data to session for the jobs page
    session['job_roles'] = analysis_data.get('job_roles') or []
    session['skills'] = analysis_data.get('skills') or []
    session['extracted_text'] = extracted_text

    source = request.form.get('source')
    if source == 'jobs':
        flash("Resume analyzed! Here are your tailored job matches.", "success")
        job_roles = analysis_data.get('job_roles') or []
        default_query = job_roles[0] if job_roles else ""
        return redirect(url_for('jobs', query=default_query))

    return render_template(
        'result.html',
        username=session.get('username'),
        candidate_name=analysis_data.get('candidate_name'),
        education=analysis_data.get('education'),
        experience=analysis_data.get('experience'),
        ai_summary=analysis_data.get('ai_summary'),
        skills=analysis_data.get('skills') or [],
        resume_score=analysis_data.get('resume_score') or 0,
        job_roles=analysis_data.get('job_roles') or [],
        strengths=strengths,
        weaknesses=weaknesses,
        missing_skills=missing_skills,
        improvement_areas=improvement_areas,
        extracted_text=extracted_text
    )

@app.route('/jobs')
@login_required
def jobs():
    import requests
    
    search_query = request.args.get('query')
    min_salary_filter = request.args.get('min_salary', 0, type=int)
    location_filter = request.args.get('location', 'India')
    emp_type_filter = request.args.get('emp_type')
    remote_filter = request.args.get('remote')
    
    # Get suggested roles from session
    job_roles = session.get('job_roles', [])
    skills = session.get('skills', [])
    
    query = search_query
        
    rapidapi_key = os.environ.get("RAPIDAPI_KEY", "")
    if not rapidapi_key:
        print("WARNING: RAPIDAPI_KEY is not set or empty!")
        flash("RapidAPI Key is missing. Live job search is disabled.", "error")
    
    recommended_jobs = []
    
    if query and rapidapi_key:
        api_query = query
        if location_filter:
            api_query += f" in {location_filter}"
            
        url = "https://jsearch.p.rapidapi.com/search"
        querystring = {
            "query": api_query, 
            "page": "1", 
            "num_pages": "1"
        }
        
        if emp_type_filter:
            querystring["employment_types"] = emp_type_filter
            
        if remote_filter == 'on':
            querystring["remote_jobs_only"] = "true"
            
        headers = {
            "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY", ""),
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        try:
            response = requests.get(url, headers=headers, params=querystring)
            data = response.json()
            
            # Debugging JSearch response
            print(f"JSearch Response Status: {response.status_code}")
            if response.status_code != 200 or 'message' in data:
                print(f"JSearch API Error: {data.get('message', 'Unknown Error')}")
                flash(f"Job Search API Error: {data.get('message', 'Unknown Error')}. Please check your RapidAPI Key.", "error")
            
            if 'data' in data:
                for job in data['data']:
                    job_min_salary = job.get('job_min_salary')
                    job_max_salary = job.get('job_max_salary')
                    
                    if min_salary_filter > 0:
                        if job_max_salary is not None and job_max_salary < min_salary_filter:
                            continue
                        elif job_max_salary is None and job_min_salary is not None and job_min_salary < min_salary_filter:
                            continue
                        elif job_max_salary is None and job_min_salary is None:
                            continue

                    # Extract location intelligently
                    city = job.get('job_city')
                    state = job.get('job_state')
                    country = job.get('job_country')
                    location_parts = [p for p in [city, state, country] if p]
                    location_str = ", ".join(location_parts) if location_parts else "Location N/A"

                    # Calculate a dynamic Match Percentage based on user's skills
                    job_desc_lower = job.get('job_description', '').lower()
                    match_score = 0
                    matched_skills_list = []
                    if skills and isinstance(skills, list):
                        for skill in skills:
                            if str(skill).lower() in job_desc_lower:
                                match_score += 1
                                matched_skills_list.append(skill)
                        
                        # Calculate percentage, give a baseline boost so it feels realistic and encouraging
                        if len(skills) > 0:
                            raw_percent = (match_score / len(skills)) * 100
                            match_percentage = min(int(raw_percent * 0.5 + 50), 99) # Range roughly 50% - 99%
                        else:
                            match_percentage = 85
                    else:
                        match_percentage = 85

                    recommended_jobs.append({
                        "title": job.get('job_title', 'Unknown Title'),
                        "company": job.get('employer_name', 'Unknown Company'),
                        "location": location_str,
                        "apply_link": job.get('job_apply_link', '#'),
                        "match_percentage": match_percentage, 
                        "matched_skills": matched_skills_list,
                        "description": job.get('job_description', '')[:300] + "...",
                        "employment_type": job.get('job_employment_type', 'N/A').replace("_", " ").title(),
                        "is_remote": job.get('job_is_remote', False),
                        "min_salary": job_min_salary,
                        "max_salary": job_max_salary,
                        "salary_currency": job.get('job_salary_currency', 'USD')
                    })
        except Exception as e:
            print(f"Error calling J Search API: {e}")
    else:
        # Fallback if no API key is provided
        print("No RAPIDAPI_KEY found in .env")

    return render_template(
        'jobs.html',
        username=session.get('username'),
        recommended_jobs=recommended_jobs,
        job_roles=job_roles,
        current_query=query,
        current_min_salary=min_salary_filter
    )

@app.route('/cover_letter', methods=['GET', 'POST'])
@login_required
def cover_letter():
    job_title = ''
    company = ''
    job_description = ''
    
    if request.method == 'POST':
        job_title = request.form.get('job_title', '')
        company = request.form.get('company', '')
        job_description = request.form.get('job_description', '')
        
    return render_template(
        'cover_letter.html',
        username=session.get('username'),
        job_title=job_title,
        company=company,
        job_description=job_description
    )

@app.route('/generate_cover_letter', methods=['POST'])
@login_required
def generate_cover_letter():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    job_title = data.get('job_title', '')
    company = data.get('company', '')
    job_description = data.get('job_description', '')
    user_answers = data.get('user_answers', '')
    resume_text = data.get('resume_text', '')
    
    import os
    from openai import OpenAI
    
    api_key = os.environ.get("GROQ_API_KEY", "your_groq_api_key_here")
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        
        prompt = f"""
        You are an expert career coach and professional copywriter. 
        Write a compelling, tailored cover letter for a candidate applying for the "{job_title}" position at {company}.
        
        Here is the job description:
        {job_description}
        
        Here is the candidate's resume:
        {resume_text}
        
        Here are some specific details the candidate wants to include or highlight (their answers to some questions):
        {user_answers}
        
        Guidelines:
        - Make it professional, concise, and engaging.
        - Start with a strong opening statement.
        - Highlight the candidate's most relevant skills and experiences based on their resume and the job description.
        - Naturally weave in the specific details they provided.
        - Keep it to 3-4 paragraphs.
        - Output ONLY the cover letter text.
        """
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        cover_letter = response.choices[0].message.content
        return jsonify({'cover_letter': cover_letter})
        
    except Exception as e:
        print(f"Error generating cover letter: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_cover_letter', methods=['POST'])
@login_required
def download_cover_letter():
    from flask import send_file
    import docx
    from io import BytesIO
    
    cover_letter_text = request.form.get('cover_letter_text', '')
    if not cover_letter_text:
        return "No text provided", 400
        
    doc = docx.Document()
    
    # Split by double newline to create paragraphs
    paragraphs = cover_letter_text.split('\n\n')
    for p in paragraphs:
        if p.strip():
            doc.add_paragraph(p.strip())
    
    file_stream = BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    
    return send_file(
        file_stream,
        as_attachment=True,
        download_name='Cover_Letter.docx',
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

if __name__ == '__main__':
    app.run(debug=True)
