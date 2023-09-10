# coding:utf-8

from datetime import date
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Employee(models.Model):
    _inherit = "hr.employee"

    emprunt_ids = fields.One2many(
        'emprunt', 
        'employee_id',
        string='Emprunts', 
        tracking=True)
    
    reservation_ids = fields.One2many(
        'reservation', 
        'employee_id', 
        string='Reservations', 
        tracking=True)
