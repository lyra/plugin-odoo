# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra-network.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

from hashlib import sha1, sha256
import base64 
import hmac
import logging

import math
from odoo.addons.payment_lyra.models.language import LyraLanguage
from odoo.addons.payment_lyra.models.card import LyraCard

from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_lyra.controllers.main import LyraController
from odoo.addons.payment_lyra.helpers import constants
from odoo import models, api, release, fields, _
from odoo.tools import float_round, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_compare, float_repr
from datetime import datetime
from pkg_resources import parse_version

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

_logger = logging.getLogger(__name__)

class AcquirerLyra(models.Model):
    _inherit = 'payment.acquirer'

    def _get_notify_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return urlparse.urljoin(base_url, LyraController._notify_url)
    
    sign_algo_help = _('Algorithm used to compute the payment form signature. Selected algorithm must be the same as one configured in the {} Back Office.').format(constants.LYRA_PARAMS.get('BACKOFFICE_NAME'))
    
    if (constants.pluginFeatures.get('shatwo') == False):
        sign_algo_help += _('The HMAC-SHA-256 algorithm should not be activated if it is not yet available in the {} Back Office, the feature will be available soon.').format(constants.LYRA_PARAMS.get('BACKOFFICE_NAME'))

    provider = fields.Selection(selection_add=[('lyra', 'Lyra')])
    lyra_site_id = fields.Char(string=_('Shop ID'), help=_('The identifier provided by {}.').format(constants.LYRA_PARAMS.get('GATEWAY_NAME')), default=constants.LYRA_PARAMS.get('SITE_ID'), required_if_provider='lyra')
    lyra_key_test = fields.Char(string=_('Key in test mode'), help=_('Key provided by {} for test mode (available in {} Back Office).').format(constants.LYRA_PARAMS.get('GATEWAY_NAME'), constants.LYRA_PARAMS.get('BACKOFFICE_NAME')), default=constants.LYRA_PARAMS.get('KEY_TEST'), readonly=constants.pluginFeatures.get('qualif'), required_if_provider='lyra')
    lyra_key_prod = fields.Char(string=_('Key in production mode'), help=_('Key provided by {} (available in {} Back Office after enabling production mode).').format(constants.LYRA_PARAMS.get('GATEWAY_NAME'), constants.LYRA_PARAMS.get('BACKOFFICE_NAME')), default=constants.LYRA_PARAMS.get('KEY_PROD'), required_if_provider='lyra')
    lyra_sign_algo = fields.Selection(string=_('Signature algorithm'), help=sign_algo_help, selection=[('SHA-1', 'SHA-1'), ('SHA-256', 'HMAC-SHA-256')], default=constants.LYRA_PARAMS.get('SIGN_ALGO'), required_if_provider='lyra')
    lyra_notify_url = fields.Char(string=_('Instant Payment Notification URL'), help=_('URL to copy into your {} Back Office > Settings > Notification rules.').format(constants.LYRA_PARAMS.get('BACKOFFICE_NAME')), default=_get_notify_url, readonly=True)
    lyra_gateway_url = fields.Char(string=_('Payment page URL'), help=_('Link to the payment page.'), default=constants.LYRA_PARAMS.get('GATEWAY_URL'), required_if_provider='lyra')
    lyra_language = fields.Selection(string=_('Default language'), help=_('Default language on the payment page.'), default=constants.LYRA_PARAMS.get('LANGUAGE'), selection='_get_languages')
    lyra_available_languages = fields.Many2many('lyra.language', string=_('Available languages'), column1='code', column2='label', help=_('Languages available on the payment page. If you do not select any, all the supported languages will be available.'))
    lyra_capture_delay = fields.Char(string=_('Capture delay'), help=_('The number of days before the bank capture (adjustable in your {} Back Office).').format(constants.LYRA_PARAMS.get('BACKOFFICE_NAME')))
    lyra_validation_mode = fields.Selection(string=_('Validation mode'), help=_('If manual is selected, you will have to confirm payments manually in your {} Back Office.').format(constants.LYRA_PARAMS.get('BACKOFFICE_NAME')), selection=[(' ', _('{} Back Office Configuration').format(constants.LYRA_PARAMS.get('BACKOFFICE_NAME'))), ('0', _('Automatic')), ('1', _('Manual'))])
    lyra_payment_cards = fields.Many2many('lyra.card', string=_('Card types'), column1='code', column2='label', help=_('The card type(s) that can be used for the payment. Select none to use gateway configuration.'))
    lyra_threeds_min_amount = fields.Char(string=_('Disable 3DS'), help=_('Amount below which 3DS will be disabled. Needs subscription to selective 3DS option. For more information, refer to the module documentation.'))
    lyra_redirect_enabled = fields.Selection(string=_('Redirection enabled'), help=_('If enabled, the buyer is automatically redirected to your site at the end of the payment.'), selection=[('0', _('Disabled')), ('1', _('Enabled'))])
    lyra_redirect_success_timeout = fields.Char(string=_('Redirection timeout on success'), help=_('Time in seconds (0-300) before the buyer is automatically redirected to your website after a successful payment.'))
    lyra_redirect_success_message = fields.Char(string=_('Redirection message on success'), help=_('Message displayed on the payment page prior to redirection after a successful payment.'), default=_('Redirection to shop in a few seconds...'))
    lyra_redirect_error_timeout = fields.Char(string=_('Redirection timeout on failure'), help=_('Time in seconds (0-300) before the buyer is automatically redirected to your website after a declined payment.'))
    lyra_redirect_error_message = fields.Char(string=_('Redirection message on failure'), help=_('Message displayed on the payment page prior to redirection after a declined payment.'), default=_('Redirection to shop in a few seconds...'))
    lyra_return_mode = fields.Selection(string=_('Return mode'), help=_('Method that will be used for transmitting the payment result from the payment page to your shop.'), selection=[('GET', 'GET'), ('POST', 'POST')], required_if_provider='lyra')

    # Check if it's Odoo 10
    lyra_odoo10 = True if (parse_version(release.version) < parse_version("11")) else False

    def _get_languages(self):
        languages = constants.LYRA_LANGUAGES
        return list(languages.items())

    def _lyra_generate_digital_sign(self, acquirer, values):
        certificate = self.lyra_key_prod if (self.environment == 'prod') else self.lyra_key_test

        sign = ''
        for key in sorted(values.keys()):
            if key.startswith('vads_'):
                sign += values[key] + '+'

        sign += certificate
        
        if self.lyra_sign_algo =='SHA-1':
            shasign = sha1(sign.encode('utf-8')).hexdigest()
        else:
            shasign = base64.b64encode(hmac.new(certificate.encode('utf-8'), sign.encode('utf-8'), sha256).digest())

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

        threeds_mpi = u''
        if self.lyra_threeds_min_amount and self.lyra_threeds_min_amount > values['amount']:
            threeds_mpi = u'2'

        # amount in cents
        amount = int(values['amount'] * math.pow(10, int(values['currency'].decimal_places)))
        
        # list of available languages
        available_languages = ''
        for value in self.lyra_available_languages:
            available_languages += value.code + ';'
        
        #list of available payment cards
        payment_cards = ''
        for value in self.lyra_payment_cards:
            payment_cards += value.code + ';'

        tx_values = dict() # values to sign in unicode
        tx_values.update({
            'vads_site_id': self.lyra_site_id,
            'vads_sign_algo': self.lyra_sign_algo,
            'vads_amount': str(amount),
            'vads_currency': constants.LYRA_CURRENCIES.get(values['currency'].name),
            'vads_trans_date': str(datetime.utcnow().strftime("%Y%m%d%H%M%S")),
            'vads_trans_id': str(trans_id),
            'vads_ctx_mode': mode,
            'vads_page_action': u'PAYMENT',
            'vads_action_mode': u'INTERACTIVE',
            'vads_payment_config': u'SINGLE',
            'vads_version': constants.LYRA_PARAMS.get('GATEWAY_VERSION'),
            'vads_url_return': urlparse.urljoin(base_url, LyraController._return_url),
            'vads_order_id': str(values.get('reference')),
            'vads_contrib': constants.LYRA_PARAMS.get('CMS_IDENTIFIER') + u'_' + constants.LYRA_PARAMS.get('PLUGIN_VERSION') + u'_' + release.version,

            'vads_language': self.lyra_language or '',
            'vads_available_languages': available_languages,
            'vads_capture_delay': self.lyra_capture_delay or '',
            'vads_validation_mode': self.lyra_validation_mode or '',
            'vads_payment_cards': payment_cards,
            'vads_redirect_enabled': self.lyra_redirect_enabled or '0',
            'vads_redirect_success_timeout': self.lyra_redirect_success_timeout or '',
            'vads_redirect_success_message': self.lyra_redirect_success_message or '',
            'vads_redirect_error_timeout': self.lyra_redirect_error_timeout or '',
            'vads_redirect_error_message': self.lyra_redirect_error_message or '',
            'vads_return_mode': str(self.lyra_return_mode),
            'vads_threeds_mpi': threeds_mpi,

            # customer info
            'vads_cust_id': str(values.get('billing_partner_id')) or '',
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

        for key in tx_values.keys():
            if tx_values[key] == ' ':
                tx_values[key] = ''

            lyra_tx_values[key] = tx_values[key].encode('utf-8')

        lyra_tx_values['lyra_signature'] = self._lyra_generate_digital_sign(self, tx_values)
        return lyra_tx_values

    @api.multi
    def lyra_get_form_action_url(self):
        return self.lyra_gateway_url


class TxLyra(models.Model):
    _inherit = 'payment.transaction'

    state_message = fields.Char(_('Transaction log'))
    authresult_message = fields.Char(_('Transaction error'))

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _lyra_form_get_tx_from_data(self, data):
        shasign, status, reference = data.get('signature'), data.get('vads_trans_status'), data.get('vads_order_id')

        if not reference or not shasign or not status:
            error_msg = 'Lyra : received bad data {}'.format(data)
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = 'Lyra: received data for reference {}'.format(reference)
            if not tx:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'

            _logger.error(error_msg)
            raise ValidationError(error_msg)

        # verify shasign
        shasign_check = tx.acquirer_id._lyra_generate_digital_sign('out', data)
        if shasign_check.upper() != shasign.upper():
            error_msg = 'Lyra: invalid shasign, received {}, computed {}, for data {}'.format(shasign, shasign_check, data)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _lyra_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        # check what is bought
        amount = float(int(data.get('vads_amount', 0)) / math.pow(10, int(self.currency_id.decimal_places)))

        if float_compare(amount, self.amount, int(self.currency_id.decimal_places)) != 0:
            invalid_parameters.append(('amount', amount, '{:.2f}'.format(self.amount)))

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
                'state_message': '{}'.format(data),
                'html_3ds': html_3ds
            })
            return True
        elif status in lyra_statuses['pending']:
            self.write({
                'date_validate': fields.Datetime.now(),
                'acquirer_reference': data.get('vads_trans_id'),
                'state': 'pending',
                'state_message': '{}'.format(data),
                'html_3ds': html_3ds
            })
            return True
        elif status in lyra_statuses['cancel']:
            self.write({
                'date_validate': fields.Datetime.now(),
                'state': 'cancel',
                'state_message': '{}'.format(data)
            })
            return False
        else:
            auth_result = data.get('vads_auth_result')
            auth_message = ''
            if auth_result in constants.LYRA_AUTH_RESULT:
                auth_message = constants.LYRA_AUTH_RESULT[auth_result]

            error_msg = 'Lyra payment error, message {}, code {}'.format(auth_message, auth_result)
            _logger.info(error_msg)

            self.write({
                'date_validate': fields.Datetime.now(),
                'acquirer_reference': data.get('vads_trans_id'),
                'state': 'error',
                'state_message': '{}'.format(data),
                'authresult_message': auth_message,
                'html_3ds': html_3ds
            })
            return False
