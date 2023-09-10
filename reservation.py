# coding:utf-8

from datetime import date
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Reservation(models.Model):
    _name = 'reservation'
    _description = 'Reservation'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    
    employee_id = fields.Many2one(
        'hr.employee', 
        string='Employee', 
        required=True, tracking=True, 
        default=lambda self: self.env.user.employee_id)
    
    user_id = fields.Many2one(
        'res.users', 
        string="Utilisateur", 
        tracking=True,default=lambda self: self.env.user)
    
    material_id = fields.Many2one(
        'material', 
        string='Material', 
        required=True, 
        tracking=True)
    
    objetif = fields.Text(
        string='Objetif', 
        required=True, 
        tracking=True)
    
    quantity = fields.Integer(
        string='Quantity', 
        required=True, 
        tracking=True, 
        default=1 )
    
    reserve_date = fields.Date(
        string="Date réservation", 
        required=True, 
        default=fields.Date.today(), 
        tracking=True)
    
    jour_debut_date = fields.Date(
        string="Date debut ", 
        required=True, 
        tracking=True)
    
    jour_retour_date = fields.Date(
        string="Date retour ", 
        required=True, 
        tracking=True)
    
    type_materiel_id = fields.Many2one(
        'type.materiel', 
        string='type_materiel')
    
    @api.onchange('type_materiel_id')
    def _onchange_type_materiel_id(self):
        for rec in self:
            domain = []
            if rec.type_materiel_id:
                domain.append(('type_materiel_id', '=',
                            rec.type_materiel_id.id))
            return {"domain": {"material_id": domain}}
    
    @api.constrains('reserve_date', 'jour_retour_date')
    def _check_dates(self):
        for Reservation in self:
            if Reservation.reserve_date and Reservation.jour_retour_date:
                if Reservation.reserve_date > Reservation.jour_retour_date:
                    raise ValidationError("La date de début doit être antérieure à la date de retour : ) .")
    @api.constrains('reserve_date', 'jour_debut_date',)
    def _check_dates(self):
        for Reservation in self:
            if Reservation.reserve_date and Reservation.jour_debut_date:
                if Reservation.reserve_date >=Reservation.jour_debut_date >= Reservation.jour_retour_date:
                    raise ValidationError("La date de reservation doit être antérieure à la date de début.")
    
    def _check_conflicts(self):
        for reservation in self:
            if reservation.jour_debut_date and reservation.jour_retour_date:
                existing_reservations = self.search([
                    ('material_id', '=', reservation.material_id.id),
                    ('id', '!=', reservation.id),
                    '|', '|',
                    ('jour_debut_date', '<=', reservation.jour_debut_date),
                    ('jour_retour_date', '>=', reservation.jour_debut_date),
                    ('jour_debut_date', '<=', reservation.jour_retour_date),
                ])
                if existing_reservations:
                    reservation.send_notification('Réservation impossible',
                        'Cette réservation entre en conflit avec une autre réservation déjà existante.')
                    raise ValidationError('Cette réservation entre en conflit avec une autre réservation déjà existante.')