# -*- coding: utf-8 -*-
{
    'name': 'KarmaBot Loyalty',
    'version': '1.0.0',
    'summary': 'Loyalty system and points management for KarmaBot',
    'description': """
        KarmaBot Loyalty Module
        ======================
        
        This module provides comprehensive loyalty system functionality:
        - Points earning and spending
        - Transaction management and fraud detection
        - Level system and achievements
        - Analytics and reporting
        - Anti-fraud mechanisms
        
        Features:
        - QR scan rewards and referral bonuses
        - Points expiration and redemption
        - Fraud detection with geolocation
        - User level progression system
        - Comprehensive transaction logging
        - Analytics dashboard for admins
    """,
    'author': 'KarmaBot Team',
    'website': 'https://karmabot.example.com',
    'category': 'Marketing/Loyalty',
    'depends': [
        'karmabot_core',
        'karmabot_cards',
        'website',
        'mail',
        'portal',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/ir.rule.csv',
        
        # Data
        'data/loyalty_programs_data.xml',
        'data/achievements_data.xml',
        
        # Views
        'views/loyalty_transaction_views.xml',
        'views/loyalty_program_views.xml',
        'views/achievement_views.xml',
        'views/loyalty_analytics_templates.xml',
        
        # Controllers
        'controllers/loyalty_api_controller.py',
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
