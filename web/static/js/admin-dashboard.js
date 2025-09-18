/**
 * Admin Dashboard JavaScript
 * Handles admin panel functionality
 */

class AdminDashboard {
    constructor() {
        this.currentSection = 'dashboard';
        this.charts = {};
        this.currentPage = 1;
        this.totalPages = 1;
        
        this.init();
    }

    async init() {
        // Setup event listeners
        this.setupEventListeners();
        
        // Load initial data
        await this.loadDashboardData();
        
        // Initialize charts
        this.initializeCharts();
        
        // Show dashboard by default
        this.showSection('dashboard');
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('[data-section]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.target.closest('[data-section]').dataset.section;
                this.showSection(section);
            });
        });

        // Form submissions
        document.getElementById('add-user-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitUser();
        });

        document.getElementById('system-settings-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSettings();
        });

        // Search and filter
        document.getElementById('user-search-input')?.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.filterUsers();
            }, 500);
        });
    }

    async loadDashboardData() {
        try {
            const response = await fetch('/api/admin/dashboard', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateDashboardMetrics(data);
                this.updateRecentActivity(data.recent_activity || []);
                this.updateSystemNotifications(data.notifications || []);
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Ошибка загрузки данных дашборда');
        }
    }

    async loadUsers(page = 1, filters = {}) {
        try {
            const params = new URLSearchParams({
                page: page.toString(),
                limit: '20',
                ...filters
            });

            const response = await fetch(`/api/admin/users?${params}`, {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderUsersTable(data);
                this.updatePagination('users', data);
            }
        } catch (error) {
            console.error('Error loading users:', error);
            this.showError('Ошибка загрузки пользователей');
        }
    }

    async loadPartners() {
        try {
            const response = await fetch('/api/admin/partners', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderPartnersTable(data);
            }
        } catch (error) {
            console.error('Error loading partners:', error);
            this.showError('Ошибка загрузки партнеров');
        }
    }

    async loadModerationQueue() {
        try {
            const response = await fetch('/api/admin/moderation/queue', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderModerationTable(data);
            }
        } catch (error) {
            console.error('Error loading moderation queue:', error);
            this.showError('Ошибка загрузки очереди модерации');
        }
    }

    async loadAnalytics(period = 30) {
        try {
            const response = await fetch(`/api/admin/analytics?period=${period}`, {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateAnalyticsCharts(data);
            }
        } catch (error) {
            console.error('Error loading analytics:', error);
            this.showError('Ошибка загрузки аналитики');
        }
    }

    async loadTransactions(page = 1, filters = {}) {
        try {
            const params = new URLSearchParams({
                page: page.toString(),
                limit: '20',
                ...filters
            });

            const response = await fetch(`/api/admin/transactions?${params}`, {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderTransactionsTable(data);
                this.updatePagination('transactions', data);
            }
        } catch (error) {
            console.error('Error loading transactions:', error);
            this.showError('Ошибка загрузки транзакций');
        }
    }

    async loadAuditLog(page = 1) {
        try {
            const params = new URLSearchParams({
                page: page.toString(),
                limit: '50'
            });

            const response = await fetch(`/api/admin/audit-log?${params}`, {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderAuditTable(data);
                this.updatePagination('audit', data);
            }
        } catch (error) {
            console.error('Error loading audit log:', error);
            this.showError('Ошибка загрузки журнала аудита');
        }
    }

    updateDashboardMetrics(data) {
        document.getElementById('total-users').textContent = data.total_users || 0;
        document.getElementById('active-partners').textContent = data.active_partners || 0;
        document.getElementById('pending-moderation').textContent = data.pending_moderation || 0;
        document.getElementById('today-transactions').textContent = data.today_transactions || 0;
    }

    updateRecentActivity(activities) {
        const container = document.getElementById('recent-activity-list');
        
        if (activities.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">Нет активности</div>';
            return;
        }

        container.innerHTML = activities.map(activity => `
            <div class="d-flex align-items-center mb-2">
                <div class="flex-shrink-0">
                    <i class="fas fa-${this.getActivityIcon(activity.type)} text-primary"></i>
                </div>
                <div class="flex-grow-1 ms-3">
                    <div class="small">${activity.description}</div>
                    <div class="text-muted small">${this.formatTime(activity.timestamp)}</div>
                </div>
            </div>
        `).join('');
    }

    updateSystemNotifications(notifications) {
        const container = document.getElementById('system-notifications');
        
        if (notifications.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">Нет уведомлений</div>';
            return;
        }

        container.innerHTML = notifications.map(notification => `
            <div class="alert alert-${this.getNotificationClass(notification.type)} alert-dismissible fade show">
                <i class="fas fa-${this.getNotificationIcon(notification.type)}"></i>
                ${notification.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `).join('');
    }

    renderUsersTable(data) {
        const tbody = document.getElementById('users-table-body');
        
        if (data.users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Пользователи не найдены</td></tr>';
            return;
        }

        tbody.innerHTML = data.users.map(user => `
            <tr>
                <td>${user.id}</td>
                <td>${user.full_name || 'Не указано'}</td>
                <td>${user.email || 'Не указан'}</td>
                <td>${user.telegram_username ? `@${user.telegram_username}` : 'Не привязан'}</td>
                <td><span class="badge ${this.getRoleBadgeClass(user.role)}">${this.getRoleText(user.role)}</span></td>
                <td><span class="badge ${user.is_active ? 'bg-success' : 'bg-secondary'}">${user.is_active ? 'Активен' : 'Неактивен'}</span></td>
                <td>${this.formatDate(user.created_at)}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="adminDashboard.editUser(${user.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-${user.is_active ? 'warning' : 'success'}" onclick="adminDashboard.toggleUserStatus(${user.id})">
                            <i class="fas fa-${user.is_active ? 'ban' : 'check'}"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="adminDashboard.deleteUser(${user.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    renderPartnersTable(data) {
        const tbody = document.getElementById('partners-table-body');
        
        if (data.partners.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Партнеры не найдены</td></tr>';
            return;
        }

        tbody.innerHTML = data.partners.map(partner => `
            <tr>
                <td>${partner.id}</td>
                <td>${partner.display_name || partner.full_name}</td>
                <td>
                    <div class="small">
                        ${partner.email ? `<i class="fas fa-envelope"></i> ${partner.email}<br>` : ''}
                        ${partner.phone ? `<i class="fas fa-phone"></i> ${partner.phone}` : ''}
                    </div>
                </td>
                <td><span class="badge bg-info">${partner.cards_count || 0}</span></td>
                <td><span class="badge ${this.getPartnerStatusBadgeClass(partner.status)}">${this.getPartnerStatusText(partner.status)}</span></td>
                <td>${this.formatDate(partner.created_at)}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="adminDashboard.viewPartner(${partner.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-success" onclick="adminDashboard.approvePartner(${partner.id})">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="btn btn-outline-warning" onclick="adminDashboard.suspendPartner(${partner.id})">
                            <i class="fas fa-pause"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    renderModerationTable(data) {
        const tbody = document.getElementById('moderation-table-body');
        
        if (data.cards.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Нет карточек на модерации</td></tr>';
            return;
        }

        tbody.innerHTML = data.cards.map(card => `
            <tr>
                <td>
                    <div>
                        <strong>${card.title}</strong>
                        <div class="small text-muted">${card.description ? card.description.substring(0, 50) + '...' : 'Описание не указано'}</div>
                    </div>
                </td>
                <td>${card.partner_name}</td>
                <td><span class="badge bg-secondary">${card.category_name}</span></td>
                <td><span class="badge ${this.getCardStatusBadgeClass(card.status)}">${this.getCardStatusText(card.status)}</span></td>
                <td>${this.formatDate(card.created_at)}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="adminDashboard.viewCard(${card.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-success" onclick="adminDashboard.approveCard(${card.id})">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="adminDashboard.rejectCard(${card.id})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    renderTransactionsTable(data) {
        const tbody = document.getElementById('transactions-table-body');
        
        if (data.transactions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Транзакции не найдены</td></tr>';
            return;
        }

        tbody.innerHTML = data.transactions.map(transaction => `
            <tr>
                <td>${transaction.id}</td>
                <td>${transaction.user_name || 'Неизвестно'}</td>
                <td><span class="badge ${this.getTransactionTypeBadgeClass(transaction.type)}">${this.getTransactionTypeText(transaction.type)}</span></td>
                <td class="${transaction.amount >= 0 ? 'text-success' : 'text-danger'}">
                    ${transaction.amount >= 0 ? '+' : ''}${transaction.amount}
                </td>
                <td>${transaction.description || 'Без описания'}</td>
                <td>${this.formatDate(transaction.created_at)}</td>
                <td><span class="badge ${transaction.status === 'completed' ? 'bg-success' : 'bg-warning'}">${this.getTransactionStatusText(transaction.status)}</span></td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="adminDashboard.viewTransaction(${transaction.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        ${transaction.status === 'pending' ? `
                            <button class="btn btn-outline-success" onclick="adminDashboard.approveTransaction(${transaction.id})">
                                <i class="fas fa-check"></i>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `).join('');
    }

    renderAuditTable(data) {
        const tbody = document.getElementById('audit-table-body');
        
        if (data.logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Записи аудита не найдены</td></tr>';
            return;
        }

        tbody.innerHTML = data.logs.map(log => `
            <tr>
                <td>${this.formatDateTime(log.timestamp)}</td>
                <td>${log.user_name || 'Система'}</td>
                <td><span class="badge bg-info">${log.action}</span></td>
                <td>${log.object_type}: ${log.object_id}</td>
                <td>${log.ip_address || 'Неизвестно'}</td>
                <td><span class="badge ${log.success ? 'bg-success' : 'bg-danger'}">${log.success ? 'Успешно' : 'Ошибка'}</span></td>
            </tr>
        `).join('');
    }

    initializeCharts() {
        // User Activity Chart
        const userActivityCtx = document.getElementById('userActivityChart');
        if (userActivityCtx) {
            this.charts.userActivity = new Chart(userActivityCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Новые пользователи',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Cards Status Chart
        const cardsStatusCtx = document.getElementById('cardsStatusChart');
        if (cardsStatusCtx) {
            this.charts.cardsStatus = new Chart(cardsStatusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Одобрено', 'На модерации', 'Отклонено'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: [
                            'rgba(75, 192, 192, 0.8)',
                            'rgba(255, 206, 86, 0.8)',
                            'rgba(255, 99, 132, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }

        // Registrations Chart
        const registrationsCtx = document.getElementById('registrationsChart');
        if (registrationsCtx) {
            this.charts.registrations = new Chart(registrationsCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Регистрации',
                        data: [],
                        backgroundColor: 'rgba(54, 162, 235, 0.8)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Transactions Chart
        const transactionsCtx = document.getElementById('transactionsChart');
        if (transactionsCtx) {
            this.charts.transactions = new Chart(transactionsCtx, {
                type: 'pie',
                data: {
                    labels: ['Начисления', 'Списания', 'Реферальные'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: [
                            'rgba(75, 192, 192, 0.8)',
                            'rgba(255, 99, 132, 0.8)',
                            'rgba(255, 206, 86, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }

    updateAnalyticsCharts(data) {
        // Update user activity chart
        if (this.charts.userActivity && data.user_activity) {
            this.charts.userActivity.data.labels = data.user_activity.labels;
            this.charts.userActivity.data.datasets[0].data = data.user_activity.data;
            this.charts.userActivity.update();
        }

        // Update cards status chart
        if (this.charts.cardsStatus && data.cards_status) {
            this.charts.cardsStatus.data.datasets[0].data = data.cards_status.data;
            this.charts.cardsStatus.update();
        }

        // Update registrations chart
        if (this.charts.registrations && data.registrations) {
            this.charts.registrations.data.labels = data.registrations.labels;
            this.charts.registrations.data.datasets[0].data = data.registrations.data;
            this.charts.registrations.update();
        }

        // Update transactions chart
        if (this.charts.transactions && data.transactions_by_type) {
            this.charts.transactions.data.datasets[0].data = data.transactions_by_type.data;
            this.charts.transactions.update();
        }
    }

    showSection(section) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(el => {
            el.style.display = 'none';
        });

        // Show selected section
        document.getElementById(`${section}-section`).style.display = 'block';

        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`).classList.add('active');

        this.currentSection = section;

        // Load section-specific data
        switch (section) {
            case 'users':
                this.loadUsers();
                break;
            case 'partners':
                this.loadPartners();
                break;
            case 'moderation':
                this.loadModerationQueue();
                break;
            case 'analytics':
                this.loadAnalytics();
                break;
            case 'transactions':
                this.loadTransactions();
                break;
            case 'audit':
                this.loadAuditLog();
                break;
        }
    }

    async submitUser() {
        const formData = {
            full_name: document.getElementById('user-name').value,
            email: document.getElementById('user-email').value,
            telegram_id: document.getElementById('user-telegram').value ? parseInt(document.getElementById('user-telegram').value) : null,
            role: document.getElementById('user-role').value,
            password: document.getElementById('user-password').value
        };

        try {
            const response = await fetch('/api/admin/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getToken()}`
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                this.showSuccess('Пользователь успешно создан!');
                bootstrap.Modal.getInstance(document.getElementById('addUserModal')).hide();
                document.getElementById('add-user-form').reset();
                this.loadUsers();
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Ошибка создания пользователя');
            }
        } catch (error) {
            console.error('Error creating user:', error);
            this.showError('Ошибка создания пользователя');
        }
    }

    async saveSettings() {
        const formData = {
            system_name: document.getElementById('system-name').value,
            system_description: document.getElementById('system-description').value,
            default_language: document.getElementById('default-language').value
        };

        try {
            const response = await fetch('/api/admin/settings', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getToken()}`
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                this.showSuccess('Настройки сохранены!');
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Ошибка сохранения настроек');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showError('Ошибка сохранения настроек');
        }
    }

    async approveCard(cardId) {
        if (confirm('Вы уверены, что хотите одобрить эту карточку?')) {
            try {
                const response = await fetch(`/api/admin/moderation/cards/${cardId}/approve`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.getToken()}`
                    }
                });

                if (response.ok) {
                    this.showSuccess('Карточка одобрена');
                    this.loadModerationQueue();
                } else {
                    this.showError('Ошибка одобрения карточки');
                }
            } catch (error) {
                console.error('Error approving card:', error);
                this.showError('Ошибка одобрения карточки');
            }
        }
    }

    async rejectCard(cardId) {
        const reason = prompt('Укажите причину отклонения:');
        if (reason) {
            try {
                const response = await fetch(`/api/admin/moderation/cards/${cardId}/reject`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.getToken()}`
                    },
                    body: JSON.stringify({ reason })
                });

                if (response.ok) {
                    this.showSuccess('Карточка отклонена');
                    this.loadModerationQueue();
                } else {
                    this.showError('Ошибка отклонения карточки');
                }
            } catch (error) {
                console.error('Error rejecting card:', error);
                this.showError('Ошибка отклонения карточки');
            }
        }
    }

    async toggleUserStatus(userId) {
        try {
            const response = await fetch(`/api/admin/users/${userId}/toggle-status`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                this.showSuccess('Статус пользователя изменен');
                this.loadUsers();
            } else {
                this.showError('Ошибка изменения статуса');
            }
        } catch (error) {
            console.error('Error toggling user status:', error);
            this.showError('Ошибка изменения статуса');
        }
    }

    async deleteUser(userId) {
        if (confirm('Вы уверены, что хотите удалить этого пользователя?')) {
            try {
                const response = await fetch(`/api/admin/users/${userId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${this.getToken()}`
                    }
                });

                if (response.ok) {
                    this.showSuccess('Пользователь удален');
                    this.loadUsers();
                } else {
                    this.showError('Ошибка удаления пользователя');
                }
            } catch (error) {
                console.error('Error deleting user:', error);
                this.showError('Ошибка удаления пользователя');
            }
        }
    }

    filterUsers() {
        const role = document.getElementById('user-role-filter').value;
        const status = document.getElementById('user-status-filter').value;
        const search = document.getElementById('user-search-input').value;

        const filters = {};
        if (role) filters.role = role;
        if (status) filters.status = status;
        if (search) filters.search = search;

        this.loadUsers(1, filters);
    }

    updatePagination(type, data) {
        const pagination = document.getElementById(`${type}-pagination`);
        if (!pagination) return;

        const currentPage = data.current_page || 1;
        const totalPages = data.total_pages || 1;

        let paginationHTML = '';
        
        // Previous button
        if (currentPage > 1) {
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="adminDashboard.load${type.charAt(0).toUpperCase() + type.slice(1)}(${currentPage - 1})">Предыдущая</a></li>`;
        }

        // Page numbers
        for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
            paginationHTML += `<li class="page-item ${i === currentPage ? 'active' : ''}"><a class="page-link" href="#" onclick="adminDashboard.load${type.charAt(0).toUpperCase() + type.slice(1)}(${i})">${i}</a></li>`;
        }

        // Next button
        if (currentPage < totalPages) {
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="adminDashboard.load${type.charAt(0).toUpperCase() + type.slice(1)}(${currentPage + 1})">Следующая</a></li>`;
        }

        pagination.innerHTML = paginationHTML;
    }

    // Utility methods
    getToken() {
        return localStorage.getItem('auth_token') || this.getCookie('authToken');
    }

    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    getRoleBadgeClass(role) {
        const classes = {
            'user': 'bg-secondary',
            'partner': 'bg-info',
            'moderator': 'bg-warning',
            'admin': 'bg-danger',
            'superadmin': 'bg-dark'
        };
        return classes[role] || 'bg-secondary';
    }

    getRoleText(role) {
        const texts = {
            'user': 'Пользователь',
            'partner': 'Партнер',
            'moderator': 'Модератор',
            'admin': 'Администратор',
            'superadmin': 'Супер-админ'
        };
        return texts[role] || role;
    }

    getCardStatusBadgeClass(status) {
        const classes = {
            'pending': 'bg-warning',
            'approved': 'bg-success',
            'rejected': 'bg-danger',
            'published': 'bg-primary'
        };
        return classes[status] || 'bg-secondary';
    }

    getCardStatusText(status) {
        const texts = {
            'pending': 'На модерации',
            'approved': 'Одобрено',
            'rejected': 'Отклонено',
            'published': 'Опубликовано'
        };
        return texts[status] || status;
    }

    getPartnerStatusBadgeClass(status) {
        const classes = {
            'active': 'bg-success',
            'suspended': 'bg-warning',
            'pending': 'bg-info',
            'inactive': 'bg-secondary'
        };
        return classes[status] || 'bg-secondary';
    }

    getPartnerStatusText(status) {
        const texts = {
            'active': 'Активен',
            'suspended': 'Приостановлен',
            'pending': 'На рассмотрении',
            'inactive': 'Неактивен'
        };
        return texts[status] || status;
    }

    getTransactionTypeBadgeClass(type) {
        const classes = {
            'earn': 'bg-success',
            'spend': 'bg-danger',
            'referral': 'bg-info',
            'bonus': 'bg-warning'
        };
        return classes[type] || 'bg-secondary';
    }

    getTransactionTypeText(type) {
        const texts = {
            'earn': 'Начисление',
            'spend': 'Списание',
            'referral': 'Реферальное',
            'bonus': 'Бонус'
        };
        return texts[type] || type;
    }

    getTransactionStatusText(status) {
        const texts = {
            'completed': 'Завершена',
            'pending': 'В обработке',
            'failed': 'Ошибка'
        };
        return texts[status] || status;
    }

    getActivityIcon(type) {
        const icons = {
            'user_registration': 'user-plus',
            'card_approval': 'check-circle',
            'transaction': 'exchange-alt',
            'login': 'sign-in-alt',
            'logout': 'sign-out-alt'
        };
        return icons[type] || 'circle';
    }

    getNotificationClass(type) {
        const classes = {
            'info': 'alert-info',
            'warning': 'alert-warning',
            'error': 'alert-danger',
            'success': 'alert-success'
        };
        return classes[type] || 'alert-info';
    }

    getNotificationIcon(type) {
        const icons = {
            'info': 'info-circle',
            'warning': 'exclamation-triangle',
            'error': 'times-circle',
            'success': 'check-circle'
        };
        return icons[type] || 'info-circle';
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('ru-RU');
    }

    formatDateTime(dateString) {
        return new Date(dateString).toLocaleString('ru-RU');
    }

    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString('ru-RU');
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showError(message) {
        this.showAlert(message, 'danger');
    }

    showInfo(message) {
        this.showAlert(message, 'info');
    }

    showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);

        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }
}

// Global functions for HTML onclick handlers
function showSection(section) {
    adminDashboard.showSection(section);
}

function showAddUserModal() {
    bootstrap.Modal.getOrCreateInstance(document.getElementById('addUserModal')).show();
}

function submitUser() {
    adminDashboard.submitUser();
}

function filterUsers() {
    adminDashboard.filterUsers();
}

function refreshData() {
    adminDashboard.loadDashboardData();
}

function generateReport() {
    adminDashboard.showInfo('Функция генерации отчетов в разработке');
}

function exportUsers() {
    adminDashboard.showInfo('Функция экспорта пользователей в разработке');
}

function exportPartners() {
    adminDashboard.showInfo('Функция экспорта партнеров в разработке');
}

function exportAnalytics() {
    adminDashboard.showInfo('Функция экспорта аналитики в разработке');
}

function exportTransactions() {
    adminDashboard.showInfo('Функция экспорта транзакций в разработке');
}

function exportAuditLog() {
    adminDashboard.showInfo('Функция экспорта журнала аудита в разработке');
}

function clearCache() {
    adminDashboard.showInfo('Функция очистки кэша в разработке');
}

function backupDatabase() {
    adminDashboard.showInfo('Функция резервного копирования БД в разработке');
}

function restartServices() {
    adminDashboard.showInfo('Функция перезапуска сервисов в разработке');
}

function clearAuditLog() {
    adminDashboard.showInfo('Функция очистки журнала аудита в разработке');
}

function approveAllPending() {
    adminDashboard.showInfo('Функция массового одобрения в разработке');
}

function approveAllCards() {
    adminDashboard.showInfo('Функция массового одобрения карточек в разработке');
}

function rejectAllCards() {
    adminDashboard.showInfo('Функция массового отклонения карточек в разработке');
}

function showAddTransactionModal() {
    adminDashboard.showInfo('Функция добавления транзакций в разработке');
}

// Initialize dashboard when page loads
let adminDashboard;
document.addEventListener('DOMContentLoaded', () => {
    adminDashboard = new AdminDashboard();
});
