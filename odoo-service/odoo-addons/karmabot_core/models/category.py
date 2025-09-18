# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class KarmaBotCategory(models.Model):
    """KarmaBot Category Model - Categories for partner cards"""
    
    _name = 'karmabot.category'
    _description = 'KarmaBot Category'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        help="Category name"
    )
    
    name_ru = fields.Char(
        string='Name (Russian)',
        translate=True,
        help="Category name in Russian"
    )
    
    name_en = fields.Char(
        string='Name (English)',
        translate=True,
        help="Category name in English"
    )
    
    name_vi = fields.Char(
        string='Name (Vietnamese)',
        translate=True,
        help="Category name in Vietnamese"
    )
    
    name_ko = fields.Char(
        string='Name (Korean)',
        translate=True,
        help="Category name in Korean"
    )
    
    description = fields.Text(
        string='Description',
        translate=True,
        help="Category description"
    )
    
    icon = fields.Char(
        string='Icon',
        help="Icon code or emoji for the category"
    )
    
    color = fields.Char(
        string='Color',
        default='#007bff',
        help="Hex color code for the category"
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Display order"
    )
    
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether the category is active"
    )
    
    # Related data
    partner_cards = fields.One2many(
        'karmabot.partner.card',
        'category_id',
        string='Partner Cards',
        help="Cards in this category"
    )
    
    cards_count = fields.Integer(
        string='Cards Count',
        compute='_compute_cards_count',
        help="Number of cards in this category"
    )
    
    @api.depends('partner_cards')
    def _compute_cards_count(self):
        for record in self:
            record.cards_count = len(record.partner_cards.filtered('is_published'))
    
    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if not record.name:
                raise ValidationError(_("Category name is required"))
    
    def get_localized_name(self, lang='ru'):
        """Get localized category name"""
        self.ensure_one()
        if lang == 'ru':
            return self.name_ru or self.name
        elif lang == 'en':
            return self.name_en or self.name
        elif lang == 'vi':
            return self.name_vi or self.name
        elif lang == 'ko':
            return self.name_ko or self.name
        else:
            return self.name
    
    def action_view_cards(self):
        """View cards in this category"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cards in %s') % self.name,
            'res_model': 'karmabot.partner.card',
            'view_mode': 'tree,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id},
        }
