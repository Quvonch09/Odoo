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
        # Robust phone matching (last 9 digits for Uzbekistan)
        phone = vals.get('phone')
        if phone:
            phone_clean = ''.join(filter(str.isdigit, phone))
            if len(phone_clean) >= 9:
                phone_match = '%' + phone_clean[-9:]
                
                # Search partner
                partner = self.env['res.partner'].search(['|', ('phone', 'ilike', phone_match), ('mobile', 'ilike', phone_match)], limit=1)
                if partner:
                    vals['partner_id'] = partner.id
                
                # Search lead
                lead = self.env['crm.lead'].search(['|', ('student_phone', 'ilike', phone_match), ('parent_phone', 'ilike', phone_match), ('phone', 'ilike', phone_match)], limit=1)
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
            message += f"<br/><audio controls src='{res.recording_url}' style='width:100%; height:30px;'></audio>"
        else:
            message += "<br/><i>Ovoz yozuvi mavjud emas (yoki hali yuklanmagan)</i>"

        if res.lead_id:
            res.lead_id.sudo().message_post(body=message)
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
            res.partner_id.sudo().message_post(body=message)
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

        # Fetch last 3 days of calls to ensure nothing is missed
        from_date = int((datetime.now() - timedelta(days=3)).timestamp())
        
        url = f"https://{api_address}/api/v1"
        data = {
            'api_key': api_key,
            'user_name': user_name,
            'action': 'calls.list',
            'from_date': from_date,
        }
        
        try:
            _logger.info("Moi Zvonki Sync: Starting sync with from_date %s", from_date)
            response = requests.post(url, json=data, timeout=30)
            
            # Log the raw response for debugging
            _logger.info("Moi Zvonki Sync: HTTP %s | Body: %s", response.status_code, response.text)
            
            if response.status_code == 200:
                res_json = response.json()
                calls = res_json.get('results', [])
                if not calls and isinstance(res_json, list):
                    calls = res_json  # Some API versions return a straight list
                
                _logger.info("Moi Zvonki Sync: Found %s calls to process", len(calls))
                
                for call in calls:
                    call_id = str(call.get('id') or call.get('id_call') or call.get('uid'))
                    if not call_id: continue
                    
                    existing = self.search([('name', '=', call_id)], limit=1)
                    if not existing:
                        _logger.info("Moi Zvonki Sync: Creating record for call %s", call_id)
                        
                        # Mapping fields based on common Moi Zvonki API names
                        rec_url = call.get('recording') or call.get('link') or call.get('recording_url')
                        direction_val = str(call.get('direction', ''))
                        direction = 'in' if direction_val in ('0', 'incoming', 'inbound') else 'out'
                        
                        status_val = str(call.get('status', '')).lower()
                        is_answered = call.get('is_answered') or status_val in ('answered', 'success', '1')
                        
                        self.create({
                            'name': call_id,
                            'phone': call.get('phone') or call.get('from_number') or call.get('to_number') or call.get('src') or call.get('dst'),
                            'direction': direction,
                            'status': 'answered' if is_answered else 'missed',
                            'duration': int(call.get('duration') or 0),
                            'recording_url': rec_url,
                            'start_time': call.get('start_time') or datetime.now(),
                        })
            else:
                _logger.error("Moi Zvonki Sync: API error %s: %s", response.status_code, response.text)
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
