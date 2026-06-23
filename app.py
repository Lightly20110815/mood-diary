import json
from datetime import date, datetime, timedelta
from functools import wraps
from calendar import monthrange

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from config import Config
from models import Mood, db

SCORE_LABELS = {
    -3: '非常不愉快',
    -2: '不愉快',
    -1: '略不愉快',
    0: '中性',
    1: '略愉快',
    2: '愉快',
    3: '非常愉快',
}

TAG_OPTIONS = [
    '平静', '开心', '满足', '期待',
    '精力充沛', '疲惫', '焦虑', '烦躁',
    '难过', '孤独', '感恩', '压力大',
]

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def index():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    month_end = today.replace(day=monthrange(today.year, today.month)[1])

    week_moods = Mood.query.filter(
        Mood.date >= week_start, Mood.date <= today
    ).order_by(Mood.date.asc()).all()

    month_moods = Mood.query.filter(
        Mood.date >= month_start, Mood.date <= month_end
    ).order_by(Mood.date.asc()).all()

    all_moods = Mood.query.order_by(Mood.date.desc()).limit(30).all()
    all_moods_list = [m.to_dict() for m in all_moods]

    # --- weekly bar chart data ---
    week_labels = [((week_start + timedelta(days=i)).strftime('%m/%d %a')) for i in range(7)]
    week_scores = [None] * 7
    for m in week_moods:
        idx = (m.date - week_start).days
        if 0 <= idx < 7:
            week_scores[idx] = m.score

    week_avg = (
        round(sum(m.score for m in week_moods) / len(week_moods), 1)
        if week_moods else None
    )
    week_count = len(week_moods)

    # --- last week comparison ---
    prev_week_start = week_start - timedelta(days=7)
    prev_week_end = week_start - timedelta(days=1)
    prev_week_moods = Mood.query.filter(
        Mood.date >= prev_week_start, Mood.date <= prev_week_end
    ).all()
    prev_week_avg = (
        round(sum(m.score for m in prev_week_moods) / len(prev_week_moods), 1)
        if prev_week_moods else None
    )

    # --- monthly calendar heatmap data ---
    cal_days_in_month = monthrange(today.year, today.month)[1]
    month_scores_map = {m.date.day: m.score for m in month_moods}

    # pad before the 1st so the calendar grid starts on Monday
    first_weekday = date(today.year, today.month, 1).weekday()
    cal_padding = [None] * first_weekday
    cal_days = [i + 1 for i in range(cal_days_in_month)]

    # --- monthly stats ---
    month_avg = (
        round(sum(m.score for m in month_moods) / len(month_moods), 1)
        if month_moods else None
    )
    month_count = len(month_moods)
    month_possible = cal_days_in_month

    # --- tag distribution ---
    tag_counts = {}
    for m in month_moods:
        for tag in json.loads(m.tags):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # --- recent weekly averages for trend ---
    weekly_trend_labels = []
    weekly_trend_avgs = []
    for w in range(7, -1, -1):
        ws = today - timedelta(days=today.weekday()) - timedelta(weeks=w)
        we = ws + timedelta(days=6)
        wm = Mood.query.filter(Mood.date >= ws, Mood.date <= we).all()
        weekly_trend_labels.append(ws.strftime('%m/%d'))
        if wm:
            weekly_trend_avgs.append(round(sum(m.score for m in wm) / len(wm), 1))
        else:
            weekly_trend_avgs.append(None)

    return render_template(
        'index.html',
        all_moods=all_moods_list,
        week_labels=week_labels,
        week_scores=week_scores,
        week_avg=week_avg,
        week_count=week_count,
        prev_week_avg=prev_week_avg,
        cal_padding=cal_padding,
        cal_days=cal_days,
        month_scores_map=month_scores_map,
        month_avg=month_avg,
        month_count=month_count,
        month_possible=month_possible,
        tag_counts=tag_counts,
        weekly_trend_labels=weekly_trend_labels,
        weekly_trend_avgs=weekly_trend_avgs,
        score_labels=SCORE_LABELS,
        today=today,
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == app.config['ADMIN_PASSWORD']:
            session['admin'] = True
            return redirect(url_for('admin'))
        return render_template('login.html', error='密码错误')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    today = date.today()

    if request.method == 'POST':
        mood_date_str = request.form.get('date', today.isoformat())
        try:
            mood_date = datetime.strptime(mood_date_str, '%Y-%m-%d').date()
        except ValueError:
            mood_date = today
        score = int(request.form.get('score', 0))
        tags = request.form.getlist('tags')
        note = request.form.get('note', '')

        existing = Mood.query.filter_by(date=mood_date).first()
        if existing:
            existing.score = score
            existing.tags = json.dumps(tags, ensure_ascii=False)
            existing.note = note
        else:
            mood = Mood(
                date=mood_date, score=score,
                tags=json.dumps(tags, ensure_ascii=False), note=note,
            )
            db.session.add(mood)
        db.session.commit()
        return redirect(url_for('admin'))

    edit_date_str = request.args.get('edit_date')
    if edit_date_str:
        try:
            selected_date = datetime.strptime(edit_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    selected_mood = Mood.query.filter_by(date=selected_date).first()
    recent_moods = Mood.query.order_by(Mood.date.desc()).limit(14).all()

    return render_template(
        'admin.html',
        today=today,
        selected_date=selected_date,
        today_mood=selected_mood.to_dict() if selected_mood else None,
        recent_moods=[m.to_dict() for m in recent_moods],
        tag_options=TAG_OPTIONS,
        score_labels=SCORE_LABELS,
    )


@app.route('/admin/delete/<int:mood_id>', methods=['POST'])
@login_required
def delete_mood(mood_id):
    mood = Mood.query.get_or_404(mood_id)
    db.session.delete(mood)
    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/api/moods')
def api_moods():
    moods = Mood.query.order_by(Mood.date.desc()).limit(90).all()
    return jsonify([m.to_dict() for m in moods])


def create_app():
    with app.app_context():
        db.create_all()
    return app


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=8080)
