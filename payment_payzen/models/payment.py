# coding: utf-8
#
# This file is part of Odoo PayZen Payment.
# Copyright (C) Lyra Network. All rights reserved.
# See COPYING.txt for license details.

from hashlib import sha1
import logging
import urlparse
import math

from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_payzen.controllers.main import PayzenController
from odoo.addons.payment_payzen.helpers import constants
from odoo import models, api, release, fields, _
from odoo.tools import float_round, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_compare, float_repr
from datetime import datetime

_logger = logging.getLogger(__name__)

class AcquirerPayzen(models.Model):
    _inherit = 'payment.acquirer'

    payzen_form_url = 'https://secure.payzen.eu/vads-payment/'

    provider = fields.Selection(selection_add=[('payzen', 'PayZen')])
    payzen_websitekey = fields.Char(string='Shop ID', required_if_provider='payzen')
    payzen_secretkey = fields.Char(string='Certificate', required_if_provider='payzen')

    def _payzen_generate_digital_sign(self, acquirer, values):
        sign = ''
        for key in sorted(values.iterkeys()):
            if key.startswith('vads_'):
                sign += values[key] + '+'

        sign += self.payzen_secretkey
        shasign = sha1(sign.encode('utf-8')).hexdigest()

        return shasign

    @api.multi
    def payzen_form_generate_values(self, values):
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
            'vads_site_id': self.payzen_websitekey,
            'vads_amount': unicode(amount),
            'vads_currency': constants.PAYZEN_CURRENCIES.get(values['currency'].name),
            'vads_trans_date': unicode(datetime.utcnow().strftime("%Y%m%d%H%M%S")),
            'vads_trans_id': unicode(trans_id),
            'vads_ctx_mode': mode,
            'vads_page_action': u'PAYMENT',
            'vads_action_mode': u'INTERACTIVE',
            'vads_payment_config': u'SINGLE',
            'vads_version': u'V2',
            'vads_url_return': urlparse.urljoin(base_url, PayzenController._return_url),
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
            'vads_redirect_success_timeout': "5",
        })

        payzen_tx_values = dict() # values encoded in utf-8

        for key in tx_values.iterkeys():
            payzen_tx_values[key] = tx_values[key].encode('utf-8')

        payzen_tx_values['payzen_signature'] = self._payzen_generate_digital_sign(self, tx_values)
        return payzen_tx_values

    @api.multi
    def payzen_get_form_action_url(self):
        return self.payzen_form_url


class TxPayzen(models.Model):
    _inherit = 'payment.transaction'

    state_message = fields.Char(string='Transaction log')
    authresult_message = fields.Char(string='Transaction error')

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _payzen_form_get_tx_from_data(self, data):
        shasign, status, reference = data.get('signature'), data.get('vads_trans_status'), data.get('vads_order_id')

        if not reference or not shasign or not status:
            error_msg = 'PayZen : received bad data %s' % (data)
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = 'PayZen: received data for reference %s' % (reference)
            if not tx:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'

            _logger.error(error_msg)
            raise ValidationError(error_msg)

        # verify shasign
        shasign_check = tx.acquirer_id._payzen_generate_digital_sign('out', data)
        if shasign_check.upper() != shasign.upper():
            error_msg = 'PayZen: invalid shasign, received %s, computed %s, for data %s' % (shasign, shasign_check, data)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _payzen_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        # check what is bought
        amount = float(int(data.get('vads_amount', 0)) / math.pow(10, int(self.currency_id.decimal_places)))

        if float_compare(amount, self.amount, int(self.currency_id.decimal_places)) != 0:
            invalid_parameters.append(('amount', amount, '%.2f' % self.amount))

        currency_code = constants.PAYZEN_CURRENCIES.get(self.currency_id.name, 0)
        if int(data.get('vads_currency')) != int(currency_code):
            invalid_parameters.append(('currency', data.get('vads_currency'), currency_code))

        return invalid_parameters

    def _payzen_form_validate(self, data):
        payzen_statuses = {'success': ['AUTHORISED', 'CAPTURED', 'CAPTURE_FAILED'],
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
        if status in payzen_statuses['success']:
            self.write({
                'date_validate': fields.Datetime.now(),
                'acquirer_reference': data.get('vads_trans_id'),
                'state': 'done',
                'state_message': '%s' % (data),
                'html_3ds': html_3ds
            })
            return True
        elif status in payzen_statuses['pending']:
            self.write({
                'date_validate': fields.Datetime.now(),
                'acquirer_reference': data.get('vads_trans_id'),
                'state': 'pending',
                'state_message': '%s' % (data),
                'html_3ds': html_3ds
            })
            return True
        elif status in payzen_statuses['cancel']:
            self.write({
                'date_validate': fields.Datetime.now(),
                'state': 'cancel',
                'state_message': '%s' % (data)
            })
            return False
        else:
            auth_result = data.get('vads_auth_result')
            auth_message = ''
            if auth_result in constants.PAYZEN_AUTH_RESULT:
                auth_message = constants.PAYZEN_AUTH_RESULT[auth_result]

            error_msg = 'PayZen payment error, message %s, code %s' % (auth_message, auth_result)
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
