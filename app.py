import csv
import os
import random
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.', static_url_path='')

CSV_FILE = 'users.csv'

def read_users():
    users = []
    if not os.path.exists(CSV_FILE):
        return users
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append(row)
    return users

def write_user(name, email, password):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['name', 'email', 'password'])
        writer.writerow([name, email, password])

@app.route('/')
def serve_index():
    return send_from_directory('.', 'ai_resume_analyzer_job_matcher.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '')
    password = data.get('password', '')
    
    users = read_users()
    for user in users:
        if user['email'] == email and user['password'] == password:
            return jsonify({
                'success': True,
                'user': {
                    'name': user['name'],
                    'email': user['email']
                }
            })
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name', 'User')
    email = data.get('email', '')
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400
        
    users = read_users()
    for user in users:
        if user['email'] == email:
            return jsonify({'success': False, 'message': 'Email already exists'}), 409
            
    write_user(name, email, password)
    return jsonify({
        'success': True,
        'user': {
            'name': name,
            'email': email
        }
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    # Simulate a delay for the analysis
    import time
    time.sleep(2)
    
    text = request.form.get('text', '')
    roles_str = request.form.get('roles', '[]')
    import json
    roles = json.loads(roles_str) if roles_str else []
    
    # Process file if attached
    if 'file' in request.files:
        file = request.files['file']
        if file.filename.endswith('.pdf'):
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(file)
                extracted = ""
                for page in reader.pages:
                    extracted += page.extract_text() + "\n"
                text += "\n" + extracted
            except Exception as e:
                print(f"PDF extraction error: {e}")
        elif file.filename.endswith('.txt'):
            try:
                text += "\n" + file.read().decode('utf-8', errors='ignore')
            except Exception as e:
                print(f"TXT extraction error: {e}")

    text_lower = text.lower()
    
    # Define some global tech skills dictionary to check against
    all_skills = [
        "python", "javascript", "html", "css", "react", "node.js", "aws", "docker",
        "sql", "kubernetes", "typescript", "c++", "java", "tensorflow", "pytorch",
        "ci/cd", "agile", "statistics", "machine learning", "mongodb", "graphql",
        "problem solving", "communication", "apis", "git", "linux"
    ]
    
    present = []
    for s in all_skills:
        if s in text_lower:
            present.append(s.title())

    if not present:
        present = ["Problem Solving"] # Minimum fallback
    
    missing = [s.title() for s in all_skills[5:15] if s.title() not in present][:3]
    suggested = [s.title() for s in all_skills[15:20] if s.title() not in present][:3]

    if not roles:
        roles = ['Software Engineer']
        
    target = roles[0] if roles else "Software Engineer"
    
    # Dynamic ATS Score based on present skills actually found in resume
    base_score = min(50 + len(present) * 5, 99)
    if len(text.strip()) < 20: 
        base_score = 30
        
    mock_response = {
        "candidateName": "Analyzed Profile",
        "atsScore": base_score,
        "atsBreakdown": {
            "formatting": min(base_score + 5, 100),
            "keywords": min(base_score, 100),
            "experience": min(base_score + 10, 100),
            "education": min(base_score + 2, 100)
        },
        "presentSkills": present,
        "missingSkills": missing,
        "suggestedSkills": suggested,
        "jobMatches": [],
        "improvements": [
            "Quantify your achievements with concrete metrics.",
            f"Add more keywords specifically related to {target}.",
            "Use clear, action-oriented verbs at the beginning of each bullet point."
        ],
        "summary": f"A profile tailored for {target}. We extracted your file successfully and found {len(present)} targeted keywords actually present.",
        "extractedText": text.strip()[:600] + ("..." if len(text) > 600 else "")
    }
    
    for r in roles:
        mock_response["jobMatches"].append({
            "role": r,
            "match": min(base_score - random.randint(-5, 5), 100),
            "reason": f"Overlap with required skills for {r}.",
            "level": "Mid-level"
        })
        
    return jsonify(mock_response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
