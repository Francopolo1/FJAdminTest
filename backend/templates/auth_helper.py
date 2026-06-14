def auth_page(title, icon_svg, heading, subheading, content, footer=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>{title} — FJADMIN</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Sora:wght@600&display=swap" rel="stylesheet"/>
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Inter',sans-serif;background:#0F172A;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:1.5rem}}
    .bg-glow{{position:fixed;width:500px;height:500px;border-radius:50%;filter:blur(120px);pointer-events:none}}
    .bg-glow-1{{background:rgba(37,99,235,.15);top:-100px;right:-100px}}
    .bg-glow-2{{background:rgba(16,185,129,.08);bottom:-100px;left:-100px}}
    .card{{background:rgba(30,41,59,.9);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,.08);border-radius:1rem;padding:2.5rem;width:100%;max-width:440px;position:relative;z-index:1}}
    .logo{{display:flex;flex-direction:column;align-items:center;margin-bottom:2rem}}
    .logo-icon{{width:52px;height:52px;background:#2563EB;border-radius:.875rem;display:flex;align-items:center;justify-content:center;margin-bottom:.875rem;box-shadow:0 4px 20px rgba(37,99,235,.4)}}
    .logo-icon svg{{width:26px;height:26px;fill:none;stroke:#fff;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}}
    h1{{font-family:'Sora',sans-serif;color:#fff;font-size:1.5rem;font-weight:600}}
    .sub{{color:#64748B;font-size:13px;margin-top:.25rem;text-align:center}}
    .field{{margin-bottom:1.125rem}}
    label{{display:block;font-size:12px;font-weight:500;color:#94A3B8;margin-bottom:.375rem}}
    input{{width:100%;padding:.625rem .875rem;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:.5rem;color:#fff;font-size:14px;font-family:inherit;outline:none;transition:border-color .15s}}
    input::placeholder{{color:#475569}}
    input:focus{{border-color:#3B82F6;box-shadow:0 0 0 3px rgba(59,130,246,.2)}}
    .field-error{{font-size:11px;color:#FB7185;margin-top:4px}}
    .field-help{{font-size:11px;color:#475569;margin-top:4px}}
    .error-box{{background:rgba(244,63,94,.12);border:1px solid rgba(244,63,94,.3);border-radius:.5rem;padding:.625rem .875rem;margin-bottom:1rem;font-size:13px;color:#FCA5A5}}
    .btn{{width:100%;padding:.75rem;background:#2563EB;color:#fff;border:none;border-radius:.5rem;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit;transition:background .15s;margin-top:.5rem;display:flex;align-items:center;justify-content:center;gap:.5rem;text-decoration:none}}
    .btn:hover{{background:#1D4ED8}}
    .btn-ghost{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1)}}
    .btn-ghost:hover{{background:rgba(255,255,255,.1)}}
    .divider{{height:1px;background:rgba(255,255,255,.06);margin:1.25rem 0}}
    .footer{{margin-top:1.5rem;text-align:center;font-size:13px;color:#475569}}
    .link{{color:#93C5FD;text-decoration:none}}
    .link:hover{{text-decoration:underline}}
    .success-ring{{width:64px;height:64px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 1.25rem}}
  </style>
</head>
<body>
<div class="bg-glow bg-glow-1"></div>
<div class="bg-glow bg-glow-2"></div>
<div class="card">
  <div class="logo">
    <div class="logo-icon">{icon_svg}</div>
    <h1>{heading}</h1>
    <p class="sub">{subheading}</p>
  </div>
{content}
{footer}
</div>
</body>
</html>"""

import os
BASE = "C:/Users/franc/fjadmintest/backend/templates/core"
os.makedirs(BASE, exist_ok=True)

LOCK_SVG = '<svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'
USER_SVG = '<svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
PLUS_SVG = '<svg viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/></svg>'

# ── change_password.html ──────────────────────────────────────────────────
html = auth_page(
    "Change Password", LOCK_SVG, "Change Password",
    "Choose a strong new password",
    """  {% if messages %}{% for msg in messages %}<div class="error-box">{{ msg }}</div>{% endfor %}{% endif %}
  {% if form.non_field_errors %}<div class="error-box">{% for e in form.non_field_errors %}{{ e }}{% endfor %}</div>{% endif %}
  <form method="post" novalidate>{% csrf_token %}
    <div class="field">
      <label>{{ form.current_password.label }}</label>{{ form.current_password }}
      {% for e in form.current_password.errors %}<p class="field-error">{{ e }}</p>{% endfor %}
    </div>
    <div class="divider"></div>
    <div class="field">
      <label>{{ form.new_password.label }}</label>{{ form.new_password }}
      {% if form.new_password.help_text %}<p class="field-help">{{ form.new_password.help_text }}</p>{% endif %}
      {% for e in form.new_password.errors %}<p class="field-error">{{ e }}</p>{% endfor %}
    </div>
    <div class="field">
      <label>{{ form.confirm_password.label }}</label>{{ form.confirm_password }}
      {% for e in form.confirm_password.errors %}<p class="field-error">{{ e }}</p>{% endfor %}
    </div>
    <button type="submit" class="btn">Update Password</button>
  </form>""",
    '<div class="footer"><a href="{% url \'auth:profile\' %}" class="link">← Back to profile</a></div>'
)
open(f"{BASE}/change_password.html", "w", encoding="utf-8").write(html)

# ── password_reset_request.html ───────────────────────────────────────────
html = auth_page(
    "Reset Password", LOCK_SVG, "Reset Password",
    "Enter your email and we'll send a link",
    """  {% if form.non_field_errors %}<div class="error-box">{% for e in form.non_field_errors %}{{ e }}{% endfor %}</div>{% endif %}
  <form method="post" novalidate>{% csrf_token %}
    <div class="field">
      <label>{{ form.email.label }}</label>{{ form.email }}
      {% for e in form.email.errors %}<p class="field-error">{{ e }}</p>{% endfor %}
    </div>
    <button type="submit" class="btn">Send Reset Link</button>
  </form>""",
    '<div class="footer"><a href="{% url \'auth:login\' %}" class="link">← Back to sign in</a></div>'
)
open(f"{BASE}/password_reset_request.html", "w", encoding="utf-8").write(html)

# ── password_reset_done.html ──────────────────────────────────────────────
html = auth_page(
    "Check Your Email", LOCK_SVG, "Check your email", "",
    """  <div style="text-align:center">
    <div class="success-ring" style="background:rgba(16,185,129,.15)">
      <svg style="width:32px;height:32px;fill:none;stroke:#10B981;stroke-width:2;stroke-linecap:round;stroke-linejoin:round" viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
    </div>
    <h1 style="font-family:'Sora',sans-serif;color:#fff;font-size:1.375rem;margin-bottom:.625rem">Check your email</h1>
    <p style="color:#64748B;font-size:13px;line-height:1.7;margin-bottom:1.5rem">If an account exists for that email address, we've sent a reset link. Check your spam folder if you don't see it.</p>
    <a href="{% url 'auth:login' %}" class="btn">Back to Sign In</a>
  </div>"""
)
open(f"{BASE}/password_reset_done.html", "w", encoding="utf-8").write(html)

# ── password_reset_confirm.html ───────────────────────────────────────────
html = auth_page(
    "Set New Password", LOCK_SVG, "Set New Password",
    "Choose a strong password",
    """  {% if invalid_link %}
  <div style="text-align:center">
    <div class="success-ring" style="background:rgba(244,63,94,.12)">
      <svg style="width:32px;height:32px;fill:none;stroke:#F43F5E;stroke-width:2;stroke-linecap:round;stroke-linejoin:round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
    </div>
    <h1 style="font-family:'Sora',sans-serif;color:#fff;font-size:1.25rem;margin-bottom:.625rem">Link expired or invalid</h1>
    <p style="color:#64748B;font-size:13px;margin-bottom:1.5rem">This link has expired or already been used. Please request a new one.</p>
    <a href="{% url 'auth:password_reset' %}" class="btn">Request New Link</a>
  </div>
  {% else %}
  {% if form.non_field_errors %}<div class="error-box">{% for e in form.non_field_errors %}{{ e }}{% endfor %}</div>{% endif %}
  <form method="post" novalidate>{% csrf_token %}
    <div class="field">
      <label>{{ form.new_password.label }}</label>{{ form.new_password }}
      {% for e in form.new_password.errors %}<p class="field-error">{{ e }}</p>{% endfor %}
    </div>
    <div class="field">
      <label>{{ form.confirm_password.label }}</label>{{ form.confirm_password }}
      {% for e in form.confirm_password.errors %}<p class="field-error">{{ e }}</p>{% endfor %}
    </div>
    <button type="submit" class="btn">Set New Password</button>
  </form>
  {% endif %}"""
)
open(f"{BASE}/password_reset_confirm.html", "w", encoding="utf-8").write(html)

# ── password_reset_complete.html ──────────────────────────────────────────
html = auth_page(
    "Password Reset Complete", LOCK_SVG, "Password Updated!", "",
    """  <div style="text-align:center">
    <div class="success-ring" style="background:rgba(16,185,129,.15)">
      <svg style="width:32px;height:32px;fill:none;stroke:#10B981;stroke-width:2;stroke-linecap:round;stroke-linejoin:round" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
    </div>
    <p style="color:#64748B;font-size:13px;line-height:1.7;margin-bottom:1.5rem">Your password has been reset successfully. You can now sign in with your new password.</p>
    <a href="{% url 'auth:login' %}" class="btn">Sign In</a>
  </div>"""
)
open(f"{BASE}/password_reset_complete.html", "w", encoding="utf-8").write(html)

# ── register.html ─────────────────────────────────────────────────────────
html = auth_page(
    "Create Account", PLUS_SVG, "Create Account",
    "Join FJADMIN",
    """  {% if messages %}{% for msg in messages %}<div class="error-box">{{ msg }}</div>{% endfor %}{% endif %}
  {% if form.non_field_errors %}<div class="error-box">{% for e in form.non_field_errors %}{{ e }}{% endfor %}</div>{% endif %}
  <form method="post" novalidate>{% csrf_token %}
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:.75rem">
      <div class="field">
        <label>{{ form.first_name.label }}</label>{{ form.first_name }}
        {% for e in form.first_name.errors %}<p class="field-error">{{ e }}</p>{% endfor %}
      </div>
      <div class="field">
        <label>{{ form.last_name.label }}</label>{{ form.last_name }}
        {% for e in form.last_name.errors %}<p class="field-error">{{ e }}</p>{% endfor %}
      </div>
    </div>
    <div class="field">
      <label>{{ form.username.label }}</label>{{ form.username }}
      {% if form.username.help_text %}<p class="field-help">{{ form.username.help_text }}</p>{% endif %}
      {% for e in form.username.errors %}<p class="field-error">{{ e }}</p>{% endfor %}
    </div>
    <div class="field">
      <label>{{ form.email.label }}</label>{{ form.email }}
      {% for e in form.email.errors %}<p class="field-error">{{ e }}</p>{% endfor %}
    </div>
    <div class="field">
      <label>{{ form.password.label }}</label>{{ form.password }}
      {% for e in form.password.errors %}<p class="field-error">{{ e }}</p>{% endfor %}
    </div>
    <div class="field">
      <label>{{ form.confirm_password.label }}</label>{{ form.confirm_password }}
      {% for e in form.confirm_password.errors %}<p class="field-error">{{ e }}</p>{% endfor %}
    </div>
    <button type="submit" class="btn">Create Account</button>
  </form>""",
    '<div class="footer">Already have an account? <a href="{% url \'auth:login\' %}" class="link">Sign in</a></div>'
)
open(f"{BASE}/register.html", "w", encoding="utf-8").write(html)

print("6 templates written: change_password, password_reset_request, password_reset_done, password_reset_confirm, password_reset_complete, register")
