from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    moizvonki_api_key = fields.Char(string='Moi Zvonki API Key', config_parameter='sfera_moizvonki.api_key')
    moizvonki_api_address = fields.Char(string='Moi Zvonki API Address', config_parameter='sfera_moizvonki.api_address')
    moizvonki_user_name = fields.Char(string='Moi Zvonki Login (Email)', config_parameter='sfera_moizvonki.user_name')

    def action_moizvonki_test_connection(self):
        """ Test connection to Moi Zvonki API """
        import requests
        api_key = self.moizvonki_api_key or self.env['ir.config_parameter'].sudo().get_param('sfera_moizvonki.api_key')
        api_address = self.moizvonki_api_address or self.env['ir.config_parameter'].sudo().get_param('sfera_moizvonki.api_address')
        user_name = self.moizvonki_user_name or self.env['ir.config_parameter'].sudo().get_param('sfera_moizvonki.user_name')
        
        if not api_key or not api_address or not user_name:
            raise ValidationError("Iltimos, barcha maydonlarni (Key, Address, Login) to'ldiring!")

        # Moi Zvonki API uses a single endpoint for all actions
        # Sometimes need to add /api/v1/ manually if user didn't provide it
        base_address = api_address.replace('https://', '').replace('http://', '').strip('/')
        if not base_address.endswith('/api/v1'):
            url = f"https://{base_address}/api/v1"
        else:
            url = f"https://{base_address}"

        payload = {
            'api_key': api_key,
            'user_name': user_name,
            'action': 'calls.list',
            'from_date': int((fields.Datetime.now() - timedelta(days=7)).timestamp()),
            'limit': 1
        }
        
        try:
            # Try POST with JSON first (Standard for REST v1)
            _logger.info("Moi Zvonki Test: Sending POST request to %s", url)
            response = requests.post(url, json=payload, timeout=20)
            
            _logger.info("Moi Zvonki Test: Received Status %s, Body: %s", response.status_code, response.text)
            
            if not response.text:
                # If body is empty, try as Form Data instead of JSON
                _logger.info("Moi Zvonki Test: Empty response with JSON, retrying with Form Data")
                response = requests.post(url, data=payload, timeout=20)
                _logger.info("Moi Zvonki Test (Form): Received Status %s, Body: %s", response.status_code, response.text)

            if response.status_code == 200:
                if not response.text:
                    raise ValidationError("Moi Zvonki serveri bo'sh javob qaytardi. Iltimos, API key va Login'ni tekshiring.")
                
                try:
                    res_data = response.json()
                    if res_data.get('status') == 'error':
                        raise ValidationError(f"Moi Zvonki Xatosi: {res_data.get('message')}")
                    
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Muvaffaqiyatli!',
                            'message': "Moi Zvonki bilan bog'lanish o'rnatildi!",
                            'type': 'success',
                        }
                    }
                except ValueError:
                    raise ValidationError(f"Noma'lum javob format: {response.text[:200]}")
            else:
                raise ValidationError(f"Server xatosi ({response.status_code}): {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            raise ValidationError(f"Tarmoq xatosi (Internet yoki DNS): {str(e)}")
        except Exception as e:
            if isinstance(e, ValidationError): raise e
            raise ValidationError(f"Kutilmagan xato: {str(e)}")
