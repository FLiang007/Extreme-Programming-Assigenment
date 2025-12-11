from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# 联系方式模型
class ContactMethod(db.Model):
    __tablename__ = 'contact_methods'

    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    method_type = db.Column(db.String(20))  # phone, email, social, address
    value = db.Column(db.String(200))
    label = db.Column(db.String(50))  # 标签：工作电话、家庭电话等

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.method_type,
            'value': self.value,
            'label': self.label
        }


# 联系人模型
class Contact(db.Model):
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 一对多关系
    contact_methods = db.relationship('ContactMethod',
                                      backref='contact',
                                      lazy=True,
                                      cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'notes': self.notes,
            'is_favorite': self.is_favorite,
            'contact_methods': [method.to_dict() for method in self.contact_methods],
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }