from odoo import models, fields, api
from odoo.exceptions import ValidationError
import requests
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class MoizvonkiCall(models.Model):
    _name = 'moizvonki.call'
    _description = 'Moi Zvonki Call'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_time desc'

    name = fields.Char(string='Call ID', required=True, tracking=True)
    phone = fields.Char(string='Phone Number', required=True, tracking=True)
    direction = fields.Selection([
        ('in', 'Incoming'),
        ('out', 'Outgoing')
    ], string='Direction', tracking=True)
    status = fields.Selection([
        ('answered', 'Answered'),
        ('missed', 'Missed'),
        ('rejected', 'Rejected')
    ], string='Status', tracking=True)
    duration = fields.Integer(string='Duration (seconds)', tracking=True)
    start_time = fields.Datetime(string='Start Time', tracking=True)
    recording_url = fields.Char(string='Recording URL', tracking=True)
    user_id = fields.Many2one('res.users', string='Employee', tracking=True)
    lead_id = fields.Many2one('crm.lead', string='Lead', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True)

    @api.model
    def create(self, vals):
        # Clean phone number (keep only digits)
        phone = vals.get('phone')
        if phone:
            phone_clean = ''.join(filter(str.isdigit, phone))
            
            # Try to find partner
            partner = self.env['res.partner'].search(['|', ('phone', 'ilike', phone_clean), ('mobile', 'ilike', phone_clean)], limit=1)
            if partner:
                vals['partner_id'] = partner.id
            
            # Try to find lead
            lead = self.env['crm.lead'].search(['|', ('phone', 'ilike', phone_clean), ('mobile', 'ilike', phone_clean)], limit=1)
            if lead:
                vals['lead_id'] = lead.id

        res = super(MoizvonkiCall, self).create(vals)
        
        # Post message to Lead and Partner chatter
        direction_text = "Kiruvchi" if res.direction == 'in' else "Chiquvchi"
        status_text = "Javob berilgan" if res.status == 'answered' else "O'tkazib yuborilgan"
        duration_text = f"{res.duration // 60} min {res.duration % 60} sek"
        
        message = (
            f"<b>Moi Zvonki: Qo'ng'iroq qayd etildi</b><br/>"
            f"Turi: {direction_text}<br/>"
            f"Holati: {status_text}<br/>"
            f"Davomiyligi: {duration_text}<br/>"
        )
        if res.recording_url:
            message += f"Suhbat yozuvi: <a href='{res.recording_url}' target='_blank'>Eshitish</a>"

        if res.lead_id:
            res.lead_id.message_post(body=message)
            # Create completed activity
            self.env['mail.activity'].sudo().create({
                'res_id': res.lead_id.id,
                'res_model_id': self.env['ir.model']._get('crm.lead').id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_call').id,
                'summary': f"{direction_text} qo'ng'iroq: {status_text}",
                'note': message,
                'user_id': res.user_id.id or self.env.uid,
                'date_deadline': fields.Date.today(),
            }).action_done()

        if res.partner_id:
            res.partner_id.message_post(body=message)
            # Create completed activity
            self.env['mail.activity'].sudo().create({
                'res_id': res.partner_id.id,
                'res_model_id': self.env['ir.model']._get('res.partner').id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_call').id,
                'summary': f"{direction_text} qo'ng'iroq: {status_text}",
                'note': message,
                'user_id': res.user_id.id or self.env.uid,
                'date_deadline': fields.Date.today(),
            }).action_done()
            
        return res

    @api.model
    def cron_fetch_calls(self):
        """ Fetch calls from Moi Zvonki API periodically """
        api_key = self.env['ir.config_parameter'].sudo().get_param('sfera_moizvonki.api_key')
        api_address = self.env['ir.config_parameter'].sudo().get_param('sfera_moizvonki.api_address')
        user_name = self.env['ir.config_parameter'].sudo().get_param('sfera_moizvonki.user_name')
        
        if not api_key or not api_address or not user_name:
            return

        # Fetch last 24 hours of calls (using timestamp)
        from_date = int((datetime.now() - timedelta(days=1)).timestamp())
        
        url = f"https://{api_address}/api/v1"
        data = {
            'api_key': api_key,
            'user_name': user_name,
            'action': 'calls.list',
            'from_date': from_date,
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                calls = response.json().get('results', [])
                for call in calls:
                    # Check if call already exists
                    existing = self.search([('name', '=', str(call.get('id')))], limit=1)
                    if not existing:
                        self.create({
                            'name': str(call.get('id')),
                            'phone': call.get('phone'),
                            'direction': 'in' if call.get('direction') == 'incoming' else 'out',
                            'status': 'answered' if call.get('is_answered') else 'missed',
                            'duration': call.get('duration'),
                            'recording_url': call.get('recording_url'),
                            'start_time': call.get('start_time'),
                        })
        except Exception as e:
            _logger.error("Error fetching Moi Zvonki calls: %s", str(e))

    @api.model
    def action_make_call(self, phone):
        """ Initiate a call from Odoo to a customer via Moi Zvonki """
        if not phone:
            return
            
        api_key = self.env['ir.config_parameter'].sudo().get_param('sfera_moizvonki.api_key')
        api_address = self.env['ir.config_parameter'].sudo().get_param('sfera_moizvonki.api_address')
        user_name = self.env['ir.config_parameter'].sudo().get_param('sfera_moizvonki.user_name')
        
        if not api_key or not api_address or not user_name:
            raise ValidationError("Moi Zvonki sozlamalari to'liq kiritilmagan!")

        # Use mapped Moi Zvonki User ID
        employee = self.env['moizvonki.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        if not employee:
            raise ValidationError("Siz administrator sifatida Moi Zvonki ID bilan bog'lanmagansiz! (Moi Zvonki -> Employees menyusiga kiring)")
            
        moizvonki_user_id = employee.moizvonki_id

        url = f"https://{api_address}/api/v1"
        data = {
            'api_key': api_key,
            'user_name': user_name,
            'action': 'calls.initiate',
            'user': moizvonki_user_id,
            'phone': phone,
        }
        
        try:
            # Try POST with JSON first
            _logger.info("Moi Zvonki Call: Sending POST request to %s with payload %s", url, data)
            response = requests.post(url, json=data, timeout=20)
            
            _logger.info("Moi Zvonki Call: Received Status %s, Body: %s", response.status_code, response.text)
            
            if not response.text:
                # If body is empty, try as Form Data instead of JSON
                _logger.info("Moi Zvonki Call: Empty response with JSON, retrying with Form Data")
                response = requests.post(url, data=data, timeout=20)
                _logger.info("Moi Zvonki Call (Form): Received Status %s, Body: %s", response.status_code, response.text)

            if response.status_code == 200:
                if not response.text:
                    raise ValidationError("Moi Zvonki serveri bo'sh javob qaytardi. Iltimos, API sozlamalarini tekshiring.")
                
                try:
                    res_data = response.json()
                    if res_data.get('status') == 'error':
                        raise ValidationError(f"Moi Zvonki Xatosi: {res_data.get('message')}")
                    
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Bog\'lanish!',
                            'message': f"{phone} raqamiga qo'ng'iroq buyrug'i yuborildi. Telefoningizga qarang.",
                            'type': 'success',
                        }
                    }
                except ValueError:
                    raise ValidationError(f"Noma'lum javob formati (Moi Zvonki): {response.text[:200]}")
            else:
                raise ValidationError(f"Moi Zvonki Server xatosi ({response.status_code}): {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            raise ValidationError(f"Tarmoq xatosi (Internet yoki DNS): {str(e)}")
        except Exception as e:
            if isinstance(e, ValidationError): raise e
            raise ValidationError(f"Qo'ng'iroq qilib bo'lmadi: {str(e)}")
