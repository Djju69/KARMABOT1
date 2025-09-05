// KARMABOT1 Main JavaScript

class KarmaBotApp {
    constructor() {
        this.apiBase = '/api';
        this.user = null;
        this.init();
    }

    init() {
        this.loadUser();
        this.setupEventListeners();
        this.setupNotifications();
    }

    // User Management
    async loadUser() {
        try {
            const response = await this.apiCall('/user/profile');
            if (response.ok) {
                this.user = await response.json();
                this.updateUserInterface();
            }
        } catch (error) {
            console.error('Error loading user:', error);
        }
    }

    updateUserInterface() {
        if (this.user) {
            const userNameElement = document.getElementById('userName');
            if (userNameElement) {
                userNameElement.textContent = this.user.first_name || 'Пользователь';
            }
        }
    }

    // API Calls
    async apiCall(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, finalOptions);
            return response;
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }

    // Stats Loading
    async loadUserStats() {
        try {
            const response = await this.apiCall('/user/profile');
            if (response.ok) {
                const data = await response.json();
                this.displayStats(data);
            }
        } catch (error) {
            console.error('Error loading stats:', error);
            this.showError('Ошибка загрузки статистики');
        }
    }

    displayStats(data) {
        const statsContainer = document.getElementById('statsContainer');
        if (!statsContainer) return;

        const stats = [
            {
                icon: 'fas fa-coins',
                value: data.loyalty_balance || 0,
                label: 'Баллы лояльности',
                color: 'warning'
            },
            {
                icon: 'fas fa-qrcode',
                value: data.qr_codes_count || 0,
                label: 'QR-коды',
                color: 'success'
            },
            {
                icon: 'fas fa-users',
                value: data.referrals_count || 0,
                label: 'Рефералы',
                color: 'info'
            },
            {
                icon: 'fas fa-chart-line',
                value: data.total_earned || 0,
                label: 'Заработано',
                color: 'primary'
            }
        ];

        statsContainer.innerHTML = stats.map(stat => `
            <div class="col-md-3 mb-3">
                <div class="stats-card">
                    <div class="icon text-${stat.color}">
                        <i class="${stat.icon}"></i>
                    </div>
                    <div class="value text-${stat.color}">${stat.value}</div>
                    <div class="label">${stat.label}</div>
                </div>
            </div>
        `).join('');
    }

    // Recent Activity
    async loadRecentActivity() {
        try {
            const response = await this.apiCall('/user/activity');
            if (response.ok) {
                const data = await response.json();
                this.displayRecentActivity(data);
            }
        } catch (error) {
            console.error('Error loading recent activity:', error);
        }
    }

    displayRecentActivity(activities) {
        const container = document.getElementById('recentActivity');
        if (!container) return;

        if (!activities || activities.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">Нет недавней активности</p>';
            return;
        }

        container.innerHTML = activities.map(activity => `
            <div class="d-flex align-items-center mb-3 p-3 bg-light rounded">
                <div class="me-3">
                    <i class="fas fa-${this.getActivityIcon(activity.type)} fa-2x text-${this.getActivityColor(activity.type)}"></i>
                </div>
                <div class="flex-grow-1">
                    <h6 class="mb-1">${activity.title}</h6>
                    <p class="mb-0 text-muted">${activity.description}</p>
                </div>
                <div class="text-muted">
                    <small>${this.formatDate(activity.created_at)}</small>
                </div>
            </div>
        `).join('');
    }

    getActivityIcon(type) {
        const icons = {
            'loyalty_earned': 'coins',
            'qr_created': 'qrcode',
            'qr_redeemed': 'check-circle',
            'referral_signup': 'user-plus',
            'referral_earned': 'gift'
        };
        return icons[type] || 'circle';
    }

    getActivityColor(type) {
        const colors = {
            'loyalty_earned': 'warning',
            'qr_created': 'success',
            'qr_redeemed': 'info',
            'referral_signup': 'primary',
            'referral_earned': 'success'
        };
        return colors[type] || 'secondary';
    }

    // QR Code Management
    async createQRCode(data) {
        try {
            const response = await this.apiCall('/qr/codes/generate', {
                method: 'POST',
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const result = await response.json();
                this.showSuccess('QR-код успешно создан!');
                return result;
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Ошибка создания QR-кода');
            }
        } catch (error) {
            console.error('Error creating QR code:', error);
            this.showError('Ошибка создания QR-кода');
        }
    }

    async loadQRCodes() {
        try {
            const response = await this.apiCall('/qr/codes');
            if (response.ok) {
                const data = await response.json();
                this.displayQRCodes(data);
            }
        } catch (error) {
            console.error('Error loading QR codes:', error);
            this.showError('Ошибка загрузки QR-кодов');
        }
    }

    displayQRCodes(qrCodes) {
        const container = document.getElementById('qrCodesContainer');
        if (!container) return;

        if (!qrCodes || qrCodes.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">У вас пока нет QR-кодов</p>';
            return;
        }

        container.innerHTML = qrCodes.map(qr => `
            <div class="col-md-4 mb-3">
                <div class="card">
                    <div class="card-body text-center">
                        <img src="${qr.qr_image}" class="qr-code-image mb-3" alt="QR Code">
                        <h6 class="card-title">${qr.description}</h6>
                        <p class="card-text">
                            <span class="badge bg-${qr.is_used ? 'secondary' : 'success'}">
                                ${qr.is_used ? 'Использован' : 'Активен'}
                            </span>
                        </p>
                        <p class="card-text">
                            <small class="text-muted">
                                Скидка: ${qr.discount_value} ${qr.discount_type}
                            </small>
                        </p>
                        <p class="card-text">
                            <small class="text-muted">
                                Истекает: ${this.formatDate(qr.expires_at)}
                            </small>
                        </p>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Referral Management
    async loadReferrals() {
        try {
            const response = await this.apiCall('/user/referrals');
            if (response.ok) {
                const data = await response.json();
                this.displayReferrals(data);
            }
        } catch (error) {
            console.error('Error loading referrals:', error);
            this.showError('Ошибка загрузки рефералов');
        }
    }

    displayReferrals(data) {
        const container = document.getElementById('referralsContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body text-center">
                            <i class="fas fa-link fa-3x text-primary mb-3"></i>
                            <h5>Ваша реферальная ссылка</h5>
                            <div class="input-group mb-3">
                                <input type="text" class="form-control" value="${data.referral_link}" readonly>
                                <button class="btn btn-outline-primary" onclick="app.copyToClipboard('${data.referral_link}')">
                                    <i class="fas fa-copy"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body text-center">
                            <i class="fas fa-users fa-3x text-success mb-3"></i>
                            <h5>Статистика рефералов</h5>
                            <div class="row">
                                <div class="col-6">
                                    <div class="value text-primary">${data.total_referrals}</div>
                                    <div class="label">Всего рефералов</div>
                                </div>
                                <div class="col-6">
                                    <div class="value text-success">${data.total_earned}</div>
                                    <div class="label">Заработано</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Utility Functions
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showSuccess('Ссылка скопирована в буфер обмена!');
        } catch (error) {
            console.error('Error copying to clipboard:', error);
            this.showError('Ошибка копирования');
        }
    }

    // Notifications
    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'danger');
    }

    showInfo(message) {
        this.showNotification(message, 'info');
    }

    showNotification(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
        }

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    setupNotifications() {
        // Check for URL parameters to show notifications
        const urlParams = new URLSearchParams(window.location.search);
        const message = urlParams.get('message');
        const type = urlParams.get('type');

        if (message) {
            this.showNotification(decodeURIComponent(message), type || 'info');
        }
    }

    // Event Listeners
    setupEventListeners() {
        // QR Code form submission
        const qrForm = document.getElementById('qrCodeForm');
        if (qrForm) {
            qrForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(qrForm);
                const data = Object.fromEntries(formData);
                
                const result = await this.createQRCode(data);
                if (result) {
                    this.loadQRCodes();
                }
            });
        }

        // Copy buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('copy-btn')) {
                const text = e.target.dataset.copy;
                this.copyToClipboard(text);
            }
        });
    }
}

// Initialize the app
const app = new KarmaBotApp();

// Global functions for HTML onclick handlers
window.app = app;

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KarmaBotApp;
}
