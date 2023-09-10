# -*- coding: utf-8 -*-

{
    'name': "Gestions des Emprunts",

    'version': '1.0',

    'author': 'AFT-ISMAEL',

    'category': 'Gestion,inventory',

    'summary': "Gestion d'emprunt des materiels par les employés",

    'license': 'LGPL-3',

    'description': """
        Ce module permet de gérer les emprunts de material par les employés.
        Il offre des fonctionnalités pour les employés et les administrateurs.
    """,

    'depends': ['base', 'hr', "mail"],

    'data': [
        'security/ir.model.access.csv',
        "security/ir_rule.xml",
        "security/security.xml",
        "views/emprunt.xml",
        "views/materiel.xml",
        "views/reservation.xml",
        "views/retour_emprunt.xml",
        "views/type.xml",
        'views/views.xml',
    ],
    
    'installable': True,
    'application': True,
    'auto_install': False,
}
