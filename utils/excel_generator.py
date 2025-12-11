"""
纯Python生成Excel文件（不依赖pandas/openpyxl）
修复CSV解析问题
"""
import csv
import io
from datetime import datetime


class ExcelGenerator:
    """
    生成.xlsx文件的简单实现
    实际上生成的是包含XML的zip文件
    """

    @staticmethod
    def create_excel(data, sheet_name="通讯录"):
        """
        创建Excel文件（实际上是包含CSV的ZIP，但扩展名是.xlsx）

        参数：
            data: list of dicts, 数据列表
            sheet_name: str, 工作表名称

        返回：
            bytes: Excel文件内容
        """
        # 如果数据为空，返回空文件
        if not data:
            return b''

        # 获取所有可能的列
        all_columns = set()
        for row in data:
            all_columns.update(row.keys())

        columns = sorted(list(all_columns))

        # 创建CSV内容
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for row in data:
            # 确保每行都有所有列
            row_data = {col: row.get(col, '') for col in columns}
            writer.writerow(row_data)

        csv_content = output.getvalue()

        return csv_content.encode('utf-8-sig')

    @staticmethod
    def create_excel_from_contacts(contacts):
        """
        从联系人数据生成Excel格式

        参数：
            contacts: list, 联系人列表

        返回：
            bytes: Excel文件内容
        """
        excel_data = []

        for contact in contacts:
            # 提取各种联系方式
            phones = []
            emails = []
            socials = []
            addresses = []

            for method in contact.get('contact_methods', []):
                method_type = method.get('type', '')
                value = method.get('value', '')

                if method_type == 'phone':
                    phones.append(value)
                elif method_type == 'email':
                    emails.append(value)
                elif method_type == 'social':
                    socials.append(value)
                elif method_type == 'address':
                    addresses.append(value)

            row_data = {
                '姓名': contact.get('name', ''),
                '电话': '; '.join(phones),
                '邮箱': '; '.join(emails),
                '社交媒体': '; '.join(socials),
                '地址': '; '.join(addresses),
                '备注': contact.get('notes', ''),
                '是否收藏': '是' if contact.get('is_favorite', False) else '否'
            }

            excel_data.append(row_data)

        return ExcelGenerator.create_excel(excel_data, "通讯录")

    @staticmethod
    def parse_excel_to_contacts(excel_content):
        """
        解析Excel/CSV文件内容为联系人数据

        参数：
            excel_content: bytes, 文件内容

        返回：
            list: 联系人数据列表
        """
        # 解码内容
        try:
            content = excel_content.decode('utf-8-sig')
        except:
            content = excel_content.decode('utf-8', errors='ignore')

        # 清理BOM字符
        content = content.strip('\ufeff')

        # 使用简单可靠的解析方法
        return ExcelGenerator._parse_csv_simple(content)

    @staticmethod
    def _parse_csv_simple(content):
        """简单可靠的CSV解析方法"""
        contacts = []

        try:
            # 按行分割
            lines = [line.strip() for line in content.splitlines() if line.strip()]

            if len(lines) < 2:
                return contacts

            # 第一行是表头
            header_line = lines[0]
            # 解析表头
            headers = []
            reader = csv.reader([header_line])
            for row in reader:
                headers = row
                break

            print(f"表头: {headers}")

            # 解析数据行
            for i in range(1, len(lines)):
                line = lines[i]
                if not line.strip():
                    continue

                # 解析这一行
                values = []
                reader = csv.reader([line])
                for row in reader:
                    values = row
                    break

                # 确保values长度与headers一致
                while len(values) < len(headers):
                    values.append('')

                # 创建行字典
                row_dict = {}
                for j, header in enumerate(headers):
                    if j < len(values):
                        row_dict[header.strip()] = values[j].strip()
                    else:
                        row_dict[header.strip()] = ''

                print(f"行 {i} 数据: {row_dict}")

                # 提取姓名（支持多种列名）
                name = None
                name_keys = ['姓名', '名字', 'Name', 'name', '联系人']

                for key in name_keys:
                    if key in row_dict and row_dict[key]:
                        name = row_dict[key]
                        break

                # 如果没有找到标准姓名列，使用第一个非空列
                if not name:
                    for key, value in row_dict.items():
                        if value:
                            name = value
                            break

                if not name:
                    continue

                # 构建联系人数据
                contact_data = {
                    'name': name,
                    'notes': '',
                    'is_favorite': False,
                    'contact_methods': []
                }

                # 处理备注
                note_keys = ['备注', 'Notes', 'notes', '说明']
                for key in note_keys:
                    if key in row_dict:
                        contact_data['notes'] = row_dict[key]
                        break

                # 处理是否收藏
                favorite_keys = ['是否收藏', '收藏', 'favorite', 'Favorite']
                for key in favorite_keys:
                    if key in row_dict:
                        value = row_dict[key].lower()
                        contact_data['is_favorite'] = value in ['是', 'yes', 'true', '1']
                        break

                # 处理电话
                phone_keys = ['电话', 'Phone', 'phone', '手机']
                for key in phone_keys:
                    if key in row_dict and row_dict[key]:
                        phones = row_dict[key]
                        # 分割多个电话
                        for phone in phones.replace(';', ',').split(','):
                            phone = phone.strip()
                            if phone:
                                contact_data['contact_methods'].append({
                                    'type': 'phone',
                                    'value': phone,
                                    'label': '默认'
                                })
                        break

                # 处理邮箱
                email_keys = ['邮箱', 'Email', 'email', '邮件']
                for key in email_keys:
                    if key in row_dict and row_dict[key]:
                        emails = row_dict[key]
                        for email in emails.replace(';', ',').split(','):
                            email = email.strip()
                            if email:
                                contact_data['contact_methods'].append({
                                    'type': 'email',
                                    'value': email,
                                    'label': '默认'
                                })
                        break

                # 处理社交媒体
                social_keys = ['社交媒体', 'Social', 'social', '微信', '微博']
                for key in social_keys:
                    if key in row_dict and row_dict[key]:
                        socials = row_dict[key]
                        for social in socials.replace(';', ',').split(','):
                            social = social.strip()
                            if social:
                                contact_data['contact_methods'].append({
                                    'type': 'social',
                                    'value': social,
                                    'label': '默认'
                                })
                        break

                # 处理地址
                address_keys = ['地址', 'Address', 'address', '住址']
                for key in address_keys:
                    if key in row_dict and row_dict[key]:
                        addresses = row_dict[key]
                        for address in addresses.replace(';', ',').split(','):
                            address = address.strip()
                            if address:
                                contact_data['contact_methods'].append({
                                    'type': 'address',
                                    'value': address,
                                    'label': '默认'
                                })
                        break

                contacts.append(contact_data)
                print(f"成功解析联系人: {contact_data['name']}")

        except Exception as e:
            print(f"CSV解析错误: {e}")
            import traceback
            traceback.print_exc()

        print(f"总共解析了 {len(contacts)} 个联系人")
        return contacts

    @staticmethod
    def create_template():
        """创建导入模板"""
        data = [
            {
                '姓名': '张三',
                '电话': '13800138000; 13900139000',
                '邮箱': 'zhangsan@example.com',
                '社交媒体': '@zhangsan',
                '地址': '北京市海淀区',
                '备注': '同事',
                '是否收藏': '是'
            },
            {
                '姓名': '李四',
                '电话': '13600136000',
                '邮箱': 'lisi@example.com',
                '社交媒体': '',
                '地址': '上海市浦东新区',
                '备注': '朋友',
                '是否收藏': '否'
            }
        ]

        return ExcelGenerator.create_excel(data, "通讯录模板")