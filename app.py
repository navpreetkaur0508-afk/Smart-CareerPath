from flask import Flask, render_template_string, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

app = Flask(__name__)
app.secret_key = "smart-careerpath-demo-change-before-deployment"
DB_PATH = Path(__file__).with_name("careerpath.db")

CAREERS = {
    "Web Developer": {
        "skills": ["HTML", "CSS", "JavaScript", "Python", "Problem Solving"],
        "description": "Build and maintain websites and web applications.",
        "roadmap": [
            "Learn HTML and create a webpage.",
            "Practice CSS and responsive design.",
            "Learn JavaScript fundamentals.",
            "Build a website project.",
            "Learn Git and publish your project."
        ]
    },
    "Data Analyst": {
        "skills": ["Python", "SQL", "Excel", "Statistics", "Data Visualization"],
        "description": "Analyze data to discover patterns and insights.",
        "roadmap": [
            "Learn Excel and data handling.",
            "Practice Python fundamentals.",
            "Learn SQL queries.",
            "Study statistics and visualization.",
            "Build a data analysis project."
        ]
    },
    "Game Developer": {
        "skills": ["Python", "C#", "Problem Solving", "Unity", "Mathematics"],
        "description": "Develop interactive games and gameplay systems.",
        "roadmap": [
            "Strengthen programming fundamentals.",
            "Learn C# basics.",
            "Study game development concepts.",
            "Practice using Unity.",
            "Create a small playable game."
        ]
    },
    "Python Developer": {
        "skills": ["Python", "OOP", "SQL", "Flask", "Problem Solving"],
        "description": "Develop Python applications and backend systems.",
        "roadmap": [
            "Learn Python fundamentals.",
            "Practice object-oriented programming.",
            "Learn SQL and databases.",
            "Build web apps using Flask.",
            "Create and document a Python project."
        ]
    },
    "UI/UX Designer": {
        "skills": ["UI Design", "UX Research", "Wireframing", "Figma", "Creativity"],
        "description": "Design useful and user-friendly digital experiences.",
        "roadmap": [
            "Learn design principles.",
            "Study user research.",
            "Practice wireframing.",
            "Learn Figma.",
            "Create a design portfolio."
        ]
    },
    "Cybersecurity Analyst": {
        "skills": ["Networking", "Linux", "Python", "Security Basics", "Problem Solving"],
        "description": "Help protect computer systems and information.",
        "roadmap": [
            "Learn networking basics.",
            "Practice Linux fundamentals.",
            "Learn Python basics.",
            "Study defensive security concepts.",
            "Complete safe, legal security lab exercises."
        ]
    },
    "Mobile App Developer": {
        "skills": ["Programming", "UI Design", "APIs", "Databases", "Problem Solving"],
        "description": "Build applications for mobile devices.",
        "roadmap": [
            "Choose a mobile development framework.",
            "Learn programming basics.",
            "Practice mobile UI design.",
            "Connect an app to an API or database.",
            "Build a small mobile application."
        ]
    }
}

def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with get_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                career TEXT NOT NULL,
                user_skills TEXT NOT NULL,
                matched_skills TEXT NOT NULL,
                missing_skills TEXT NOT NULL,
                match_percentage INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

def get_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_db() as connection:
        return connection.execute(
            "SELECT id, name, email FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

def analyze_skills(career, skills_text):
    required = CAREERS[career]["skills"]
    entered = {
        skill.strip().casefold()
        for skill in skills_text.split(",")
        if skill.strip()
    }
    matched = [s for s in required if s.casefold() in entered]
    missing = [s for s in required if s.casefold() not in entered]
    percentage = round(len(matched) * 100 / len(required))
    return required, matched, missing, percentage

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#f3f6fc;color:#202943;font-family:Arial,sans-serif}
header{background:linear-gradient(120deg,#172554,#4f46e5);color:white;padding:24px 6%}
header h1{margin:0 0 8px}
header p{color:#e0e7ff}
nav{display:flex;gap:18px;flex-wrap:wrap}
nav a{color:white;text-decoration:none;font-weight:bold}
main{max-width:1100px;margin:28px auto;padding:0 18px}
.card{background:white;padding:23px;border-radius:15px;margin-bottom:20px;
box-shadow:0 5px 20px #17255412}
h2{color:#273575;margin-top:0}
label{display:block;font-weight:bold;margin:14px 0 7px}
input,select{width:100%;padding:12px;border:1px solid #cbd5e1;
border-radius:8px;font-size:15px}
button,.btn{display:inline-block;background:#4f46e5;color:white;border:0;
border-radius:8px;padding:11px 15px;margin-top:13px;text-decoration:none;
font-weight:bold;cursor:pointer}
button:hover,.btn:hover{background:#3730a3}
.danger{background:#dc2626}
.secondary{background:#475569}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:15px}
.stat{background:#eef2ff;border-radius:12px;padding:18px;overflow-wrap:anywhere}
.stat strong{display:block;font-size:27px;color:#3730a3;margin-bottom:6px}
.tag{display:inline-block;background:#dcfce7;color:#166534;padding:7px 10px;
border-radius:20px;margin:4px;font-size:13px}
.missing{background:#fee2e2;color:#991b1b}
.progress{height:12px;background:#e2e8f0;border-radius:20px;overflow:hidden;margin:12px 0}
.progress div{height:100%;background:#4f46e5}
.hint,.muted{color:#64748b;font-size:13px}
.flash{padding:12px;background:#dcfce7;border-radius:8px;margin-bottom:12px}
.error{background:#fee2e2}
.table-wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;min-width:620px}
th,td{padding:12px;border-bottom:1px solid #e2e8f0;text-align:left}
th{background:#eef2ff}
footer{text-align:center;color:#64748b;padding:22px}
@media(max-width:600px){header{padding:20px}main{margin:18px auto}.card{padding:17px}}
"""

PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smart CareerPath</title>
<style>""" + CSS + r"""</style>
</head>
<body>
<header>
<h1>🎯 Smart CareerPath</h1>
<p>Career Discovery | Skill Gap Analysis | Learning Roadmap</p>
<nav>
{% if user %}
<a href="{{ url_for('dashboard') }}">Dashboard</a>
<a href="{{ url_for('home') }}">New Analysis</a>
<a href="{{ url_for('recommend') }}">Career Suggestions</a>
<a href="{{ url_for('history') }}">My History</a>
<a href="{{ url_for('logout') }}">Logout</a>
{% else %}
<a href="{{ url_for('login') }}">Login</a>
<a href="{{ url_for('signup') }}">Create Account</a>
{% endif %}
</nav>
</header>
<main>
{% for category, message in get_flashed_messages(with_categories=true) %}
<div class="flash {{ 'error' if category == 'error' else '' }}">{{ message }}</div>
{% endfor %}
{{ content|safe }}
</main>
<footer>Smart CareerPath | Python, Flask and SQLite</footer>
</body>
</html>
"""

def render_page(title, content, **context):
    return render_template_string(
        PAGE, title=title, content=content, user=get_user(), **context
    )

def login_required():
    if get_user() is None:
        flash("Please log in first.", "error")
        return False
    return True

@app.route("/")
def index():
    return redirect(url_for("dashboard") if get_user() else url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if get_user():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or len(name) > 80 or "@" not in email or len(password) < 6:
            flash("Enter a valid name and email. Password must have 6 characters.", "error")
        else:
            try:
                with get_db() as connection:
                    cursor = connection.execute(
                        "INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",
                        (name, email, generate_password_hash(password))
                    )
                    session["user_id"] = cursor.lastrowid
                flash("Account created successfully.")
                return redirect(url_for("dashboard"))
            except sqlite3.IntegrityError:
                flash("This email is already registered. Please log in.", "error")

    content = """
    <div class="card" style="max-width:520px;margin:auto">
    <h2>Create Account</h2>
    <form method="post">
    <label>Full Name</label><input name="name" maxlength="80" required>
    <label>Email</label><input name="email" type="email" required>
    <label>Password (minimum 6 characters)</label>
    <input name="password" type="password" minlength="6" required>
    <button>Create Account</button>
    </form><p>Already registered? <a href="{{ url_for('login') }}">Login</a></p>
    </div>
    """
    return render_page("Sign Up", content)

@app.route("/login", methods=["GET", "POST"])
def login():
    if get_user():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as connection:
            user = connection.execute(
                "SELECT * FROM users WHERE email=?", (email,)
            ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.", "error")

    content = """
    <div class="card" style="max-width:520px;margin:auto">
    <h2>Welcome Back</h2>
    <form method="post">
    <label>Email</label><input name="email" type="email" required>
    <label>Password</label><input name="password" type="password" required>
    <button>Login</button></form>
    <p>New user? <a href="/signup">Create an account</a></p>
    </div>
    """
    return render_page("Login", content)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.")
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    user = get_user()
    with get_db() as connection:
        rows = connection.execute(
            "SELECT * FROM analyses WHERE user_id=? ORDER BY id DESC",
            (user["id"],)
        ).fetchall()

    total = len(rows)
    average = round(sum(r["match_percentage"] for r in rows) / total) if total else 0
    best = max(rows, key=lambda r: r["match_percentage"]) if rows else None
    recent = rows[:5]

    content = render_template_string(r"""
    <div class="card">
    <h2>Hello, {{ user.name }} 👋</h2>
    <p>Welcome to your personal career planning dashboard.</p>
    <a class="btn" href="{{ url_for('home') }}">Analyze My Skills</a>
    <a class="btn secondary" href="{{ url_for('recommend') }}">Find Career Suggestions</a>
    </div>
    <div class="grid">
    <div class="stat"><strong>{{ total }}</strong>Total Analyses</div>
    <div class="stat"><strong>{{ average }}%</strong>Average Match</div>
    <div class="stat"><strong>{{ best.match_percentage if best else 0 }}%</strong>Best Match</div>
    <div class="stat"><strong>{{ best.career if best else '—' }}</strong>Best-matched Career</div>
    </div>
    <div class="card"><h2>Recent Activity</h2>
    {% if recent %}
    <div class="table-wrap"><table><tr><th>Career</th><th>Match</th><th>Date</th><th>Action</th></tr>
    {% for r in recent %}
    <tr><td>{{ r.career }}</td><td>{{ r.match_percentage }}%</td><td>{{ r.created_at }}</td>
    <td><a href="{{ url_for('view_analysis',record_id=r.id) }}">View</a></td></tr>
    {% endfor %}</table></div>
    {% else %}<p>No analyses yet. Start your first analysis!</p>{% endif %}
    </div>
    """, user=user, total=total, average=average, best=best, recent=recent)
    return render_page("Dashboard", content)

@app.route("/analyze", methods=["GET", "POST"])
def home():
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip() or get_user()["name"]
        career = request.form.get("career", "")
        skills = request.form.get("skills", "").strip()

        if career not in CAREERS or len(name) > 80 or len(skills) > 1000:
            flash("Please check your inputs.", "error")
            return redirect(url_for("home"))

        _, matched, missing, percentage = analyze_skills(career, skills)
        with get_db() as connection:
            cursor = connection.execute("""
                INSERT INTO analyses
                (user_id,name,career,user_skills,matched_skills,missing_skills,
                 match_percentage,created_at)
                VALUES(?,?,?,?,?,?,?,?)
            """, (
                session["user_id"], name, career, skills,
                ", ".join(matched), ", ".join(missing), percentage,
                datetime.now().strftime("%d-%m-%Y %I:%M %p")
            ))
            record_id = cursor.lastrowid

        return redirect(url_for("view_analysis", record_id=record_id))

    content = render_template_string(r"""
    <div class="card"><h2>Career & Skill Gap Analyzer</h2>
    <p>Enter your skills to identify strengths and areas to improve.</p>
    <form method="post">
    <label>Name</label><input name="name" value="{{ user.name }}" maxlength="80" required>
    <label>Choose Career</label><select name="career" required>
    {% for career in careers %}<option value="{{ career }}">{{ career }}</option>{% endfor %}
    </select>
    <label>Your Current Skills</label>
    <input name="skills" maxlength="1000" placeholder="Python, SQL, Problem Solving">
    <p class="hint">Separate skills with commas. Leave blank if you are a beginner.</p>
    <button>Analyze My Skills</button></form></div>
    <div class="grid">{% for career, info in careers.items() %}
    <div class="card"><h3>{{ career }}</h3><p class="muted">{{ info.description }}</p>
    {% for skill in info.skills %}<span class="tag">{{ skill }}</span>{% endfor %}
    </div>{% endfor %}</div>
    """, user=get_user(), careers=CAREERS)
    return render_page("New Analysis", content)

@app.route("/analysis/<int:record_id>")
def view_analysis(record_id):
    if not login_required():
        return redirect(url_for("login"))

    with get_db() as connection:
        record = connection.execute(
            "SELECT * FROM analyses WHERE id=? AND user_id=?",
            (record_id, session["user_id"])
        ).fetchone()

    if not record:
        flash("Analysis not found.", "error")
        return redirect(url_for("history"))

    required, matched, missing, percentage = analyze_skills(
        record["career"], record["user_skills"]
    )
    info = CAREERS[record["career"]]

    content = render_template_string(r"""
    <div class="card"><h2>Analysis Results</h2>
    <p><b>{{ record.name }}</b> | Target career: <b>{{ record.career }}</b></p>
    <div class="grid">
    <div class="stat"><strong>{{ percentage }}%</strong>Skill Match</div>
    <div class="stat"><strong>{{ matched|length }}</strong>Matched Skills</div>
    <div class="stat"><strong>{{ missing|length }}</strong>Skills to Learn</div>
    </div>
    <div class="progress"><div style="width:{{ percentage }}%"></div></div>
    <h3>Skills You Have</h3>
    {% if matched %}{% for s in matched %}<span class="tag">{{ s }}</span>{% endfor %}
    {% else %}<p>No listed skills matched yet.</p>{% endif %}
    <h3>Missing Skills</h3>
    {% if missing %}{% for s in missing %}<span class="tag missing">{{ s }}</span>{% endfor %}
    {% else %}<p>All listed skills matched!</p>{% endif %}
    <h3>Learning Roadmap</h3><ol>{% for step in info.roadmap %}<li>{{ step }}</li>{% endfor %}</ol>
    <p class="hint">This rule-based score is a learning guide, not a job guarantee.</p>
    <a class="btn" href="{{ url_for('download_pdf',record_id=record.id) }}">Download PDF Report</a>
    <a class="btn secondary" href="{{ url_for('edit_analysis',record_id=record.id) }}">Edit Analysis</a>
    <a class="btn secondary" href="{{ url_for('history') }}">Back to History</a>
    </div>
    """, record=record, percentage=percentage, matched=matched,
         missing=missing, info=info)
    return render_page("Analysis Results", content)

@app.route("/history")
def history():
    if not login_required():
        return redirect(url_for("login"))

    with get_db() as connection:
        rows = connection.execute(
            "SELECT * FROM analyses WHERE user_id=? ORDER BY id DESC",
            (session["user_id"],)
        ).fetchall()

    content = render_template_string(r"""
    <div class="card"><h2>My Analysis History</h2>
    {% if rows %}<div class="table-wrap"><table>
    <tr><th>Name</th><th>Career</th><th>Match</th><th>Date</th><th>Actions</th></tr>
    {% for r in rows %}<tr>
    <td>{{ r.name }}</td><td>{{ r.career }}</td><td>{{ r.match_percentage }}%</td>
    <td>{{ r.created_at }}</td><td>
    <a href="{{ url_for('view_analysis',record_id=r.id) }}">View</a> |
    <a href="{{ url_for('edit_analysis',record_id=r.id) }}">Edit</a>
    <form style="display:inline" method="post"
    action="{{ url_for('delete_analysis',record_id=r.id) }}"
    onsubmit="return confirm('Delete this record?')">
    <button class="danger" style="padding:6px 9px">Delete</button></form>
    </td></tr>{% endfor %}</table></div>
    {% else %}<p>No saved analyses yet.</p>{% endif %}
    <a class="btn" href="{{ url_for('home') }}">New Analysis</a></div>
    """, rows=rows)
    return render_page("My History", content)

@app.route("/analysis/<int:record_id>/edit", methods=["GET", "POST"])
def edit_analysis(record_id):
    if not login_required():
        return redirect(url_for("login"))

    with get_db() as connection:
        record = connection.execute(
            "SELECT * FROM analyses WHERE id=? AND user_id=?",
            (record_id, session["user_id"])
        ).fetchone()

    if not record:
        flash("Analysis not found.", "error")
        return redirect(url_for("history"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        career = request.form.get("career", "")
        skills = request.form.get("skills", "").strip()

        if not name or len(name) > 80 or career not in CAREERS or len(skills) > 1000:
            flash("Please check the entered details.", "error")
        else:
            _, matched, missing, percentage = analyze_skills(career, skills)
            with get_db() as connection:
                connection.execute("""
                    UPDATE analyses SET name=?,career=?,user_skills=?,matched_skills=?,
                    missing_skills=?,match_percentage=?,created_at=?
                    WHERE id=? AND user_id=?
                """, (
                    name, career, skills, ", ".join(matched), ", ".join(missing),
                    percentage, datetime.now().strftime("%d-%m-%Y %I:%M %p"),
                    record_id, session["user_id"]
                ))
            flash("Analysis updated.")
            return redirect(url_for("view_analysis", record_id=record_id))

    content = render_template_string(r"""
    <div class="card"><h2>Edit Analysis</h2><form method="post">
    <label>Name</label><input name="name" value="{{ record.name }}" maxlength="80" required>
    <label>Career</label><select name="career">
    {% for career in careers %}<option value="{{ career }}"
    {% if career==record.career %}selected{% endif %}>{{ career }}</option>{% endfor %}
    </select>
    <label>Skills (comma-separated)</label>
    <input name="skills" value="{{ record.user_skills }}" maxlength="1000">
    <button>Save Changes</button></form></div>
    """, record=record, careers=CAREERS.keys())
    return render_page("Edit Analysis", content)

@app.route("/analysis/<int:record_id>/delete", methods=["POST"])
def delete_analysis(record_id):
    if not login_required():
        return redirect(url_for("login"))

    with get_db() as connection:
        connection.execute(
            "DELETE FROM analyses WHERE id=? AND user_id=?",
            (record_id, session["user_id"])
        )
    flash("Analysis deleted.")
    return redirect(url_for("history"))

@app.route("/recommend", methods=["GET", "POST"])
def recommend():
    if not login_required():
        return redirect(url_for("login"))

    suggestions = []
    entered = ""

    if request.method == "POST":
        entered = request.form.get("skills", "").strip()
        if len(entered) > 1000:
            flash("Please enter a shorter skills list.", "error")
        else:
            for career, info in CAREERS.items():
                _, matched, missing, percentage = analyze_skills(career, entered)
                suggestions.append({
                    "career": career,
                    "description": info["description"],
                    "matched": matched,
                    "missing": missing,
                    "percentage": percentage
                })
            suggestions.sort(
                key=lambda x: (x["percentage"], len(x["matched"])),
                reverse=True
            )

    content = render_template_string(r"""
    <div class="card"><h2>Career Recommendations</h2>
    <p>Enter your skills to compare your current skills with different career paths.</p>
    <form method="post"><label>Your Skills</label>
    <input name="skills" value="{{ entered }}" placeholder="Python, SQL, Problem Solving">
    <button>Find Careers</button></form></div>
    {% if suggestions %}<div class="card"><h2>Suggested Careers</h2>
    {% for s in suggestions %}<div style="padding:12px 0;border-bottom:1px solid #e2e8f0">
    <h3>{{ loop.index }}. {{ s.career }} — {{ s.percentage }}%</h3>
    <p class="muted">{{ s.description }}</p>
    <div class="progress"><div style="width:{{ s.percentage }}%"></div></div>
    <p><b>Matched:</b> {{ ", ".join(s.matched) if s.matched else "None yet" }}</p>
    <p><b>To learn:</b> {{ ", ".join(s.missing) if s.missing else "All listed skills matched" }}</p>
    </div>{% endfor %}
    <p class="hint">Suggestions are based on skill overlap, not a formal aptitude test.</p>
    {% endif %}</div>
    """, suggestions=suggestions, entered=entered)
    return render_page("Career Recommendations", content)

@app.route("/analysis/<int:record_id>/pdf")
def download_pdf(record_id):
    if not login_required():
        return redirect(url_for("login"))

    with get_db() as connection:
        record = connection.execute(
            "SELECT * FROM analyses WHERE id=? AND user_id=?",
            (record_id, session["user_id"])
        ).fetchone()

    if not record:
        flash("Analysis not found.", "error")
        return redirect(url_for("history"))

    _, matched, missing, percentage = analyze_skills(
        record["career"], record["user_skills"]
    )
    info = CAREERS[record["career"]]
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=45, leftMargin=45,
        topMargin=45, bottomMargin=45
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CareerTitle", parent=styles["Title"],
        textColor=colors.HexColor("#3730a3"), alignment=TA_CENTER
    ))

    story = [
        Paragraph("Smart CareerPath", styles["CareerTitle"]),
        Paragraph("Career &amp; Skill Gap Analysis Report", styles["Heading2"]),
        Spacer(1, 14)
    ]

    details = [
        ["Name", record["name"]],
        ["Target Career", record["career"]],
        ["Analysis Date", record["created_at"]],
        ["Skill Match", f"{percentage}%"]
    ]
    table = Table(details, colWidths=[120, 330])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef2ff")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))
    story.extend([
        table, Spacer(1, 15),
        Paragraph("Skills Entered", styles["Heading2"]),
        Paragraph(record["user_skills"] or "None entered", styles["BodyText"]),
        Spacer(1, 10),
        Paragraph("Matched Skills", styles["Heading2"]),
        Paragraph(", ".join(matched) or "None", styles["BodyText"]),
        Spacer(1, 10),
        Paragraph("Skills to Learn", styles["Heading2"]),
        Paragraph(", ".join(missing) or "All listed skills matched", styles["BodyText"]),
        Spacer(1, 10),
        Paragraph("Learning Roadmap", styles["Heading2"])
    ])

    for number, step in enumerate(info["roadmap"], start=1):
        story.append(Paragraph(f"{number}. {step}", styles["BodyText"]))
        story.append(Spacer(1, 5))

    story.extend([
        Spacer(1, 12),
        Paragraph(
            "Note: This rule-based report is a learning guide and does not guarantee employment.",
            styles["Italic"]
        )
    ])
    doc.build(story)
    buffer.seek(0)

    return send_file(
        buffer, mimetype="application/pdf", as_attachment=True,
        download_name="Smart_CareerPath_Report.pdf"
    )

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
    