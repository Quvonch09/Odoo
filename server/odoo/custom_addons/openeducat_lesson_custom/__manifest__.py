{
    'name': 'OpenEduCat Lesson Custom',
    'version': '1.0',
    'category': 'Education',
    'summary': 'Manage Lesson Plans for Courses',
    'author': 'Antigravity',
    'depends': ['openeducat_core'],
    'data': [
        'security/ir.model.access.csv',
        'views/op_lesson_view.xml',
        'views/op_course_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
