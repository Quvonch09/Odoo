
import os
import sys

# Add Odoo path to sys.path
sys.path.append(r'c:\odoo-19\server')

# Minimal Odoo environment setup
import odoo
from odoo import api, SUPERUSER_ID

# Mocking a configuration to load the environment
config_file = r'c:\odoo-19\server\odoo.conf'
odoo.tools.config.parse_config(['-c', config_file])
registry = odoo.registry(odoo.tools.config['db_name'])

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Set parameters
    env['ir.config_parameter'].sudo().set_param('sfera_moizvonki.api_key', '5c27ir101zns8aa9xvkad97m2ajookbo')
    env['ir.config_parameter'].sudo().set_param('sfera_moizvonki.api_address', 'sferaacademy.moizvonki.ru')
    env['ir.config_parameter'].sudo().set_param('sfera_moizvonki.user_name', 'sferaacademy')
    
    # Map Admin
    admin_user = env['res.users'].search([('login', '=', 'admin')], limit=1)
    if admin_user:
        employee_mapping = env['moizvonki.employee'].sudo().search([('user_id', '=', admin_user.id)], limit=1)
        if not employee_mapping:
            env['moizvonki.employee'].sudo().create({
                'user_id': admin_user.id,
                'moizvonki_id': 'sferaacademy',
            })
        else:
            employee_mapping.write({'moizvonki_id': 'sferaacademy'})
            
    cr.commit()
    print("Moi Zvonki configuration updated successfully.")
