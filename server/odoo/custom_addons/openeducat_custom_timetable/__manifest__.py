{
    'name': 'OpenEduCat Custom Timetable',
    'version': '1.0',
    'category': 'Education',
    'summary': 'Custom Timetable and Attendance Dashboard',
    'author': 'Antigravity',
    'depends': ['openeducat_core', 'openeducat_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'views/attendance_dashboard_view.xml',
        'views/op_batch_view_inherit.xml',
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'openeducat_custom_timetable/static/src/attendance_dashboard.js',
            'openeducat_custom_timetable/static/src/attendance_dashboard.xml',
            'openeducat_custom_timetable/static/src/attendance_dashboard.scss',
        ],
        'web.assets_frontend': [
            'openeducat_custom_timetable/static/src/scss/teacher_portal.scss',
        ],
    },
    'installable': True,
    'application': True,
}