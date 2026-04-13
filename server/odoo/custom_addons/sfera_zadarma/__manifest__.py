{
    'name': 'Sfera Zadarma Integration',
    'version': '1.1',
    'category': 'Sales/CRM',
    'summary': 'Zadarma telephony integration for CRM',
    'description': 'Integration with Zadarma (Novofon) for click-to-call, webhook logging and CRM matching.',
    'author': 'Sfera Academy',
    'depends': ['base', 'crm', 'mail', 'sfera_admission_custom'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/res_users_views.xml',
        'views/crm_lead_views.xml',
        'views/crm_lead_form_style_views.xml',
        'views/zadarma_call_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sfera_zadarma/static/src/scss/crm_lead_form.scss',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
