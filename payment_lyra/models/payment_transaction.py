# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

import logging
import math
from datetime import datetime

from odoo import models, api, release, fields, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment import utils as payment_utils
from odoo.tools.float_utils import float_compare

from ..helpers import tools

_logger = logging.getLogger(__name__)

class TransactionLyra(models.Model):
    _inherit = 'payment.transaction'

    lyra_trans_status = fields.Char(_('Transaction status'))
    lyra_card_brand = fields.Char(_('Means of payment'))
    lyra_card_number = fields.Char(_('Card number'))
    lyra_expiration_date = fields.Char(_('Expiration date'))
    lyra_auth_result = fields.Char(_('Authorization result'))
    lyra_raw_data = fields.Text(string=_('Transaction log'), readonly=True)

    lyra_html_3ds = fields.Char('3D Secure HTML')

    lyra_statuses = {
        'success': ['AUTHORISED', 'CAPTURED', 'ACCEPTED'],
        'pending': ['AUTHORISED_TO_VALIDATE', 'WAITING_AUTHORISATION', 'WAITING_AUTHORISATION_TO_VALIDATE', 'INITIAL', 'UNDER_VERIFICATION', 'WAITING_FOR_PAYMENT', 'PRE_AUTHORISED'],
        'cancel': ['ABANDONED']
    }

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    # Odoo 15.
    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Lyra-specific rendering values."""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider not in ['lyra', 'lyramulti']:
            return res

        values = self.acquirer_id.lyra_form_generate_values(processing_values)

        for key in values.keys():
            if key.startswith('vads_') and values[key] != '':
               values[key] = values[key].decode('utf-8')

        partner_first_name, partner_last_name = payment_utils.split_partner_name(self.partner_name)

        partner_shipping_id = self.sale_order_ids[0].partner_shipping_id
        partner_shipping_first_name, partner_shipping_last_name = payment_utils.split_partner_name(partner_shipping_id.name) if partner_shipping_id else ('', '')

        values.update({
            'vads_cust_id': str(self.partner_id.id) or '',
            'vads_cust_first_name': partner_first_name or '',
            'vads_cust_last_name': partner_last_name or '',
            'vads_cust_address': self.partner_address or '',
            'vads_cust_zip': self.partner_zip or '',
            'vads_cust_city': self.partner_city or '',
            'vads_cust_state': self.partner_state_id.name or '',
            'vads_cust_country': self.partner_country_id.code or '',
            'vads_cust_email': self.partner_email or '',
            'vads_cust_phone': self.partner_phone or '',

            # Shipping info.
            'vads_ship_to_first_name': partner_shipping_first_name if partner_shipping_id else '',
            'vads_ship_to_last_name': partner_shipping_last_name if partner_shipping_id else '',
            'vads_ship_to_street': partner_shipping_id.street if partner_shipping_id else '',
            'vads_ship_to_zip': partner_shipping_id.zip if partner_shipping_id else '',
            'vads_ship_to_city': partner_shipping_id.city if partner_shipping_id else '',
            'vads_ship_to_state': partner_shipping_id.state_id.name if partner_shipping_id else '',
            'vads_ship_to_country': partner_shipping_id.country_id.code if partner_shipping_id else '',
            'vads_ship_to_phone_num': partner_shipping_id.phone if partner_shipping_id else ''
        })

        values['lyra_signature'] = self.acquirer_id._lyra_generate_sign(self, values)
        values['api_url'] = self.acquirer_id.lyra_get_form_action_url()
        return values

    @api.model
    def _lyra_form_get_tx_from_data(self, data):
        shasign, status, reference = data.get('signature'), data.get('vads_trans_status'), data.get('vads_order_id')

        if not reference or not shasign or not status:
            error_msg = 'Lyra Collect : received bad data {}'.format(data)
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = 'Lyra Collect: received data for reference {}'.format(reference)
            if not tx:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'

            _logger.error(error_msg)
            raise ValidationError(error_msg)

        # Verify shasign.
        shasign_check = tx.acquirer_id._lyra_generate_sign('out', data)
        if shasign_check.upper() != shasign.upper():
            error_msg = 'Lyra Collect: invalid shasign, received {}, computed {}, for data {}'.format(shasign, shasign_check, data)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'lyra' and self.provider != 'lyramulti':
            return tx

        return self._lyra_form_get_tx_from_data(data)

    def _process_feedback_data(self, data):
        super()._process_feedback_data(data)
        if self.provider != 'lyra' and self.provider != 'lyramulti':
            return

        self.acquirer_reference = data.get('vads_order_id')

        html_3ds = _('3DS authentication: ')
        if data.get('vads_threeds_status') == 'Y':
            html_3ds += _('YES')
            html_3ds += '<br />' + _('3DS certificate: ') + data.get('vads_threeds_cavv')
        else:
            html_3ds += _('NO')

        expiry = ''
        if data.get('vads_expiry_month') and data.get('vads_expiry_year'):
            expiry = data.get('vads_expiry_month').zfill(2) + '/' + data.get('vads_expiry_year')

        values = {
            'acquirer_reference': data.get('vads_trans_uuid'),
            'lyra_raw_data': '{}'.format(data),
            'lyra_html_3ds': html_3ds,
            'lyra_trans_status': data.get('vads_trans_status'),
            'lyra_card_brand': data.get('vads_card_brand'),
            'lyra_card_number': data.get('vads_card_number'),
            'lyra_expiration_date': expiry,
        }

        status = data.get('vads_trans_status')
        if status in self.lyra_statuses['success']:
            self.write(values)
            self._set_done()

            return True
        elif status in self.lyra_statuses['pending']:
            self.write(values)
            self._set_pending()

            return True
        elif status in self.lyra_statuses['cancel']:
            self.write({
                'state_message': 'Payment for transaction #%s is cancelled (%s).' % (self.reference, data.get('vads_result')),
            })

            self._set_canceled()

            return False
        else:
            auth_result = data.get('vads_auth_result')
            auth_message = _('See the transaction details for more information ({}).').format(auth_result)

            error_msg = 'Lyra Collect payment error, transaction status: {}, authorization result: {}.'.format(status, auth_result)
            _logger.info(error_msg)

            values.update({
                'state_message': 'Payment for transaction #%s is refused (%s).' % (self.reference, data.get('vads_result')),
                'lyra_auth_result': auth_message,
            })

            self.write(values)
            self._set_error('Payment for transaction #%s is refused (%s).' % (self.reference, data.get('vads_result')))

            return False
