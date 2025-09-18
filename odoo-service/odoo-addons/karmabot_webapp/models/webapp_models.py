# -*- coding: utf-8 -*-

from odoo import models, fields, api

class WebAppUser(models.Model):
    _name = 'webapp.user'
    _description = 'WebApp User'
    
    name = fields.Char('Name', required=True)
    telegram_id = fields.Char('Telegram ID')
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    is_active = fields.Boolean('Active', default=True)
