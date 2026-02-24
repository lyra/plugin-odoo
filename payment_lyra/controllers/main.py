# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

import logging
import pprint

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
from ..helpers import tools

_logger = logging.getLogger(__name__)

class LyraController(http.Controller):
    _notify_url = '/payment/lyra/ipn'
    _return_url = '/payment/lyra/return'

    def _get_return_url(self, result, **pdt_data):
        return_url = pdt_data.pop('return_url', '')

        if not return_url:
            return_url = '/payment/process' if result else '/shop/cart'

        return return_url

    @http.route(
        _return_url, type='http', auth='public', methods=['POST', 'GET'], csrf=False,
        save_session=False
    )
    def lyra_return_from_checkout(self, **pdt_data):
        # Check payment result and create transaction.
        _logger.info('Lyra Collect: customer returns to shop with data %s', pprint.pformat(pdt_data))

        try:
            is_rest = False
            data = pdt_data

            # Check the type of integration.
            if tools.check_rest_response(pdt_data):
                data = tools.convert_rest_result(pdt_data)
                data['is_rest'] = '1'
                is_rest = True

            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data('lyra', data)

            # Verify hash.
            if is_rest:
                hmac256_key = tx_sudo.provider_id._lyra_get_rest_sha256_key()
                hash_checked = tools.check_hash(pdt_data, hmac256_key)
                if not hash_checked:
                    error_msg = 'Lyra Collect: invalid signature for data {}'.format(pdt_data)
                    _logger.info(error_msg)

                    raise ValidationError(error_msg)

            # Handle the notification data.
            tx_sudo._handle_notification_data('lyra', data)
        except ValidationError:
            _logger.exception("Lyra Collect: Unable to handle the return notification data; skipping to acknowledge.")

        # Redirect the user to the status page.
        return request.redirect('/payment/status')

    @http.route(_notify_url, type='http', auth='public', methods=['POST'], csrf=False,
        save_session=False
    )
    def lyra_ipn(self, **post):
        # Check payment result and create transaction.
        _logger.info('Lyra Collect: entering IPN _get_tx_from_notification with post data %s', pprint.pformat(post))

        try:
            is_rest = False
            data = post

            # Check the type of integration.
            if tools.check_rest_response(post):
                if not tools.order_cycle_closed(post):
                    return 'Payment failure.'

                data = tools.convert_rest_result(post)
                data['is_rest'] = '1'
                is_rest = True

            result = request.env['payment.transaction'].sudo()._get_tx_from_notification_data('lyra', data)

            if is_rest:
                rest_password = result.provider_id._lyra_get_rest_password()
                hash_checked = tools.check_hash(post, rest_password)
                if not hash_checked:
                    error_msg = 'Lyra Collect: invalid signature for data {}'.format(post)
                    _logger.info(error_msg)

                    raise ValidationError(error_msg)

            if (data.get('vads_trans_status') == 'ABANDONED') or (data.get('vads_trans_status') == 'CANCELED') and (data.get('vads_order_status') == 'UNPAID') and (data.get('vads_order_cycle') == 'CLOSED'):
                return 'Payment abandoned.'

            # Handle the notification data.
            result._handle_notification_data('lyra', data)
        except ValidationError: # Acknowledge the notification to avoid getting spammed.
            _logger.exception("Lyra Collect: Unable to handle the IPN notification data; skipping to acknowledge.")
            return 'Bad request received.'

        return 'Payment processed, order has been updated.' if result else 'An error occurred while processing payment.'