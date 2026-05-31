# Luxaura AI — Frontend Templates

> Dark Medical Futuristic / Biopunk Clinical UI  
> Flask + Jinja2 · Font Awesome 6.5 · VGG16 skin-lesion classifier

---

## 📁 Project Structure

```
project/
├── static/
│   └── style.css          ← Design system (all variables, components)
├── templates/
│   ├── login.html          ← Authentication — redesigned centered card
│   ├── signup.html         ← Registration with password strength meter
│   ├── forget_password.html← Password recovery
│   ├── dashboard.html      ← Main dashboard (stats, priority patients, AI info)
│   ├── predict.html        ← Upload & run dermoscopy analysis
│   ├── result.html         ← Diagnosis result with risk gauge
│   ├── patients.html       ← Patient database table
│   ├── notifications.html  ← Notification centre
│   └── settings.html       ← Account & system preferences
└── README.md
```

---

## 🎨 Design System

All design tokens live in `style.css` under `:root`. The palette is:

| Token | Value | Role |
|---|---|---|
| `--cyan` | `#ff2d7d` | Primary accent (pink-magenta) |
| `--teal` | `#00d4ff` | Secondary accent (electric blue) |
| `--danger` | `#ff4560` | Alerts / malignant |
| `--success` | `#00e5a0` | Confirmed / benign |
| `--warning` | `#ffb547` | Moderate risk |
| `--bg-void` | `#050a0f` | Page background |

Typography: **Syne** (display/headings) + **DM Sans** (body) — loaded from Google Fonts.

---

## 📸 Captures d’écran

Les captures d’écran suivantes montrent l’interface principale de la plateforme. Placez vos images dans le dossier `screenshots/` et remplacez les noms de fichiers si nécessaire.

### Page de connexion

![Capture d'écran de la page de connexion](screenshots/login.png)

### Tableau de bord

![Capture d'écran du dashboard](screenshots/dashboard.png)

### Données patients

![Capture d'écran de la page patients](screenshots/patients.png)

### Lancement d’une nouvelle analyse

![Capture d'écran de la page de nouvelle analyse](screenshots/new_analysis.png)

### Centre de notifications

![Capture d'écran du centre de notifications](screenshots/notifications.png)

### Configuration

![Capture d'écran de la page de configuration](screenshots/settings.png)

### Assistant médical AI

![Capture d'écran de l'assistant médical AI](screenshots/assistant.png)



---

## �🔄 Login Page — v2 Redesign

`login.html` was redesigned from a **two-column split layout** into a **full-page immersive background + centered glass card**:

### What changed
- The left brand panel is now a **fixed full-viewport background** with animated ambient glow blobs, pulsing rings, a floating logo (top-left), a descriptor strip (bottom-left), and stat counters (bottom-center).
- The right form panel becomes a **frosted-glass card** centered on screen using `backdrop-filter: blur(24px)`.
- The card features a **top-edge scanning glow line** that animates left-to-right.
- The submit button uses a **animated gradient shift** (pink → magenta → teal loop).
- A **ping ring animation** on the avatar icon adds depth on load.
- All other pages (`signup.html`, `forget_password.html`, etc.) retain the original two-column layout and are **not affected**.

### Files modified
| File | Change |
|---|---|
| `login.html` | Full redesign — scoped `<style>` block, no changes to `style.css` |

---

## ⚙️ Flask Integration

All templates use Jinja2 template syntax and expect the following from Flask:

### Routes expected

| Template | Route name | Session / context vars |
|---|---|---|
| `login.html` | `login` | flash messages |
| `signup.html` | `signup` | flash messages |
| `forget_password.html` | `forgot_password` | flash messages |
| `dashboard.html` | `dashboard` | `session['user']`, `session['role']`, `patients_count`, `analyses_count`, `priority_patients`, `notif_unread`, `notifications` |
| `predict.html` | `predict` | `session['user']`, `session['role']` |
| `result.html` | `result` | `session['user']`, `result`, `prob`, `img` |
| `patients.html` | `patients` | `patients` list of `{name, age, result, probability, image_path}` |
| `notifications.html` | `notifications_page` | — |
| `settings.html` | `settings` | — |

### Minimum Flask app skeleton

```python
from flask import Flask, render_template, session, redirect, url_for, flash, request

app = Flask(__name__)
app.secret_key = 'change-me'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # validate credentials
        session['user'] = request.form['username']
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html',
        patients_count=0,
        analyses_count=0,
        priority_patients=[],
        notif_unread=0,
        notifications=[]
    )
```

---

## 🚀 Quick Start

```bash
# 1. Clone / copy files into your Flask project
cp login.html signup.html forget_password.html \
   dashboard.html predict.html result.html \
   patients.html notifications.html settings.html \
   templates/

cp style.css static/

# 2. Install Flask
pip install flask

# 3. Run
flask run
```

---

## 📝 Notes

- **CAPTCHA** is a front-end-only mock (click to toggle). Replace with real reCAPTCHA in production.
- **AI model stats** (97.4% accuracy) are hard-coded in the HTML for display purposes; wire them to your Flask context for live values.
- The `style.css` uses `--cyan` mapped to `#ff2d7d` (pink-magenta) — this is intentional per the original design system.
- All pages are responsive down to ~480px. Sidebar collapses to hidden on small screens.

---

## 📄 License

Internal project — all rights reserved.
