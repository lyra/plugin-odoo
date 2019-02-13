# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra-network.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

from hashlib import sha1
import logging
import urlparse
import math
from odoo.addons.payment_lyra.models.language import LyraLanguage

from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_lyra.controllers.main import LyraController
from odoo.addons.payment_lyra.helpers import constants
from odoo import models, api, release, fields, _
from odoo.tools import float_round, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_compare, float_repr
from datetime import datetime

_logger = logging.getLogger(__name__)

class AcquirerLyra(models.Model):
    _inherit = 'payment.acquirer'

    lyra_form_url = 'https://secure.lyra.com/vads-payment/'

    provider = fields.Selection(selection_add=[('lyra', 'Lyra')])
    lyra_site_id = fields.Char(string='Shop ID', required_if_provider='lyra')
    lyra_key_test = fields.Char(string='Key in test mode', required_if_provider='lyra')
    lyra_key_prod = fields.Char(string='Key in production mode', required_if_provider='lyra')
    lyra_sign_algo = fields.Selection(string='Signature algorithm', selection=[('SHA-1', 'SHA-1'), ('SHA-256', 'HMAC-SHA-256')], required_if_provider='lyra')
    lyra_notify_url = fields.Char(string='Instant Payment Notification URL', readonly=True)
    lyra_gateway_url = fields.Char(string='Payment page URL', required_if_provider='lyra')
    lyra_language = fields.Selection(string='Default language', selection='_get_languages')
    lyra_available_languages = fields.Many2many('lyra.language', string='Available languages', column1='code', column2='label')
    lyra_capture_delay = fields.Char(string='Capture delay')
    lyra_validation_mode = fields.Selection(string='Validation mode', selection=[(' ', _('Back Office Configuration')), ('0', _('Automatic')), ('1', _('Manual'))])
    lyra_payment_cards = fields.Char(string='Card types')
    lyra_threeds_min_amount = fields.Char(string='Disable 3DS')
    lyra_redirect_enabled = fields.Selection(string='Redirection enabled', selection=[('0', _('Disabled')), ('1', _('Enabled'))])
    lyra_redirect_success_timeout = fields.Char(string='Redirection timeout on success')
    lyra_redirect_success_message = fields.Char(string='Redirection message on success')
    lyra_redirect_error_timeout = fields.Char(string='Redirection timeout on failure')
    lyra_redirect_error_message = fields.Char(string='Redirection message on failure')
    lyra_return_mode = fields.Selection(string='Return mode', selection=[('GET', 'GET'), ('POST', 'POST')])

    def _get_languages(self):
        languages = constants.LYRA_LANGUAGES
        return list(languages.items())

    def _lyra_generate_digital_sign(self, acquirer, values):
        sign = ''
        for key in sorted(values.iterkeys()):
            if key.startswith('vads_'):
                sign += values[key] + '+'

        sign += self.lyra_secretkey
        shasign = sha1(sign.encode('utf-8')).hexdigest()

        return shasign

    @api.multi
    def lyra_form_generate_values(self, values):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')

        # trans id is number of 1/10 seconds from midnight
        now = datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        delta = int((now - midnight).total_seconds() * 10)
        trans_id = str(delta).rjust(6, '0')

        mode = u'PRODUCTION' if (self.environment == 'prod') else u'TEST'

        # amount in cents
        amount = int(values['amount'] * math.pow(10, int(values['currency'].decimal_places)))

        tx_values = dict() # values to sign in unicode
        tx_values.update({
            'vads_site_id': self.lyra_websitekey,
            'vads_amount': unicode(amount),
            'vads_currency': constants.LYRA_CURRENCIES.get(values['currency'].name),
            'vads_trans_date': unicode(datetime.utcnow().strftime("%Y%m%d%H%M%S")),
            'vads_trans_id': unicode(trans_id),
            'vads_ctx_mode': mode,
            'vads_page_action': u'PAYMENT',
            'vads_action_mode': u'INTERACTIVE',
            'vads_payment_config': u'SINGLE',
            'vads_version': u'V2',
            'vads_url_return': urlparse.urljoin(base_url, LyraController._return_url),
            'vads_return_mode': u'GET',
            'vads_order_id': unicode(values.get('reference')),
            'vads_contrib': u'Odoo10_0.9.1/' + release.version,

            # customer info
            'vads_cust_id': unicode(values.get('billing_partner_id')) or '',
            'vads_cust_first_name': values.get('billing_partner_first_name') and values.get('billing_partner_first_name')[0:62] or '',
            'vads_cust_last_name': values.get('billing_partner_last_name') and values.get('billing_partner_last_name')[0:62] or '',
            'vads_cust_address': values.get('billing_partner_address') and values.get('billing_partner_address')[0:254] or '',
            'vads_cust_zip': values.get('billing_partner_zip') and values.get('billing_partner_zip')[0:62] or '',
            'vads_cust_city': values.get('billing_partner_city') and values.get('billing_partner_city')[0:62] or '',
            'vads_cust_state': values.get('billing_partner_state').code and values.get('billing_partner_state').code[0:62] or '',
            'vads_cust_country': values.get('billing_partner_country').code and values.get('billing_partner_country').code.upper() or '',
            'vads_cust_email': values.get('billing_partner_email') and values.get('billing_partner_email')[0:126] or '',
            'vads_cust_phone': values.get('billing_partner_phone') and values.get('billing_partner_phone')[0:31] or '',

            # shipping info
            'vads_ship_to_first_name': values.get('partner_first_name') and values.get('partner_first_name')[0:62] or '',
            'vads_ship_to_last_name': values.get('partner_last_name') and values.get('partner_last_name')[0:62] or '',
            'vads_ship_to_street': values.get('partner_address') and values.get('partner_address')[0:254] or '',
            'vads_ship_to_zip': values.get('partner_zip') and values.get('partner_zip')[0:62] or '',
            'vads_ship_to_city': values.get('partner_city') and values.get('partner_city')[0:62] or '',
            'vads_ship_to_state': values.get('partner_state').code and values.get('partner_state').code[0:62] or '',
            'vads_ship_to_country': values.get('partner_country').code and values.get('partner_country').code.upper() or '',
            'vads_ship_to_phone_num': values.get('partner_phone') and values.get('partner_phone')[0:31] or '',
        })

        lyra_tx_values = dict() # values encoded in utf-8

        for key in tx_values.iterkeys():
            lyra_tx_values[key] = tx_values[key].encode('utf-8')

        lyra_tx_values['lyra_signature'] = self._lyra_generate_digital_sign(self, tx_values)
        return lyra_tx_values

    @api.multi
    def lyra_get_form_action_url(self):
        return self.lyra_form_url


class TxLyra(models.Model):
    _inherit = 'payment.transaction'

    state_message = fields.Char(string='Transaction log')
    authresult_message = fields.Char(string='Transaction error')

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _lyra_form_get_tx_from_data(self, data):
        shasign, status, reference = data.get('signature'), data.get('vads_trans_status'), data.get('vads_order_id')

        if not reference or not shasign or not status:
            error_msg = 'Lyra : received bad data %s' % (data)
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = 'Lyra: received data for reference %s' % (reference)
            if not tx:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'

            _logger.error(error_msg)
            raise ValidationError(error_msg)

        # verify shasign
        shasign_check = tx.acquirer_id._lyra_generate_digital_sign('out', data)
        if shasign_check.upper() != shasign.upper():
            error_msg = 'Lyra: invalid shasign, received %s, computed %s, for data %s' % (shasign, shasign_check, data)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _lyra_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        # check what is bought
        amount = float(int(data.get('vads_amount', 0)) / math.pow(10, int(self.currency_id.decimal_places)))

        if float_compare(amount, self.amount, int(self.currency_id.decimal_places)) != 0:
            invalid_parameters.append(('amount', amount, '%.2f' % self.amount))

        currency_code = constants.LYRA_CURRENCIES.get(self.currency_id.name, 0)
        if int(data.get('vads_currency')) != int(currency_code):
            invalid_parameters.append(('currency', data.get('vads_currency'), currency_code))

        return invalid_parameters

    def _lyra_form_validate(self, data):
        lyra_statuses = {'success': ['AUTHORISED', 'CAPTURED', 'CAPTURE_FAILED'],
                         'pending': ['AUTHORISED_TO_VALIDATE', 'WAITING_AUTHORISATION', 'WAITING_AUTHORISATION_TO_VALIDATE', 'INITIAL', 'UNDER_VERIFICATION'],
                         'cancel': ['NOT_CREATED', 'ABANDONED']
                        }

        html_3ds = '3-DS authentication : '
        if data.get('vads_threeds_status') == 'Y':
            html_3ds += 'YES'
            html_3ds += '<br />3-DS certificate : ' + data.get('vads_threeds_cavv')
        else:
            html_3ds += 'NO'

        status = data.get('vads_trans_status')
        if status in lyra_statuses['success']:
            self.write({
                'date_validate': fields.Datetime.now(),
                'acquirer_reference': data.get('vads_trans_id'),
                'state': 'done',
                'state_message': '%s' % (data),
                'html_3ds': html_3ds
            })
            return True
        elif status in lyra_statuses['pending']:
            self.write({
                'date_validate': fields.Datetime.now(),
                'acquirer_reference': data.get('vads_trans_id'),
                'state': 'pending',
                'state_message': '%s' % (data),
                'html_3ds': html_3ds
            })
            return True
        elif status in lyra_statuses['cancel']:
            self.write({
                'date_validate': fields.Datetime.now(),
                'state': 'cancel',
                'state_message': '%s' % (data)
            })
            return False
        else:
            auth_result = data.get('vads_auth_result')
            auth_message = ''
            if auth_result in constants.LYRA_AUTH_RESULT:
                auth_message = constants.LYRA_AUTH_RESULT[auth_result]

            error_msg = 'Lyra payment error, message %s, code %s' % (auth_message, auth_result)
            _logger.info(error_msg)

            self.write({
                'date_validate': fields.Datetime.now(),
                'acquirer_reference': data.get('vads_trans_id'),
                'state': 'error',
                'state_message': '%s' % (data),
                'authresult_message': auth_message,
                'html_3ds': html_3ds
            })
            return False
