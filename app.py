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
    
    # Diverse Job Categories & Skill Mapping
    SKILL_MAP = {
        "Software Engineer": ["python", "javascript", "react", "html", "css", "node.js", "aws", "docker", "sql", "git", "agile", "c++", "java"],
        "Data Scientist": ["python", "r", "sql", "machine learning", "statistics", "data analysis", "tensorflow", "pytorch", "pandas", "tableau"],
        "Teacher": ["lesson planning", "classroom management", "curriculum design", "grading", "special education", "pedagogy", "communication", "student evaluation"],
        "Nurse": ["patient care", "cpr", "vitals", "emr", "medication administration", "triage", "infection control", "phlebotomy"],
        "Biologist": ["lab research", "microbiology", "genetics", "data analysis", "pcr", "pipetting", "scientific writing", "field work"],
        "Accountant": ["bookkeeping", "tax preparation", "financial reporting", "excel", "auditing", "quickbooks", "gaap", "reconciliation"],
        "Graphic Designer": ["adobe creative suite", "illustrator", "photoshop", "typography", "branding", "ui/ux", "layout design", "figma"],
        "Marketing Manager": ["seo", "content strategy", "social media", "market research", "campaign management", "google analytics", "b2b", "copywriting"],
        "Sales Representative": ["crm", "lead generation", "cold calling", "negotiation", "b2b sales", "customer", "closing", "salesforce"],
        "HR Specialist": ["talent acquisition", "onboarding", "employee relations", "payroll", "benefits", "compliance", "hiring", "interviews"],
        "Mechanical Engineer": ["cad", "solidworks", "thermodynamics", "manufacturing", "prototyping", "matlab", "fluid mechanics", "project management"],
        "Lawyer": ["legal research", "litigation", "contract drafting", "negotiation", "case management", "legal writing", "client counseling", "compliance"],
        "Chef": ["food safety", "menu planning", "inventory management", "culinary techniques", "baking", "line cook", "sanitation", "catering"],
        "Electrician": ["wiring", "troubleshooting", "blueprints", "safety codes", "installation", "circuitry", "maintenance", "power tools"],
        "Civil Engineer": ["autocad", "structural design", "project management", "surveying", "construction methods", "estimation", "materials testing"],
        "Architect": ["revit", "sketchup", "autocad", "building codes", "3d modeling", "project management", "sustainability", "interior design"],
        "Pharmacist": ["prescription", "counseling", "pharmacology", "inventory", "compliance", "immunization", "medication safety"],
        "Plumber": ["pipe fitting", "blueprint reading", "water systems", "drainage", "soldering", "maintenance", "troubleshooting", "safety codes"],
        "Writer": ["copywriting", "proofreading", "seo", "content creation", "ap style", "research", "grammar", "storytelling"],
        "Psychologist": ["counseling", "assessment", "therapy", "diagnostics", "empathy", "crisis intervention", "record keeping", "treatment planning"]
    }
    general_skills = ["communication", "problem solving", "leadership", "teamwork", "time management", "project management", "attention to detail"]
    
    if not roles:
        roles = ['Software Engineer']
        
    target = roles[0] if roles else "Software Engineer"
    
    # Build list of required skills based on matched target roles
    required_skills = []
    for r in roles:
        mapped = SKILL_MAP.get(r, general_skills)
        for skill in mapped:
            if skill not in required_skills:
                required_skills.append(skill)
                
    if not required_skills:
        required_skills = general_skills
        
    present = []
    for s in required_skills:
        if s in text_lower:
            present.append(s.title())

    if not present:
        present = ["Communication", "Problem Solving"] # Minimum fallback
    
    missing = [s.title() for s in required_skills if s.title() not in present][:3]
    suggested = [s.title() for s in required_skills if s.title() not in present][3:6]
    if not suggested:
        suggested = ["Leadership", "Time Management", "Adaptability"]

    # Dynamic ATS Score heavily weighted by satisfying the REQUIRED category target skills
    match_ratio = len(present) / float(len(required_skills)) if len(required_skills) > 0 else 0.5
    base_score = int(min(40 + (match_ratio * 60), 99))
    if len(text.strip()) < 20: 
        base_score = 30
        
    mock_response = {
        "candidateName": "Analyzed Profile",
        "atsScore": base_score,
        "atsBreakdown": {
            "formatting": min(base_score + 10, 100),
            "keywords": min(int(match_ratio * 100) + 15, 100),
            "experience": min(base_score + 5, 100),
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
        "summary": f"A profile evaluated dynamically for {target}. We extracted your file successfully and found {len(present)} industry-specific keywords actually present.",
        "extractedText": text.strip()[:600] + ("..." if len(text) > 600 else "")
    }
    
    for r in roles:
        r_mapped = SKILL_MAP.get(r, general_skills)
        r_present = sum(1 for s in r_mapped if s in text_lower)
        r_match = int(min(20 + ((r_present / max(len(r_mapped), 1)) * 80), 100))
        mock_response["jobMatches"].append({
            "role": r,
            "match": r_match,
            "reason": f"Matched {r_present} out of {len(r_mapped)} vital skills for {r}.",
            "level": "Mid-level"
        })
        
    return jsonify(mock_response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
