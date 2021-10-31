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

from pkg_resources import parse_version
import werkzeug

from odoo import http, release
from odoo.http import request


_logger = logging.getLogger(__name__)

class LyraController(http.Controller):
    _notify_url = '/payment/lyra/ipn'
    _return_url = '/payment/lyra/return'

    def _get_return_url(self, result, **post):
        return_url = post.pop('return_url', '')

        if not return_url:
            if result:
                old_version = True if parse_version(release.version) < parse_version('12') else False
                return_url = '/shop/payment/validate' if old_version else '/payment/process'
            else:
                return_url = '/shop/cart'

        return return_url

    @http.route('/payment/lyra/return', type='http', auth='public', methods=['POST', 'GET'], csrf=False)
    def lyra_return(self, **post):
        # Check payment result and create transaction.
        if parse_version(release.version) >= parse_version('15'):
            _logger.info('Lyra Collect: entering _handle_feedback with post data %s', pprint.pformat(post))
            request.env['payment.transaction'].sudo()._handle_feedback_data('lyra', post)
            return request.redirect('/payment/status')
        else:
            _logger.info('Lyra Collect: entering form_feedback with post data %s', pprint.pformat(post))
            result = request.env['payment.transaction'].sudo().form_feedback(post, 'lyra')
            return_url = self._get_return_url(result, **post)
            return werkzeug.utils.redirect(return_url)

    @http.route('/payment/lyra/ipn', type='http', auth='public', methods=['POST'], csrf=False)
    def lyra_ipn(self, **post):
        # Check payment result and create transaction.
        if parse_version(release.version) >= parse_version('15'):
            _logger.info('Lyra Collect: entering IPN _handle_feedback with post data %s', pprint.pformat(post))
            result = request.env['payment.transaction'].sudo()._handle_feedback_data('lyra', post)
        else:
            _logger.info('Lyra Collect: entering IPN form_feedback with post data %s', pprint.pformat(post))
            result = request.env['payment.transaction'].sudo().form_feedback(post, 'lyra')

        return 'Accepted payment, order has been updated.' if result else 'Payment failure, order has been cancelled.'
