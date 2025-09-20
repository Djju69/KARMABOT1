/**
 * KarmaBot WebApp JavaScript
 * Handles client-side functionality for the web application
 */

class KarmaBotWebApp {
    constructor() {
        this.ssoToken = null;
        this.userInfo = null;
        this.init();
    }

    init() {
        this.loadSSOToken();
        this.setupEventListeners();
        this.initializeComponents();
    }

    loadSSOToken() {
        // Get SSO token from URL parameters or localStorage
        const urlParams = new URLSearchParams(window.location.search);
        this.ssoToken = urlParams.get('sso') || localStorage.getItem('karmabot_sso_token');
        
        if (this.ssoToken) {
            localStorage.setItem('karmabot_sso_token', this.ssoToken);
            this.validateSSOToken();
        }
    }

    async validateSSOToken() {
        try {
            const response = await fetch('/karmabot/sso/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sso_token: this.ssoToken
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.userInfo = data.user_info;
                this.updateUI();
            } else {
                this.handleSSOError(data.error);
            }
        } catch (error) {
            console.error('Error validating SSO token:', error);
            this.handleSSOError('Network error');
        }
    }

    updateUI() {
        // Update user information in the UI
        if (this.userInfo) {
            const userNameElement = document.getElementById('user-name');
            if (userNameElement) {
                userNameElement.textContent = this.userInfo.display_name;
            }

            const userRoleElement = document.getElementById('user-role');
            if (userRoleElement) {
                userRoleElement.textContent = this.userInfo.role;
            }

            // Show role-specific content
            this.showRoleSpecificContent();
        }
    }

    showRoleSpecificContent() {
        const role = this.userInfo.role;
        
        // Hide all role-specific sections
        document.querySelectorAll('.role-specific').forEach(section => {
            section.style.display = 'none';
        });

        // Show relevant section
        const relevantSection = document.getElementById(`${role}-section`);
        if (relevantSection) {
            relevantSection.style.display = 'block';
        }

        // Update navigation
        this.updateNavigation();
    }

    updateNavigation() {
        const role = this.userInfo.role;
        const navButtons = document.querySelectorAll('.nav-button');
        
        navButtons.forEach(button => {
            const requiredRole = button.dataset.role;
            if (requiredRole && requiredRole !== role) {
                button.style.display = 'none';
            } else {
                button.style.display = 'block';
            }
        });
    }

    setupEventListeners() {
        // Add event listeners for various interactions
        document.addEventListener('click', this.handleClick.bind(this));
        document.addEventListener('submit', this.handleSubmit.bind(this));
        
        // Auto-refresh functionality
        this.setupAutoRefresh();
    }

    handleClick(event) {
        const target = event.target;
        
        // Handle button clicks
        if (target.classList.contains('btn')) {
            this.handleButtonClick(target);
        }
        
        // Handle card clicks
        if (target.closest('.card-item')) {
            this.handleCardClick(target.closest('.card-item'));
        }
    }

    handleButtonClick(button) {
        const action = button.dataset.action;
        
        switch (action) {
            case 'open-cabinet':
                this.openCabinet();
                break;
            case 'refresh-data':
                this.refreshData();
                break;
            case 'moderate-card':
                this.moderateCard(button.dataset.cardId, button.dataset.action);
                break;
            case 'view-analytics':
                this.viewAnalytics();
                break;
            case 'manage-users':
                this.manageUsers();
                break;
            case 'system-settings':
                this.systemSettings();
                break;
            default:
                console.log('Unknown button action:', action);
        }
    }

    handleCardClick(cardElement) {
        const cardId = cardElement.dataset.cardId;
        if (cardId) {
            this.viewCardDetails(cardId);
        }
    }

    handleSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
        
        // Handle form submission
        this.submitForm(form, formData);
    }

    async openCabinet() {
        try {
            const response = await fetch('/karmabot/webapp/cabinet-url', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.ssoToken}`
                },
                body: JSON.stringify({
                    role: this.userInfo.role,
                    telegram_id: this.userInfo.telegram_id
                })
            });

            const data = await response.json();
            
            if (data.success) {
                window.open(data.cabinet_url, '_blank');
            } else {
                this.showError('Error opening cabinet: ' + data.error);
            }
        } catch (error) {
            console.error('Error opening cabinet:', error);
            this.showError('Network error');
        }
    }

    async refreshData() {
        const loadingElement = document.getElementById('loading-spinner');
        if (loadingElement) {
            loadingElement.style.display = 'block';
        }

        try {
            const response = await fetch('/karmabot/webapp/dashboard-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.ssoToken}`
                },
                body: JSON.stringify({
                    role: this.userInfo.role
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.updateDashboardData(data.data);
            } else {
                this.showError('Error refreshing data: ' + data.error);
            }
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showError('Network error');
        } finally {
            if (loadingElement) {
                loadingElement.style.display = 'none';
            }
        }
    }

    async moderateCard(cardId, action) {
        if (!confirm(`Are you sure you want to ${action} this card?`)) {
            return;
        }

        try {
            const response = await fetch('/karmabot/webapp/moderate-card', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.ssoToken}`
                },
                body: JSON.stringify({
                    card_id: cardId,
                    action: action
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(data.message);
                this.refreshData();
            } else {
                this.showError('Error moderating card: ' + data.error);
            }
        } catch (error) {
            console.error('Error moderating card:', error);
            this.showError('Network error');
        }
    }

    viewAnalytics() {
        const analyticsUrl = `/web#menu_id=karmabot_loyalty.action_karmabot_loyalty_transaction&sso=${this.ssoToken}`;
        window.open(analyticsUrl, '_blank');
    }

    manageUsers() {
        const usersUrl = `/web#menu_id=karmabot_core.action_karmabot_user&sso=${this.ssoToken}`;
        window.open(usersUrl, '_blank');
    }

    systemSettings() {
        const settingsUrl = `/web#menu_id=karmabot_core.menu_karmabot_config&sso=${this.ssoToken}`;
        window.open(settingsUrl, '_blank');
    }

    viewCardDetails(cardId) {
        const cardUrl = `/web#id=${cardId}&model=karmabot.partner.card&view_type=form&sso=${this.ssoToken}`;
        window.open(cardUrl, '_blank');
    }

    async submitForm(form, formData) {
        const formAction = form.dataset.action;
        
        try {
            const response = await fetch(formAction, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.ssoToken}`
                },
                body: JSON.stringify(Object.fromEntries(formData))
            });

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(data.message);
                form.reset();
            } else {
                this.showError('Error: ' + data.error);
            }
        } catch (error) {
            console.error('Error submitting form:', error);
            this.showError('Network error');
        }
    }

    updateDashboardData(data) {
        // Update dashboard metrics
        if (data.user_stats) {
            this.updateElement('total-users', data.user_stats.total_users);
            this.updateElement('active-users', data.user_stats.active_users);
        }

        if (data.card_stats) {
            this.updateElement('pending-cards', data.card_stats.pending_cards);
            this.updateElement('published-cards', data.card_stats.published_cards);
        }

        if (data.recent_activity) {
            this.updateRecentActivity(data.recent_activity);
        }
    }

    updateElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    updateRecentActivity(activity) {
        // Update recent cards
        if (activity.recent_cards) {
            this.updateRecentCards(activity.recent_cards);
        }

        // Update recent users
        if (activity.recent_users) {
            this.updateRecentUsers(activity.recent_users);
        }
    }

    updateRecentCards(cards) {
        const container = document.getElementById('recent-cards-container');
        if (!container) return;

        container.innerHTML = '';
        
        cards.forEach(card => {
            const cardElement = this.createCardElement(card);
            container.appendChild(cardElement);
        });
    }

    updateRecentUsers(users) {
        const container = document.getElementById('recent-users-container');
        if (!container) return;

        container.innerHTML = '';
        
        users.forEach(user => {
            const userElement = this.createUserElement(user);
            container.appendChild(userElement);
        });
    }

    createCardElement(card) {
        const div = document.createElement('div');
        div.className = 'list-group-item';
        div.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">${card.name}</h6>
                <small>${card.created_at}</small>
            </div>
            <p class="mb-1">
                Partner: ${card.partner}<br/>
                Category: ${card.category}
            </p>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-success btn-sm" onclick="webapp.moderateCard(${card.id}, 'approve')">
                    <i class="fa fa-check"></i> Approve
                </button>
                <button class="btn btn-danger btn-sm" onclick="webapp.moderateCard(${card.id}, 'reject')">
                    <i class="fa fa-times"></i> Reject
                </button>
            </div>
        `;
        return div;
    }

    createUserElement(user) {
        const div = document.createElement('div');
        div.className = 'list-group-item';
        div.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">${user.name}</h6>
                <small>${user.created_at}</small>
            </div>
            <p class="mb-1">
                Username: @${user.username || 'No username'}<br/>
                Role: <span class="badge badge-info">${user.role}</span>
            </p>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-info btn-sm" onclick="webapp.viewUser(${user.id})">
                    <i class="fa fa-eye"></i> View
                </button>
                <button class="btn btn-warning btn-sm" onclick="webapp.manageUser(${user.id})">
                    <i class="fa fa-cog"></i> Manage
                </button>
            </div>
        `;
        return div;
    }

    setupAutoRefresh() {
        // Auto-refresh every 30 seconds
        setInterval(() => {
            this.refreshData();
        }, 30000);
    }

    initializeComponents() {
        // Initialize any additional components
        this.initializeCharts();
        this.initializeModals();
    }

    initializeCharts() {
        // Initialize Chart.js charts if present
        const chartElements = document.querySelectorAll('canvas');
        chartElements.forEach(canvas => {
            const chartType = canvas.dataset.chartType;
            if (chartType) {
                this.createChart(canvas, chartType);
            }
        });
    }

    createChart(canvas, type) {
        const ctx = canvas.getContext('2d');
        const data = JSON.parse(canvas.dataset.chartData || '{}');
        
        new Chart(ctx, {
            type: type,
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    initializeModals() {
        // Initialize Bootstrap modals if present
        const modalElements = document.querySelectorAll('.modal');
        modalElements.forEach(modal => {
            // Add modal functionality if needed
        });
    }

    handleSSOError(error) {
        console.error('SSO Error:', error);
        this.showError('Authentication error: ' + error);
        
        // Redirect to login or show error page
        setTimeout(() => {
            window.location.href = '/karmabot/webapp/login';
        }, 3000);
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize the WebApp when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.webapp = new KarmaBotWebApp();
});

// Export for global access
window.KarmaBotWebApp = KarmaBotWebApp;
