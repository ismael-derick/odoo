# coding :  utf-8

from odoo import models, fields


class TypeMateriel(models.Model):
    _name = 'type.materiel'
    _description = 'Type de Matériel'
    
    code = fields.Char('code')
    
    name = fields.Char(
        string='Nom', 
        required=True)
