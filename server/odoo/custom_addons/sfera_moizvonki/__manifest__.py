{
    'name': 'Sfera Moi Zvonki Integration',
    'version': '1.0',
    'summary': 'Integrate Moi Zvonki IP Telephony with Odoo',
    'category': 'CRM',
    'author': 'Antigravity',
    'depends': ['base', 'crm', 'mail', 'sfera_admission_custom'],
    'data': [
        'data/moizvonki_data.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/res_config_settings_views.xml',
        'views/moizvonki_call_views.xml',
        'views/res_users_views.xml',
    ],
    'installable': True,
    'application': True,
}
