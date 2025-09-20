# -*- coding: utf-8 -*-
{
    'name': 'KarmaBot Core',
    'version': '1.0.0',
    'summary': 'Core models and access rights for KarmaBot',
    'description': """
        KarmaBot Core Module
        ===================
        
        This module provides the core functionality for KarmaBot:
        - User management with Telegram integration
        - Access rights and security groups
        - Base models for loyalty system
        - SSO authentication for WebApp
        
        Features:
        - Telegram user synchronization
        - Role-based access control (USER, PARTNER, ADMIN, SUPER_ADMIN)
        - Points and loyalty tracking
        - Security groups and permissions
    """,
    'author': 'KarmaBot Team',
    'website': 'https://karmabot.example.com',
    'category': 'Marketing/Loyalty',
    'depends': [
        'base',
        'website',
        'mail',
        'portal',
    ],
    'data': [
        # Security
        'security/karmabot_groups.xml',
        'security/ir.model.access.csv',
        'security/ir.rule.csv',
        
        # Data
        'data/categories_data.xml',
        'data/loyalty_programs_data.xml',
        
        # Views
        'views/karmabot_user_views.xml',
        'views/category_views.xml',
        'views/menu_views.xml',
        'views/user_cabinet_templates.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'external_dependencies': {
        'python': ['requests', 'jwt'],
    },
}
