# coding:utf-8
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class RetourEmprunt(models.Model):
    _name = 'retour.emprunt'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Retour du Matériel Emprunté'
    
    user_id = fields.Many2one(
        'res.users', 
        string="Utilisateur",
        tracking=True,
        default=lambda self: self.env.user)
    
    code_emprunt = fields.Char(
        string='Code Emprunt', 
        required=True, 
        tracking=True)
    
    employee_id = fields.Many2one(
        'hr.employee', 
        string='Employé',
        tracking=True, 
        default=lambda self: self.env.user.employee_id)
    
    material_id = fields.Many2one(
        'material', 
        string='Matériel Emprunté', 
        tracking=True)
    
    return_date = fields.Date(
        string='Date de Retour', 
        default=fields.Date.today(), 
        required=True, 
        tracking=True)
    
    quantity_returned = fields.Integer(
        string='Quantité Retournée', 
        tracking=True)
    
    @api.onchange('code_emprunt')
    def _onchange_code_emprunt(self):
        if self.code_emprunt:
            emprunt = self.env['emprunt'].search(
                [('code', '=', self.code_emprunt), ('state', '=', 'validated')], limit=1)
            if not emprunt:
                raise ValidationError("Aucun emprunt trouvé avec ce code ou l'emprunt n'est pas validé.")
            self.employee_id = emprunt.employee_id
            self.material_id = emprunt.material_id
            self.quantity_returned = emprunt.quantity
        else:
            self.employee_id = False
            self.material_id = False
            self.quantity_returned = 0
    
    def return_materials(self):
        for record in self:
            if not record.code_emprunt:
                raise ValidationError("Veuillez entrer le code d'emprunt.")
            emprunt = self.env['emprunt'].search(
                [('code', '=', record.code_emprunt)], limit=1)
            if not emprunt:
                raise ValidationError("Aucun emprunt trouvé avec ce code ou l'emprunt n'est pas validé.")
            if emprunt.state != 'validated':
                raise ValidationError("L'emprunt associé à ce code n'est pas validé.")
            record.code_emprunt = emprunt.code # Utiliser le code de l'emprunt pour le retour
            retour_vals = {
                'return_date': fields.Date.today(),
                'employee_id': emprunt.employee_id.id,
                'material_id': emprunt.material_id.id,
                'quantity_returned': emprunt.quantity,
                'code_emprunt': emprunt.code,
            }# Enregistrer les informations de retour dans un modèle de retour
            self.env['retour.emprunt'].create(retour_vals)
            emprunt.state = 'returned'# Mettre à jour l'état de l'emprunt
