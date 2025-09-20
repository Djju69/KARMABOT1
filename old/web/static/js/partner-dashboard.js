/**
 * Partner Dashboard JavaScript
 * Handles partner cabinet functionality
 */

class PartnerDashboard {
    constructor() {
        this.currentSection = 'dashboard';
        this.cards = [];
        this.categories = [];
        this.statistics = {};
        this.currentPage = 1;
        this.totalPages = 1;
        
        this.init();
    }

    async init() {
        // Setup event listeners
        this.setupEventListeners();
        
        // Load initial data
        await this.loadDashboardData();
        await this.loadCategories();
        
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

        // Category change handler
        document.getElementById('card-category')?.addEventListener('change', (e) => {
            this.loadSubcategories(e.target.value);
        });

        // City change handler
        document.getElementById('card-city')?.addEventListener('change', (e) => {
            this.loadAreas(e.target.value);
        });

        // Form submissions
        document.getElementById('add-card-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitCard();
        });

        document.getElementById('create-qr-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitQR();
        });

        document.getElementById('partner-settings-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSettings();
        });

        // Search and filter
        document.getElementById('search-input')?.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.filterCards();
            }, 500);
        });
    }

    async loadDashboardData() {
        try {
            const response = await fetch('/api/partner/statistics', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                this.statistics = await response.json();
                this.updateDashboardStats();
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Ошибка загрузки данных дашборда');
        }
    }

    async loadCategories() {
        try {
            const response = await fetch('/partner/categories', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                this.categories = await response.json();
                this.populateCategorySelects();
            }
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    async loadCards(page = 1, filters = {}) {
        try {
            const params = new URLSearchParams({
                page: page.toString(),
                limit: '10',
                ...filters
            });

            const response = await fetch(`/partner/cards?${params}`, {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.cards = data.items || [];
                this.currentPage = page;
                this.renderCards();
            }
        } catch (error) {
            console.error('Error loading cards:', error);
            this.showError('Ошибка загрузки карточек');
        }
    }

    async loadQRCodes() {
        try {
            const response = await fetch('/user/qr-codes', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderQRCodes(data);
            }
        } catch (error) {
            console.error('Error loading QR codes:', error);
            this.showError('Ошибка загрузки QR-кодов');
        }
    }

    updateDashboardStats() {
        document.getElementById('total-cards').textContent = this.statistics.total_cards || 0;
        document.getElementById('active-cards').textContent = this.statistics.active_cards || 0;
        document.getElementById('total-views').textContent = this.statistics.total_views || 0;
        document.getElementById('total-scans').textContent = this.statistics.total_scans || 0;
        document.getElementById('conversion-rate').textContent = `${this.statistics.conversion_rate || 0}%`;
        document.getElementById('recent-scans').textContent = this.statistics.recent_scans || 0;

        // Update popular cards
        const popularCardsList = document.getElementById('popular-cards-list');
        if (this.statistics.popular_cards && this.statistics.popular_cards.length > 0) {
            popularCardsList.innerHTML = this.statistics.popular_cards.map(card => `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div>
                        <strong>${card.title}</strong>
                        <small class="text-muted d-block">${card.views} просмотров</small>
                    </div>
                    <span class="badge bg-primary">${card.scans} сканирований</span>
                </div>
            `).join('');
        } else {
            popularCardsList.innerHTML = '<div class="text-center text-muted">Нет данных</div>';
        }
    }

    populateCategorySelects() {
        const selects = ['card-category', 'category-filter'];
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                select.innerHTML = '<option value="">Выберите категорию</option>' +
                    this.categories.map(cat => 
                        `<option value="${cat.id}">${cat.emoji || ''} ${cat.name}</option>`
                    ).join('');
            }
        });
    }

    async loadSubcategories(categoryId) {
        if (!categoryId) {
            document.getElementById('card-subcategory').innerHTML = '<option value="">Выберите подкатегорию</option>';
            return;
        }

        try {
            const response = await fetch(`/partner/subcategories?category_id=${categoryId}`, {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                const subcategories = await response.json();
                const select = document.getElementById('card-subcategory');
                select.innerHTML = '<option value="">Выберите подкатегорию</option>' +
                    subcategories.map(sub => `<option value="${sub.id}">${sub.name}</option>`).join('');
            }
        } catch (error) {
            console.error('Error loading subcategories:', error);
        }
    }

    async loadCities() {
        try {
            const response = await fetch('/partner/cities', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                const cities = await response.json();
                const select = document.getElementById('card-city');
                select.innerHTML = '<option value="">Выберите город</option>' +
                    cities.map(city => `<option value="${city.id}">${city.name}</option>`).join('');
            }
        } catch (error) {
            console.error('Error loading cities:', error);
        }
    }

    async loadAreas(cityId) {
        if (!cityId) {
            document.getElementById('card-area').innerHTML = '<option value="">Выберите район</option>';
            return;
        }

        try {
            const response = await fetch(`/partner/areas?city_id=${cityId}`, {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                const areas = await response.json();
                const select = document.getElementById('card-area');
                select.innerHTML = '<option value="">Выберите район</option>' +
                    areas.map(area => `<option value="${area.id}">${area.name}</option>`).join('');
            }
        } catch (error) {
            console.error('Error loading areas:', error);
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
            case 'cards':
                this.loadCards();
                break;
            case 'statistics':
                this.loadDashboardData();
                break;
            case 'qr-codes':
                this.loadQRCodes();
                break;
        }
    }

    renderCards() {
        const container = document.getElementById('cards-list');
        
        if (this.cards.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">Карточки не найдены</div>';
            return;
        }

        container.innerHTML = this.cards.map(card => `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-8">
                            <h5 class="card-title">${card.title}</h5>
                            <p class="card-text text-muted">${card.description || 'Описание не указано'}</p>
                            <div class="row">
                                <div class="col-sm-6">
                                    <small class="text-muted">
                                        <i class="fas fa-map-marker-alt"></i> ${card.address || 'Адрес не указан'}
                                    </small>
                                </div>
                                <div class="col-sm-6">
                                    <small class="text-muted">
                                        <i class="fas fa-phone"></i> ${card.contact || 'Контакты не указаны'}
                                    </small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4 text-end">
                            <span class="badge ${this.getStatusBadgeClass(card.status)} mb-2">
                                ${this.getStatusText(card.status)}
                            </span>
                            <div class="btn-group-vertical">
                                <button class="btn btn-sm btn-outline-primary" onclick="partnerDashboard.editCard(${card.id})">
                                    <i class="fas fa-edit"></i> Редактировать
                                </button>
                                <button class="btn btn-sm btn-outline-info" onclick="partnerDashboard.viewCardImages(${card.id})">
                                    <i class="fas fa-images"></i> Фото
                                </button>
                                ${card.status === 'approved' ? `
                                    <button class="btn btn-sm btn-outline-warning" onclick="partnerDashboard.hideCard(${card.id})">
                                        <i class="fas fa-eye-slash"></i> Скрыть
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderQRCodes(qrCodes) {
        const container = document.getElementById('qr-codes-list');
        
        if (qrCodes.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">QR-коды не найдены</div>';
            return;
        }

        container.innerHTML = qrCodes.map(qr => `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-8">
                            <h5 class="card-title">QR-код #${qr.id}</h5>
                            <p class="card-text">
                                <strong>Номинал:</strong> ${qr.value} баллов<br>
                                <strong>Статус:</strong> ${qr.is_active ? 'Активен' : 'Неактивен'}<br>
                                <strong>Создан:</strong> ${new Date(qr.created_at).toLocaleDateString()}
                            </p>
                        </div>
                        <div class="col-md-4 text-end">
                            <div class="mb-2">
                                <img src="${qr.qr_code_url}" alt="QR Code" class="img-thumbnail" style="width: 100px;">
                            </div>
                            <div class="btn-group-vertical">
                                <button class="btn btn-sm btn-outline-primary" onclick="partnerDashboard.downloadQR(${qr.id})">
                                    <i class="fas fa-download"></i> Скачать
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="partnerDashboard.deactivateQR(${qr.id})">
                                    <i class="fas fa-ban"></i> Деактивировать
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    getStatusBadgeClass(status) {
        const classes = {
            'pending': 'bg-warning',
            'approved': 'bg-success',
            'published': 'bg-primary',
            'archived': 'bg-secondary',
            'blocked': 'bg-danger'
        };
        return classes[status] || 'bg-secondary';
    }

    getStatusText(status) {
        const texts = {
            'pending': 'На модерации',
            'approved': 'Одобрено',
            'published': 'Опубликовано',
            'archived': 'Архив',
            'blocked': 'Заблокировано'
        };
        return texts[status] || status;
    }

    async submitCard() {
        const formData = {
            category_id: parseInt(document.getElementById('card-category').value),
            subcategory_id: document.getElementById('card-subcategory').value ? parseInt(document.getElementById('card-subcategory').value) : null,
            city_id: document.getElementById('card-city').value ? parseInt(document.getElementById('card-city').value) : null,
            area_id: document.getElementById('card-area').value ? parseInt(document.getElementById('card-area').value) : null,
            title: document.getElementById('card-title').value,
            description: document.getElementById('card-description').value,
            contact: document.getElementById('card-contact').value,
            address: document.getElementById('card-address').value,
            discount_text: document.getElementById('card-discount').value,
            google_maps_url: document.getElementById('card-maps').value
        };

        try {
            const response = await fetch('/partner/cards', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getToken()}`
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                this.showSuccess('Карточка успешно создана!');
                bootstrap.Modal.getInstance(document.getElementById('addCardModal')).hide();
                document.getElementById('add-card-form').reset();
                this.loadCards();
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Ошибка создания карточки');
            }
        } catch (error) {
            console.error('Error creating card:', error);
            this.showError('Ошибка создания карточки');
        }
    }

    async submitQR() {
        const formData = {
            card_id: parseInt(document.getElementById('qr-card').value),
            value: parseInt(document.getElementById('qr-value').value),
            expires_days: parseInt(document.getElementById('qr-expires').value)
        };

        try {
            const response = await fetch('/user/qr-codes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getToken()}`
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                this.showSuccess('QR-код успешно создан!');
                bootstrap.Modal.getInstance(document.getElementById('createQRModal')).hide();
                document.getElementById('create-qr-form').reset();
                this.loadQRCodes();
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Ошибка создания QR-кода');
            }
        } catch (error) {
            console.error('Error creating QR code:', error);
            this.showError('Ошибка создания QR-кода');
        }
    }

    async saveSettings() {
        const formData = {
            display_name: document.getElementById('partner-name').value,
            phone: document.getElementById('partner-phone').value,
            email: document.getElementById('partner-email').value
        };

        try {
            const response = await fetch('/partner/settings', {
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

    async editCard(cardId) {
        // Implementation for editing card
        this.showInfo('Функция редактирования в разработке');
    }

    async viewCardImages(cardId) {
        // Implementation for viewing card images
        this.showInfo('Функция просмотра фото в разработке');
    }

    async hideCard(cardId) {
        if (confirm('Вы уверены, что хотите скрыть эту карточку?')) {
            try {
                const response = await fetch(`/partner/cards/${cardId}/hide`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.getToken()}`
                    }
                });

                if (response.ok) {
                    this.showSuccess('Карточка скрыта');
                    this.loadCards();
                } else {
                    this.showError('Ошибка скрытия карточки');
                }
            } catch (error) {
                console.error('Error hiding card:', error);
                this.showError('Ошибка скрытия карточки');
            }
        }
    }

    async downloadQR(qrId) {
        // Implementation for downloading QR code
        this.showInfo('Функция скачивания в разработке');
    }

    async deactivateQR(qrId) {
        if (confirm('Вы уверены, что хотите деактивировать этот QR-код?')) {
            try {
                const response = await fetch(`/user/qr-codes/${qrId}/deactivate`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.getToken()}`
                    }
                });

                if (response.ok) {
                    this.showSuccess('QR-код деактивирован');
                    this.loadQRCodes();
                } else {
                    this.showError('Ошибка деактивации QR-кода');
                }
            } catch (error) {
                console.error('Error deactivating QR code:', error);
                this.showError('Ошибка деактивации QR-кода');
            }
        }
    }

    filterCards() {
        const status = document.getElementById('status-filter').value;
        const category = document.getElementById('category-filter').value;
        const search = document.getElementById('search-input').value;

        const filters = {};
        if (status) filters.status = status;
        if (category) filters.category_id = category;
        if (search) filters.q = search;

        this.loadCards(1, filters);
    }

    showAddCardModal() {
        this.loadCities();
        bootstrap.Modal.getOrCreateInstance(document.getElementById('addCardModal')).show();
    }

    showCreateQRModal() {
        // Load approved cards for QR creation
        this.loadApprovedCards();
        bootstrap.Modal.getOrCreateInstance(document.getElementById('createQRModal')).show();
    }

    async loadApprovedCards() {
        try {
            const response = await fetch('/partner/cards?status=approved', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                const select = document.getElementById('qr-card');
                select.innerHTML = '<option value="">Выберите карточку</option>' +
                    data.items.map(card => `<option value="${card.id}">${card.title}</option>`).join('');
            }
        } catch (error) {
            console.error('Error loading approved cards:', error);
        }
    }

    getToken() {
        // Get token from localStorage or cookie
        return localStorage.getItem('auth_token') || this.getCookie('authToken');
    }

    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
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
    partnerDashboard.showSection(section);
}

function showAddCardModal() {
    partnerDashboard.showAddCardModal();
}

function showCreateQRModal() {
    partnerDashboard.showCreateQRModal();
}

function submitCard() {
    partnerDashboard.submitCard();
}

function submitQR() {
    partnerDashboard.submitQR();
}

function filterCards() {
    partnerDashboard.filterCards();
}

function refreshData() {
    partnerDashboard.loadDashboardData();
}

// Initialize dashboard when page loads
let partnerDashboard;
document.addEventListener('DOMContentLoaded', () => {
    partnerDashboard = new PartnerDashboard();
});
