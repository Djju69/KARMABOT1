# -*- coding: utf-8 -*-
{
    'name': 'KarmaBot Cards',
    'version': '1.0.0',
    'summary': 'Partner cards management for KarmaBot',
    'description': """
        KarmaBot Cards Module
        ====================
        
        This module provides partner card management functionality:
        - Partner card creation and management
        - Card moderation workflow
        - QR code generation and management
        - Card analytics and statistics
        - Partner dashboard
        
        Features:
        - Card creation with photos and details
        - Moderation workflow (draft -> pending -> approved/rejected)
        - QR code generation for each card
        - Card analytics and scan tracking
        - Partner self-service portal
    """,
    'author': 'KarmaBot Team',
    'website': 'https://karmabot.example.com',
    'category': 'Marketing/Loyalty',
    'depends': [
        'karmabot_core',
        'website',
        'mail',
        'portal',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/ir.rule.csv',
        
        # Data
        'data/card_categories_data.xml',
        
        # Views
        'views/partner_card_views.xml',
        'views/qr_code_views.xml',
        'views/partner_cabinet_templates.xml',
        
        # Controllers
        'controllers/partner_cabinet_controller.py',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
}
