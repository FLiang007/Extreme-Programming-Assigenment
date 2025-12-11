from flask import Flask, render_template, request, jsonify, make_response
from flask_cors import CORS
import os
from datetime import datetime

from config import config
from database.models import db, Contact, ContactMethod
from services.contact_service import ContactService
from utils.excel_generator import ExcelGenerator


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 初始化扩展
    db.init_app(app)
    CORS(app)

    # 初始化服务
    contact_service = ContactService(db)

    @app.route('/')
    def index():
        """主页"""
        return render_template('index.html')

    @app.route('/template')
    def download_template():
        """显示导入模板说明"""
        return render_template('import_template.html')

    @app.route('/api/template/download')
    def download_csv_template():
        """下载CSV模板"""
        template = """姓名,电话,邮箱,社交媒体,地址,备注,是否收藏
张三,13800138000; 13900139000,zhangsan@example.com,@zhangsan,北京市海淀区,同事,是
李四,13600136000,lisi@example.com,,上海市浦东新区,朋友,否
王五,13700137000,wangwu@example.com,@wangwu,广州市天河区,同学,是"""

        response = make_response(template)
        response.headers['Content-Disposition'] = 'attachment; filename=通讯录模板.csv'
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        return response

    # ========== API 接口 ==========

    @app.route('/api/contacts', methods=['GET'])
    def get_contacts():
        """获取所有联系人"""
        try:
            contacts = contact_service.get_all_contacts()
            return jsonify({'success': True, 'data': contacts})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/contacts/<int:contact_id>', methods=['GET'])
    def get_contact(contact_id):
        """获取单个联系人"""
        try:
            contact = contact_service.get_contact_by_id(contact_id)
            if contact:
                return jsonify({'success': True, 'data': contact})
            return jsonify({'success': False, 'error': '联系人不存在'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/contacts', methods=['POST'])
    def create_contact():
        """创建联系人"""
        try:
            data = request.json
            contact = contact_service.create_contact(data)
            return jsonify({'success': True, 'data': contact}), 201
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/contacts/<int:contact_id>', methods=['PUT'])
    def update_contact(contact_id):
        """更新联系人"""
        try:
            data = request.json
            contact = contact_service.update_contact(contact_id, data)
            if contact:
                return jsonify({'success': True, 'data': contact})
            return jsonify({'success': False, 'error': '联系人不存在'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/contacts/<int:contact_id>/favorite', methods=['PUT'])
    def toggle_favorite(contact_id):
        """切换收藏状态"""
        try:
            data = request.json
            is_favorite = data.get('is_favorite')
            contact = contact_service.toggle_favorite(contact_id, is_favorite)
            if contact:
                return jsonify({'success': True, 'data': contact})
            return jsonify({'success': False, 'error': '联系人不存在'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
    def delete_contact(contact_id):
        """删除联系人"""
        try:
            success = contact_service.delete_contact(contact_id)
            if success:
                return jsonify({'success': True, 'message': '删除成功'})
            return jsonify({'success': False, 'error': '联系人不存在'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/contacts/search', methods=['GET'])
    def search_contacts():
        """搜索联系人"""
        try:
            keyword = request.args.get('q', '')
            if not keyword:
                return jsonify({'success': True, 'data': []})

            contacts = contact_service.search_contacts(keyword)
            return jsonify({'success': True, 'data': contacts})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # ========== 导入导出功能 ==========

    @app.route('/api/contacts/export', methods=['GET'])
    def export_contacts():
        """导出联系人到Excel - 修复性能问题"""
        try:
            import time
            start_time = time.time()

            print(f"\n{'=' * 50}")
            print(f"📤 开始导出 - {datetime.now().strftime('%H:%M:%S')}")

            # 1. 获取联系人
            contacts = contact_service.get_all_contacts()
            print(f"📊 联系人数量: {len(contacts)}")

            if not contacts:
                print("⚠️ 没有联系人数据，创建测试数据...")
                # 创建一些测试数据
                contacts = [
                    {
                        'id': 1,
                        'name': '测试用户',
                        'notes': '测试备注',
                        'is_favorite': True,
                        'contact_methods': [
                            {'type': 'phone', 'value': '13800000000', 'label': '手机'}
                        ],
                        'created_at': '2024-01-01 00:00:00',
                        'updated_at': '2024-01-01 00:00:00'
                    }
                ]

            print(f"⏱️ 获取联系人耗时: {time.time() - start_time:.2f}秒")

            # 2. 生成Excel内容
            excel_start = time.time()

            # 简化Excel生成 - 对于大量数据可能需要优化
            print("🔄 正在生成Excel文件...")

            # 使用简化的Excel生成
            excel_content = generate_simple_excel(contacts)

            print(f"⏱️ 生成Excel耗时: {time.time() - excel_start:.2f}秒")
            print(f"📄 文件大小: {len(excel_content)} 字节")

            # 3. 创建响应
            filename = f"通讯录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            response = make_response(excel_content)
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

            # 如果是CSV内容，用CSV的Content-Type
            if filename.endswith('.csv'):
                response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            else:
                response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

            total_time = time.time() - start_time
            print(f"✅ 导出完成 - 总耗时: {total_time:.2f}秒")
            print(f"📁 文件名: {filename}")
            print(f"{'=' * 50}\n")

            return response

        except Exception as e:
            print(f"❌ 导出失败: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    def generate_simple_excel(contacts):
        """生成简化的Excel/CSV文件"""
        import csv
        import io

        # 创建CSV内容
        output = io.StringIO()

        # 表头
        fieldnames = ['姓名', '电话', '邮箱', '社交媒体', '地址', '备注', '是否收藏']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # 写入数据
        for contact in contacts:
            # 提取各种联系方式
            phones = []
            emails = []
            socials = []
            addresses = []

            for method in contact.get('contact_methods', []):
                if method['type'] == 'phone':
                    phones.append(method['value'])
                elif method['type'] == 'email':
                    emails.append(method['value'])
                elif method['type'] == 'social':
                    socials.append(method['value'])
                elif method['type'] == 'address':
                    addresses.append(method['value'])

            row = {
                '姓名': contact.get('name', ''),
                '电话': '; '.join(phones),
                '邮箱': '; '.join(emails),
                '社交媒体': '; '.join(socials),
                '地址': '; '.join(addresses),
                '备注': contact.get('notes', ''),
                '是否收藏': '是' if contact.get('is_favorite', False) else '否'
            }

            writer.writerow(row)

        content = output.getvalue()
        return content.encode('utf-8-sig')

    @app.route('/api/contacts/import', methods=['POST'])
    def import_contacts():
        """从Excel导入联系人"""
        try:
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': '没有上传文件'}), 400

            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': '没有选择文件'}), 400

            # 检查文件格式
            if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
                return jsonify({'success': False, 'error': '只支持Excel/CSV文件'}), 400

            # 读取文件内容
            file_content = file.read()
            print(f"=== 导入调试 ===")
            print(f"文件大小: {len(file_content)} bytes")

            # 使用纯Python解析
            contacts_data = ExcelGenerator.parse_excel_to_contacts(file_content)

            print(f"解析出的联系人数量: {len(contacts_data)}")

            # 导入数据
            success_count = 0
            error_records = []

            for index, contact_data in enumerate(contacts_data):
                try:
                    contact_service.create_contact(contact_data)
                    success_count += 1
                    print(f"成功导入: {contact_data['name']}")
                except Exception as e:
                    error_records.append({
                        '行号': index + 2,
                        '姓名': contact_data.get('name', ''),
                        '错误': str(e)
                    })
                    print(f"导入失败: {contact_data.get('name', '')} - {e}")

            print(f"导入结果: 成功 {success_count}, 失败 {len(error_records)}")
            print("=== 导入结束 ===")

            return jsonify({
                'success': True,
                'message': f'导入完成，成功{success_count}条，失败{len(error_records)}条',
                'errors': error_records
            })

        except Exception as e:
            print(f"导入异常: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/favorites', methods=['GET'])
    def get_favorites():
        """获取收藏的联系人"""
        try:
            favorites = contact_service.get_favorite_contacts()
            return jsonify({'success': True, 'data': favorites})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # ========== 其他辅助接口 ==========

    @app.route('/api/stats', methods=['GET'])
    def get_stats():
        """获取统计数据"""
        try:
            all_contacts = Contact.query.all()
            favorite_contacts = Contact.query.filter_by(is_favorite=True).all()

            # 统计各种联系方式的数量
            phone_count = ContactMethod.query.filter_by(method_type='phone').count()
            email_count = ContactMethod.query.filter_by(method_type='email').count()
            social_count = ContactMethod.query.filter_by(method_type='social').count()
            address_count = ContactMethod.query.filter_by(method_type='address').count()

            return jsonify({
                'success': True,
                'data': {
                    'total_contacts': len(all_contacts),
                    'favorite_contacts': len(favorite_contacts),
                    'phone_methods': phone_count,
                    'email_methods': email_count,
                    'social_methods': social_count,
                    'address_methods': address_count
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # ========== 错误处理 ==========

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'error': '资源不存在'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'success': False, 'error': '服务器内部错误'}), 500

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'success': False, 'error': '文件太大，最大支持16MB'}), 413

    return app


if __name__ == '__main__':
    app = create_app('development')

    with app.app_context():
        # 创建数据库表
        db.create_all()

        # 添加测试数据（如果数据库为空）
        if Contact.query.count() == 0:
            print("添加测试数据...")
            test_contacts = [
                {
                    'name': '张三',
                    'notes': '同事',
                    'is_favorite': True,
                    'contact_methods': [
                        {'type': 'phone', 'value': '13800138000', 'label': '工作电话'},
                        {'type': 'email', 'value': 'zhangsan@example.com', 'label': '工作邮箱'}
                    ]
                },
                {
                    'name': '李四',
                    'notes': '朋友',
                    'is_favorite': False,
                    'contact_methods': [
                        {'type': 'phone', 'value': '13900139000', 'label': '手机'},
                        {'type': 'address', 'value': '北京市海淀区', 'label': '家庭地址'}
                    ]
                },
                {
                    'name': '王五',
                    'notes': '同学',
                    'is_favorite': True,
                    'contact_methods': [
                        {'type': 'phone', 'value': '13700137000', 'label': '手机'},
                        {'type': 'social', 'value': '@wangwu', 'label': '微信'},
                        {'type': 'email', 'value': 'wangwu@example.com', 'label': '个人邮箱'}
                    ]
                }
            ]

            contact_service = ContactService(db)
            for contact_data in test_contacts:
                contact_service.create_contact(contact_data)

            print("测试数据添加完成！")

        print("✅ 数据库表创建完成！")
        print("✅ 服务器启动中...")
        print("🌐 请访问: http://127.0.0.1:5000")
        print("📄 模板页面: http://127.0.0.1:5000/template")
        print("📊 API测试: http://127.0.0.1:5000/api/contacts")

    app.run(debug=True, port=5000)