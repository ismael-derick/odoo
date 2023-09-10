# coding:utf-8
from datetime import date
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Material(models.Model):
    _name = 'material'
    _description = 'material'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string='Nom', 
        required=True)

    stock_quantity = fields.Integer(
        string='Stock Quantity', 
        default=1, 
        tracking=True)
    
    quantite_emprunte = fields.Integer(
        string='Quantite Emprunte', 
        compute='_compute_quantities', 
        store=True)
    
    quantite_reserve = fields.Integer(
        string='Quantite reservé', 
        compute='_compute_quantities', 
        store=True)
    
    emprunt_ids = fields.One2many(
        'emprunt', 
        'material_id', 
        string='Emprunts')

    reservation_ids = fields.One2many(
        'reservation', 
        'material_id', 
        string='Reservations')
    
    Model = fields.Char(
        string='Model',  
        required=True)

    etiquette = fields.Char(
        string="Etiquette",  
        required=True, 
        tracking=True)

    marque = fields.Char(
        string="Marque", 
        tracking=True)

    image = fields.Binary(string="Image")

    type_materiel_id = fields.Many2one(
        'type.materiel', 
        string='type_materiel')
    
    etat = fields.Selection([
        ('bon_etat', 'Bon Etat'),
        ('mauvais_etat', 'Mauvais Etat')
        ], 
            default='bon_etat', 
            string='Etat', tracking=True)

    @api.depends('emprunt_ids', 'reservation_ids')
    def _compute_quantities(self):
        for material in self:
            material.quantite_emprunte = sum(
                material.emprunt_ids.mapped('quantity'))
            material.quantite_reserve = sum(
                material.reservation_ids.mapped('quantity'))
