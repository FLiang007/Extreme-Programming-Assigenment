// 全局变量
let contacts = [];
let currentView = 'all';
let currentEditId = null;
let searchTimeout = null;

// API基础URL
const API_BASE = '/api';

// 显示通知
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 加载联系人
async function loadContacts() {
    try {
        const response = await fetch(`${API_BASE}/contacts`);
        const result = await response.json();

        if (result.success) {
            contacts = result.data;
            renderContacts();
            updateStats();
        } else {
            showNotification('加载失败: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('网络错误: ' + error.message, 'error');
    }
}

// 渲染联系人
function renderContacts() {
    const grid = document.getElementById('contactsGrid');

    if (!contacts || contacts.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-users"></i>
                <h3>暂无联系人</h3>
                <p>点击"添加联系人"按钮开始创建</p>
            </div>
        `;
        return;
    }

    // 根据当前视图筛选
    let filteredContacts = contacts;
    if (currentView === 'favorites') {
        filteredContacts = contacts.filter(c => c.is_favorite);
    }

    // 如果有搜索关键词
    const searchInput = document.getElementById('searchInput');
    if (searchInput && searchInput.value.trim()) {
        const keyword = searchInput.value.trim().toLowerCase();
        filteredContacts = filteredContacts.filter(contact =>
            contact.name.toLowerCase().includes(keyword) ||
            contact.notes.toLowerCase().includes(keyword) ||
            contact.contact_methods.some(method =>
                method.value.toLowerCase().includes(keyword)
            )
        );
    }

    if (filteredContacts.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <h3>未找到匹配的联系人</h3>
                <p>尝试其他搜索关键词</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = filteredContacts.map(contact => createContactCard(contact)).join('');
}

// 创建联系人卡片HTML
function createContactCard(contact) {
    // 按类型分组联系方式
    const methodsByType = {
        phone: contact.contact_methods.filter(m => m.type === 'phone'),
        email: contact.contact_methods.filter(m => m.type === 'email'),
        social: contact.contact_methods.filter(m => m.type === 'social'),
        address: contact.contact_methods.filter(m => m.type === 'address')
    };

    return `
        <div class="contact-card ${contact.is_favorite ? 'favorite' : ''}">
            <div class="contact-header">
                <div class="contact-name">${escapeHtml(contact.name)}</div>
                <button class="favorite-btn ${contact.is_favorite ? 'active' : ''}"
                        onclick="toggleFavorite(${contact.id}, ${!contact.is_favorite})">
                    ${contact.is_favorite ? '★' : '☆'}
                </button>
            </div>

            <div class="contact-methods">
                ${methodsByType.phone.length > 0 ? `
                    <div class="method-item">
                        <i class="fas fa-phone"></i>
                        <span>${escapeHtml(methodsByType.phone.map(m => m.value).join(', '))}</span>
                    </div>
                ` : ''}

                ${methodsByType.email.length > 0 ? `
                    <div class="method-item">
                        <i class="fas fa-envelope"></i>
                        <span>${escapeHtml(methodsByType.email.map(m => m.value).join(', '))}</span>
                    </div>
                ` : ''}

                ${methodsByType.social.length > 0 ? `
                    <div class="method-item">
                        <i class="fas fa-hashtag"></i>
                        <span>${escapeHtml(methodsByType.social.map(m => m.value).join(', '))}</span>
                    </div>
                ` : ''}

                ${methodsByType.address.length > 0 ? `
                    <div class="method-item">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>${escapeHtml(methodsByType.address.map(m => m.value).join(', '))}</span>
                    </div>
                ` : ''}
            </div>

            ${contact.notes ? `
                <div class="contact-notes">
                    ${escapeHtml(contact.notes)}
                </div>
            ` : ''}

            <div class="contact-footer">
                <div class="contact-date">
                    创建于 ${contact.created_at}
                </div>
                <div class="contact-actions">
                    <button class="btn btn-secondary" onclick="editContact(${contact.id})">
                        <i class="fas fa-edit"></i> 编辑
                    </button>
                    <button class="btn btn-danger" onclick="deleteContact(${contact.id})">
                        <i class="fas fa-trash"></i> 删除
                    </button>
                </div>
            </div>
        </div>
    `;
}

// 更新统计信息
function updateStats() {
    const totalContacts = contacts.length;
    const favoriteContacts = contacts.filter(c => c.is_favorite).length;

    document.getElementById('contactCount').textContent = `共 ${totalContacts} 个联系人`;
    document.getElementById('favoriteCount').textContent = `收藏: ${favoriteContacts}`;
}

// 切换视图
function toggleView(view) {
    currentView = view;
    renderContacts();

    // 更新按钮状态
    document.querySelectorAll('.btn-group .btn-secondary').forEach(btn => {
        btn.classList.remove('active');
    });

    if (view === 'all') {
        document.querySelector('.btn-group .btn-secondary:nth-child(1)').classList.add('active');
    } else {
        document.querySelector('.btn-group .btn-secondary:nth-child(2)').classList.add('active');
    }
}

// 搜索联系人
function searchContacts() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        renderContacts();
    }, 300);
}

// 显示添加表单
function showAddForm() {
    currentEditId = null;
    document.getElementById('modalTitle').textContent = '添加联系人';
    document.getElementById('contactForm').reset();
    document.getElementById('contactId').value = '';

    // 重置联系方式
    const methodsContainer = document.getElementById('contactMethods');
    methodsContainer.innerHTML = `
        <div class="method-row">
            <select class="method-type">
                <option value="phone">电话</option>
                <option value="email">邮箱</option>
                <option value="social">社交媒体</option>
                <option value="address">地址</option>
            </select>
            <input type="text" class="method-value" placeholder="联系方式">
            <input type="text" class="method-label" placeholder="标签（可选）">
            <button type="button" class="remove-method" onclick="removeMethod(this)">×</button>
        </div>
    `;

    document.getElementById('contactFavorite').checked = false;
    openModal('contactModal');
}

// 编辑联系人
async function editContact(contactId) {
    try {
        const response = await fetch(`${API_BASE}/contacts/${contactId}`);
        const result = await response.json();

        if (result.success) {
            const contact = result.data;
            currentEditId = contactId;
            document.getElementById('modalTitle').textContent = '编辑联系人';
            document.getElementById('contactId').value = contactId;
            document.getElementById('contactName').value = contact.name;
            document.getElementById('contactNotes').value = contact.notes || '';
            document.getElementById('contactFavorite').checked = contact.is_favorite;

            // 添加联系方式
            const methodsContainer = document.getElementById('contactMethods');
            methodsContainer.innerHTML = '';

            if (contact.contact_methods.length === 0) {
                addMethod();
            } else {
                contact.contact_methods.forEach(method => {
                    const methodRow = document.createElement('div');
                    methodRow.className = 'method-row';
                    methodRow.innerHTML = `
                        <select class="method-type">
                            <option value="phone" ${method.type === 'phone' ? 'selected' : ''}>电话</option>
                            <option value="email" ${method.type === 'email' ? 'selected' : ''}>邮箱</option>
                            <option value="social" ${method.type === 'social' ? 'selected' : ''}>社交媒体</option>
                            <option value="address" ${method.type === 'address' ? 'selected' : ''}>地址</option>
                        </select>
                        <input type="text" class="method-value" value="${escapeHtml(method.value)}" placeholder="联系方式">
                        <input type="text" class="method-label" value="${escapeHtml(method.label || '')}" placeholder="标签（可选）">
                        <button type="button" class="remove-method" onclick="removeMethod(this)">×</button>
                    `;
                    methodsContainer.appendChild(methodRow);
                });
            }

            openModal('contactModal');
        } else {
            showNotification('加载联系人失败: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('网络错误: ' + error.message, 'error');
    }
}

// 保存联系人
async function saveContact(event) {
    event.preventDefault();

    const contactId = document.getElementById('contactId').value;
    const name = document.getElementById('contactName').value.trim();
    const notes = document.getElementById('contactNotes').value.trim();
    const isFavorite = document.getElementById('contactFavorite').checked;

    if (!name) {
        showNotification('请输入联系人姓名', 'error');
        return false;
    }

    // 收集联系方式
    const contactMethods = [];
    const methodRows = document.querySelectorAll('#contactMethods .method-row');

    methodRows.forEach(row => {
        const type = row.querySelector('.method-type').value;
        const value = row.querySelector('.method-value').value.trim();
        const label = row.querySelector('.method-label').value.trim();

        if (value) {
            contactMethods.push({
                type: type,
                value: value,
                label: label || '默认'
            });
        }
    });

    const contactData = {
        name: name,
        notes: notes,
        is_favorite: isFavorite,
        contact_methods: contactMethods
    };

    try {
        let response;
        let method;

        if (contactId) {
            // 更新
            response = await fetch(`${API_BASE}/contacts/${contactId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(contactData)
            });
            method = '更新';
        } else {
            // 创建
            response = await fetch(`${API_BASE}/contacts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(contactData)
            });
            method = '创建';
        }

        const result = await response.json();

        if (result.success) {
            showNotification(`${method}联系人成功`, 'success');
            closeModal('contactModal');
            loadContacts();
        } else {
            showNotification(`${method}失败: ` + result.error, 'error');
        }
    } catch (error) {
        showNotification('网络错误: ' + error.message, 'error');
    }

    return false;
}

// 切换收藏状态
async function toggleFavorite(contactId, isFavorite) {
    try {
        const response = await fetch(`${API_BASE}/contacts/${contactId}/favorite`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_favorite: isFavorite })
        });

        const result = await response.json();

        if (result.success) {
            showNotification(isFavorite ? '已添加到收藏夹' : '已从收藏夹移除', 'success');
            loadContacts();
        } else {
            showNotification('操作失败: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('网络错误: ' + error.message, 'error');
    }
}

// 删除联系人
async function deleteContact(contactId) {
    if (!confirm('确定要删除这个联系人吗？')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/contacts/${contactId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showNotification('删除联系人成功', 'success');
            loadContacts();
        } else {
            showNotification('删除失败: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('网络错误: ' + error.message, 'error');
    }
}

// 导出Excel - 简单可靠版
async function exportExcel() {
    console.log('开始导出Excel...');

    try {
        showNotification('正在生成Excel文件，请稍候...', 'info');

        // 方法1：直接在新窗口打开（最简单）
        window.open(`${API_BASE}/contacts/export`, '_blank');

        // 方法2：使用传统的下载方式
        /*
        const response = await fetch(`${API_BASE}/contacts/export`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const blob = await response.blob();

        // 创建下载链接
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = '通讯录.xlsx';

        // 直接点击
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        // 清理
        setTimeout(() => {
            URL.revokeObjectURL(url);
            showNotification('导出成功！', 'success');
        }, 100);
        */

    } catch (error) {
        console.error('导出错误:', error);
        showNotification('导出失败: ' + error.message, 'error');
    }
}

// 显示导入模态框
function showImportModal() {
    document.getElementById('excelFile').value = '';
    openModal('importModal');
}

// 上传Excel文件
async function uploadExcel() {
    const fileInput = document.getElementById('excelFile');
    const file = fileInput.files[0];

    if (!file) {
        showNotification('请选择要导入的文件', 'error');
        return;
    }

    // 检查文件类型
    const validExtensions = ['.xlsx', '.xls', '.csv'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(fileExtension)) {
        showNotification('只支持 .xlsx, .xls, .csv 格式的文件', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        showNotification('正在导入文件，请稍候...', 'info');

        const response = await fetch(`${API_BASE}/contacts/import`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            showNotification(result.message, 'success');

            if (result.errors && result.errors.length > 0) {
                console.warn('导入错误详情:', result.errors);
                // 可以在这里显示详细的错误信息
                if (result.errors.length > 0) {
                    const errorMsg = result.errors.map(e => `第${e.行号}行: ${e.错误}`).join('\n');
                    console.error('导入错误:', errorMsg);
                }
            }

            closeModal('importModal');
            loadContacts();
        } else {
            showNotification('导入失败: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('导入失败: ' + error.message, 'error');
    }
}

// 添加联系方式行
function addMethod() {
    const methodsContainer = document.getElementById('contactMethods');
    const methodRow = document.createElement('div');
    methodRow.className = 'method-row';
    methodRow.innerHTML = `
        <select class="method-type">
            <option value="phone">电话</option>
            <option value="email">邮箱</option>
            <option value="social">社交媒体</option>
            <option value="address">地址</option>
        </select>
        <input type="text" class="method-value" placeholder="联系方式">
        <input type="text" class="method-label" placeholder="标签（可选）">
        <button type="button" class="remove-method" onclick="removeMethod(this)">×</button>
    `;
    methodsContainer.appendChild(methodRow);
}

// 移除联系方式行
function removeMethod(button) {
    const methodRow = button.parentElement;
    const methodsContainer = document.getElementById('contactMethods');

    if (methodsContainer.children.length > 1) {
        methodRow.remove();
    } else {
        // 如果是最后一行，清空输入框
        methodRow.querySelector('.method-value').value = '';
        methodRow.querySelector('.method-label').value = '';
    }
}

// 打开模态框
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// 关闭模态框
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
    document.body.style.overflow = 'auto';
}

// HTML转义
function escapeHtml(text) {
    if (text === null || text === undefined) {
        return '';
    }
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 点击模态框外部关闭
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
};

// 显示错误
function showError(message) {
    console.error(message);
    const errorDiv = document.createElement('div');
    errorDiv.className = 'notification error';
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);

    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadContacts();

    // 初始化按钮状态
    document.querySelector('.btn-group .btn-secondary:nth-child(1)').classList.add('active');

    // 添加快捷键支持
    document.addEventListener('keydown', function(e) {
        // Ctrl+F 聚焦搜索框
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Escape 关闭所有模态框
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal').forEach(modal => {
                if (modal.style.display === 'flex') {
                    modal.style.display = 'none';
                    document.body.style.overflow = 'auto';
                }
            });
        }
    });
});