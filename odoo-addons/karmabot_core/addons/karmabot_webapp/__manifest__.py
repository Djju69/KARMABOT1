# -*- coding: utf-8 -*-
{
    'name': 'KarmaBot WebApp',
    'version': '1.0.0',
    'summary': 'Web application interfaces for KarmaBot',
    'description': """
        KarmaBot WebApp Module
        ======================
        
        This module provides web application interfaces:
        - WebApp landing page
        - Basic routing functionality
        - Integration endpoints
    """,
    'author': 'KarmaBot Team',
    'website': 'https://karmabot.example.com',
    'category': 'Website',
    'depends': [
        'base',
        'web',
    ],
    'data': [
        'views/webapp_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
