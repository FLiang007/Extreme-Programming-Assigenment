from database.models import db, Contact, ContactMethod
from datetime import datetime

class ContactService:
    def __init__(self, db_session):
        """初始化ContactService"""
        self.db = db_session
    
    def get_all_contacts(self):
        """获取所有联系人"""
        contacts = Contact.query.order_by(Contact.created_at.desc()).all()
        return [contact.to_dict() for contact in contacts]
    
    def get_contact_by_id(self, contact_id):
        """根据ID获取联系人"""
        contact = Contact.query.get(contact_id)
        return contact.to_dict() if contact else None
    
    def create_contact(self, data):
        """创建联系人"""
        contact = Contact(
            name=data['name'],
            notes=data.get('notes', ''),
            is_favorite=data.get('is_favorite', False)
        )
        
        # 添加联系方式
        for method_data in data.get('contact_methods', []):
            method = ContactMethod(
                method_type=method_data['type'],
                value=method_data['value'],
                label=method_data.get('label', '默认')
            )
            contact.contact_methods.append(method)
        
        self.db.session.add(contact)
        self.db.session.commit()
        return contact.to_dict()
    
    def update_contact(self, contact_id, data):
        """更新联系人"""
        contact = Contact.query.get(contact_id)
        if not contact:
            return None
        
        # 更新基本信息
        if 'name' in data:
            contact.name = data['name']
        if 'notes' in data:
            contact.notes = data['notes']
        
        # 更新联系方式
        if 'contact_methods' in data:
            # 删除旧的联系方式
            ContactMethod.query.filter_by(contact_id=contact_id).delete()
            
            # 添加新的联系方式
            for method_data in data['contact_methods']:
                method = ContactMethod(
                    method_type=method_data['type'],
                    value=method_data['value'],
                    label=method_data.get('label', '默认')
                )
                contact.contact_methods.append(method)
        
        contact.updated_at = datetime.utcnow()
        self.db.session.commit()
        return contact.to_dict()
    
    def toggle_favorite(self, contact_id, is_favorite):
        """切换收藏状态"""
        contact = Contact.query.get(contact_id)
        if not contact:
            return None
        
        contact.is_favorite = is_favorite
        contact.updated_at = datetime.utcnow()
        self.db.session.commit()
        return contact.to_dict()
    
    def delete_contact(self, contact_id):
        """删除联系人"""
        contact = Contact.query.get(contact_id)
        if not contact:
            return False
        
        self.db.session.delete(contact)
        self.db.session.commit()
        return True
    
    def get_favorite_contacts(self):
        """获取收藏的联系人"""
        favorites = Contact.query.filter_by(is_favorite=True)\
                                 .order_by(Contact.updated_at.desc())\
                                 .all()
        return [contact.to_dict() for contact in favorites]
    
    def search_contacts(self, keyword):
        """搜索联系人"""
        # 搜索姓名和备注
        contacts = Contact.query.filter(
            (Contact.name.contains(keyword)) |
            (Contact.notes.contains(keyword))
        ).all()
        
        # 同时搜索联系方式
        methods = ContactMethod.query.filter(
            ContactMethod.value.contains(keyword)
        ).all()
        
        contact_ids = set([c.id for c in contacts])
        contact_ids.update([m.contact_id for m in methods])
        
        result_contacts = Contact.query.filter(Contact.id.in_(contact_ids)).all()
        return [contact.to_dict() for contact in result_contacts]