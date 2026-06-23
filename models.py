import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Mood(db.Model):
    __tablename__ = 'moods'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    tags = db.Column(db.Text, default='[]')
    note = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'score': self.score,
            'tags': json.loads(self.tags),
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
