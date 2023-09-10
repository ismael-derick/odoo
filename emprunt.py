# coding:utf-8

import random
import string
from datetime import date
from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Emprunt(models.Model):
    _name = 'emprunt'
    _description = 'Emprunt'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # variable
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        required=True,
        tracking=True, default=lambda self: self.env.user.employee_id)

    material_id = fields.Many2one(
        'material', 
        string='Material', 
        required=True, 
        tracking=True, 
        default=1)

    objetif = fields.Text(
        string='Objetif', 
        required=True, 
        tracking=True)

    type_materiel_id = fields.Many2one(
        'type.materiel', 
        string='type_materiel')

    user_id = fields.Many2one(
        'res.users', 
        string="Utilisateur",
        tracking=True, 
        default=lambda self: self.env.user)

    quantity = fields.Integer(
        string='Quantity', 
        required=True, 
        tracking=True, 
        default=1)

    jour_debut_date = fields.Date(
        string="Date debut ",
        required=True,
        default=fields.Date.today(), 
        tracking=True)

    jour_retour_date = fields.Date(
        string="Date retour ", 
        tracking=True)

    code = fields.Char(
        string="Code Emprunt",
        readonly=True,
        default=lambda self: self._generate_code())

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('validated', 'Validé'),
        ('rejected', 'Rejeté'),
        ('returned', 'Retourné'),
        ],  default='draft', 
            string='Statut',
            tracking=True)

    @api.onchange('type_materiel_id')
    def _onchange_type_materiel_id(self):
        for rec in self:
            domain = []
            if rec.type_materiel_id:
                domain.append(('type_materiel_id', '=',
                            rec.type_materiel_id.id))
            return {
                "domain": {"material_id": domain}
                }

    # validation par l'admi
    def admin_validate_emprunt(self):
        self.ensure_one()
        self.write({'state': 'validated'})
        self._check_stock_availability()
        self.material_id.stock_quantity -= self.quantity
        self.send_notification('Emprunt validé', 'L\'emprunt a été validé par l\'administrateur : ) .')

    def admin_reject_emprunt(self):
        self.ensure_one()
        self.write({'state': 'rejected'})
        self.send_notification('Emprunt rejeté', 'L\'emprunt a été rejeté par l\'administrateur : ) .')

    # controle des emprint exitant
    @api.constrains('quantity', 'material_id', 'jour_debut_date')
    def _check_stock_availability(self):
        for emprunt in self:
            if emprunt.jour_debut_date and emprunt.material_id and emprunt.quantity > 0:
                existing_emprunts = self.search([
                    ('material_id', '=', emprunt.material_id.id),
                    ('jour_debut_date', '<=', emprunt.jour_retour_date),
                    ('jour_retour_date', '>=', emprunt.jour_debut_date),
                ])
                total_existing_quantity = sum(
                    existing_emprunts.mapped('quantity'))
                available_stock = emprunt.material_id.stock_quantity - total_existing_quantity
                if emprunt.quantity <= available_stock:
                    # Stock disponible
                    emprunt.material_id.stock_quantity -= emprunt.quantity
                    emprunt.send_notification('Emprunt validé', 'Votre demande d\'emprunt a été validée : ) .')
                else:
                    # Stock insuffisant
                    emprunt.send_notification('Emprunt rejeté', 'Le stock est insuffisant pour cet emprunt : ) .')

    def send_notification(self, subject, message):
        for emprunt in self:
            emprunt.employee_id.message_post(body=message, subject=subject)

    # controle de dates
    @api.constrains('jour_debut_date', 'jour_retour_date')
    def _check_dates(self):
        for emprunt in self:
            if emprunt.jour_debut_date and emprunt.jour_retour_date:
                if emprunt.jour_debut_date > emprunt.jour_retour_date:
                    raise ValidationError("La date de début doit être antérieure à la date de retour : ) .")

    def _check_conflicts(self):  # chevochement de date
        for emprunt in self:
            if emprunt.jour_debut_date and emprunt.jour_retour_date:
                existing_emprunts = self.search([
                    ('material_id', '=', emprunt.material_id.id),
                    ('id', '!=', emprunt.id),
                    # Ne vérifier que les emprunts non rejetés
                    ('state', '!=', 'rejected'),
                    '|', '|',
                    ('jour_debut_date', '<=', emprunt.jour_debut_date),
                    ('jour_retour_date', '>=', emprunt.jour_debut_date),
                    ('jour_debut_date', '<=', emprunt.jour_retour_date),
                ])
                if existing_emprunts:
                    emprunt.send_notification('Emprunt impossible','Cet emprunt entre en conflit avec un autre emprunt déjà existant.')
                    raise ValidationError('Cet emprunt entre en conflit avec un autre emprunt déjà existant : ) .')

    # controle de la quantite a enprunté
    @api.constrains('quantity')
    def _check_quantity(self):
        for emprunt in self:
            if emprunt.quantity <= 0:
                raise ValidationError("La quantité doit être supérieure à zéro : ) .")

    def update_stock_after_emprunt(self):
        for emprunt in self:
            if emprunt.quantity > 0 and emprunt.material_id:
                emprunt.material_id.stock_quantity -= emprunt.quantity

    def update_stock_after_return(self):
        for emprunt in self:
            if emprunt.quantity > 0 and emprunt.material_id:
                emprunt.material_id.stock_quantity += emprunt.quantity

    def validate_emprunt(self):
        self._check_stock_availability()
        self.update_stock_after_emprunt()
        self.send_notification('Emprunt validé', 'Votre demande d\'emprunt a été validée : ) .') 
        
    # controle de la quantite de matereil retouné
    def confirm_return(self):
        for record in self:
            if record.quantity_returned <= 0:
                raise ValueError("La quantité retournée doit être supérieure à zéro : ).")
            if record.quantity_returned > record.material_id.quantite_emprunte:
                raise ValueError("La quantité retournée ne peut pas être supérieure à la quantité empruntée : ) .")
            record.material_id.quantite_emprunte -= record.quantity_returned
            self.update_stock_after_return()

    # controle de l'emprunt du méme materiel le meme jour
    @api.constrains('jour_debut_date', 'jour_retour_date', 'employee_id', 'material_id')
    def _check_duplicate_emprunt(self):
        for emprunt in self:
            if emprunt.jour_debut_date and emprunt.jour_retour_date and emprunt.employee_id and emprunt.material_id:
                existing_emprunts = self.search([
                    ('employee_id', '=', emprunt.employee_id.id),
                    ('material_id', '=', emprunt.material_id.id),
                    ('id', '!=', emprunt.id),
                    ('jour_debut_date', '<=', emprunt.jour_retour_date),
                    ('jour_retour_date', '>=', emprunt.jour_debut_date),
                ])
                if existing_emprunts:
                    raise ValidationError("vous ne pouvez pas faire plusieurs emprunts du même matériel le même jour : ) .")

    # generateur de code d'emprunt unique
    @staticmethod
    def _generate_code():
        characters = string.ascii_uppercase + string.digits
        code = ''.join(random.choice(characters)
                    for _ in range(8))  # Génère un code de 8 caractères
        return code

    # Fonction pour créer un emprunt par un employé
    def create_emprunt(self, material_ids, objetif, jour_debut_date, jour_retour_date):
        employee_id = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        if not employee_id:
            raise ValidationError("Aucun employé trouvé associé à cet utilisateur : ).")
        emprunt_vals = {
            'employee_id': employee_id.id,
            'material_ids': [(6, 0, material_ids.ids)],
            'objetif': objetif,
            'jour_debut_date': jour_debut_date,
            'jour_retour_date': jour_retour_date,
            'state': 'draft',  # État initial en mode brouillon
        }
        emprunt = self.env['emprunt'].create(emprunt_vals)
        return emprunt

    # Fonction pour l'administrateur pour valider un emprunt
    def admin_validate_emprunt(self):
        self.ensure_one()
        if not self.env.user.has_group('base.group_erp_manager'):
            raise ValidationError("Vous n'avez pas les permissions pour valider cet emprunt : ).")
        self.write({'state': 'validated'})
        self._check_stock_availability()
        self.material_id.stock_quantity -= self.quantity
        self.send_notification('Emprunt validé', 'L\'emprunt a été validé par l\'administrateur : ) .')
