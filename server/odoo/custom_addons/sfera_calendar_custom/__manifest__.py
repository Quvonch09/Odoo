{
    'name': 'Sfera Calendar Custom',
    'version': '1.0',
    'category': 'Education',
    'summary': 'Custom Calendar for Lesson Sessions',
    'author': 'Antigravity',
    'depends': [
        'openeducat_core', 
        'openeducat_lesson_custom', 
        'openeducat_attendance',
        'mail'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sfera_calendar_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
