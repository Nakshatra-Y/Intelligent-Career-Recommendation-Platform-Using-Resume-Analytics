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

    # Build recommended jobs by scraping LinkedIn based on job roles
    job_roles = analysis_data.get('job_roles') or []
    recommended_jobs = []
    
    try:
        from scraper import get_job_recommendations
        # Sanitize roles to avoid OSError on Windows
        clean_roles = []
        for role in job_roles:
            cr = "".join([c for c in str(role) if ord(c) < 128 and (c.isalnum() or c in (' ', '-', '.'))]).strip()
            if cr: clean_roles.append(cr)
            
        if not clean_roles:
            clean_roles = ["Software Engineer"]
            
        print(f"Scraping jobs for roles: {clean_roles[:3]} in India")
        
        # Extract top 10 skills for better matching source
        top_skills = (analysis_data.get('skills') or [])[:10]
        
        scraped_jobs = get_job_recommendations(clean_roles, extracted_text, top_skills=top_skills, location="India", max_jobs=20)
        
        for j in scraped_jobs:
            recommended_jobs.append({
                "title": j.get('title', 'Unknown Title'),
                "company": j.get('company', 'Unknown Company'),
                "location": j.get('location', 'Location N/A'),
                "apply_link": j.get('link', '#'),
                "match_percentage": j.get('match_percentage', 0),
                "description": j.get('description', ''),
                "matched_skills": j.get('matched_skills', [])
            })
            
    except Exception as e:
        print(f"Scraper error caught in app.py logic: {e}")
        import traceback
        traceback.print_exc()

    # Ensure at least 15 jobs if possible, filling with fallback if scraper returned fewer
    if len(recommended_jobs) < 15:
        ai_jobs = analysis_data.get('recommended_jobs') or []
        temp_jobs = []
        
        # 1. Try to add AI recommended jobs first if they aren't already there
        existing_titles = {rj['title'].lower() for rj in recommended_jobs}
        for aj in ai_jobs:
            title = aj.get('title', 'Role')
            if title.lower() not in existing_titles:
                temp_jobs.append({
                    "title": title,
                    "company": aj.get('company', 'Potential Match'),
                    "location": aj.get('location', 'Remote'),
                    "link": aj.get('apply_link', 'https://www.linkedin.com/jobs'),
                    "description": f"Exciting opportunity for a {title} to contribute to innovative projects and drive impact."
                })
        
        # 2. If still under 15, generate from the job_roles suggested by AI
        if len(recommended_jobs) + len(temp_jobs) < 15:
            base_companies = ["TCS", "Infosys", "Wipro", "Google", "Amazon", "Microsoft", "Accenture", "Capgemini", "Cognizant"]
            base_locations = ["Bengaluru", "Pune", "Hyderabad", "Mumbai", "Chennai", "Remote"]
            
            # Use all suggested job roles to fill up to 15
            target_fill = 15 - (len(recommended_jobs) + len(temp_jobs))
            for i in range(target_fill):
                role = job_roles[i % len(job_roles)] if job_roles else "Software Engineer"
                temp_jobs.append({
                    "title": f"Entry Level {role}" if i > 5 else role,
                    "company": base_companies[i % len(base_companies)],
                    "location": base_locations[i % len(base_locations)],
                    "link": f"https://www.linkedin.com/jobs/search?keywords={str(role).replace(' ', '%20')}",
                    "description": f"Develop high-quality software solutions and collaborate with expert teams as a {role}."
                })
        
        # 3. Apply matching logic to these fallback jobs and add them
        if temp_jobs:
            from scraper import match_resume_with_jobs
            top_skills = (analysis_data.get('skills') or [])[:10]
            processed_fallbacks = match_resume_with_jobs(extracted_text, temp_jobs, top_skills=top_skills)
            for pf in processed_fallbacks:
                recommended_jobs.append({
                    "title": pf['title'],
                    "company": pf['company'],
                    "location": pf['location'],
                    "apply_link": pf.get('link', pf.get('apply_link', '#')),
                    "match_percentage": pf['match_percentage'],
                    "description": pf.get('description', ''),
                    "matched_skills": pf.get('matched_skills', [])
                })
    
    # Final trim to top 20 max
    recommended_jobs = recommended_jobs[:20]

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
        recommended_jobs=recommended_jobs
    )

if __name__ == '__main__':
    app.run(debug=True)
