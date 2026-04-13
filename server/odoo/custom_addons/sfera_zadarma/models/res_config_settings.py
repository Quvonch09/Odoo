from odoo import _, fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    zadarma_api_key = fields.Char(string='Zadarma API Key', config_parameter='sfera_zadarma.api_key')
    zadarma_secret_key = fields.Char(string='Zadarma Secret Key', config_parameter='sfera_zadarma.secret_key')
    zadarma_webhook_url = fields.Char(
        string='Webhook URL',
        compute='_compute_zadarma_webhook_url',
        readonly=True,
    )

    def _compute_zadarma_webhook_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '').rstrip('/')
        for record in self:
            record.zadarma_webhook_url = f'{base_url}/zadarma/webhook' if base_url else False

    def action_zadarma_test_connection(self):
        self.ensure_one()
        api_key = (self.zadarma_api_key or self.env['ir.config_parameter'].sudo().get_param('sfera_zadarma.api_key') or '').strip()
        secret_key = (self.zadarma_secret_key or self.env['ir.config_parameter'].sudo().get_param('sfera_zadarma.secret_key') or '').strip()
        if not api_key or not secret_key:
            raise ValidationError(_("Fill in Zadarma API Key and Secret Key first."))

        result = self.env['zadarma.call']._zadarma_api_request('/v1/info/balance/', params={'format': 'json'})
        balance = result.get('balance')
        currency = result.get('currency')
        message = _("Connection established successfully.")
        if balance is not None and currency:
            message = _("Connection established successfully. Balance: %(balance)s %(currency)s", balance=balance, currency=currency)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Zadarma'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }
