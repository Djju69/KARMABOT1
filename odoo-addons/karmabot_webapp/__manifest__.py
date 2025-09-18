# -*- coding: utf-8 -*-
{
    'name': 'KarmaBot WebApp',
    'version': '1.0.0',
    'summary': 'Web application interfaces and SSO for KarmaBot',
    'description': """
        KarmaBot WebApp Module
        ======================
        
        This module provides web application interfaces and SSO functionality:
        - SSO authentication and token management
        - WebApp landing page with role-based routing
        - Admin dashboard with live analytics
        - Super admin control panel
        - Mobile-responsive interfaces
        
        Features:
        - JWT-based SSO authentication
        - Role-based access control
        - Live dashboard with real-time updates
        - Mobile-optimized interfaces
        - Integration with Telegram bot
        - Analytics and reporting tools
    """,
    'author': 'KarmaBot Team',
    'website': 'https://karmabot.example.com',
    'category': 'Marketing/Loyalty',
    'depends': [
        'karmabot_core',
        'karmabot_cards', 
        'karmabot_loyalty',
        'website',
        'mail',
        'portal',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Views
        'views/webapp_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
