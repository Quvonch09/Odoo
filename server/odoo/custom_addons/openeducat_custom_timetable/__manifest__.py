{
    'name': 'OpenEduCat Custom Timetable',
    'version': '1.0',
    'category': 'Education',
    'depends': ['openeducat_core', 'openeducat_timetable', 'website', 'sfera_calendar_custom'],
    'data': [
        'security/ir.model.access.csv',
        'views/op_batch_view_inherit.xml',
        'views/op_student_view_inherit.xml',
        'views/portal_templates.xml',
        'views/public_holiday_view.xml',
    ],
    'installable': True,
}