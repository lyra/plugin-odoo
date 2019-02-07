# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network <https://www.lyra-network.com>
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class LyraController(http.Controller):
    _notify_url = '/payment/lyra/ipn'
    _return_url = '/payment/lyra/return'

    def _get_return_url(self, result, **post):
        return_url = post.pop('return_url', '')
        if not return_url:
            return_url = '/shop/payment/validate' if result else '/shop/cart'

        return return_url

    @http.route('/payment/lyra/return', type='http', auth='none', methods=['POST', 'GET'])
    def lyra_return(self, **post):
        _logger.info('Lyra: entering form_feedback with post data %s', pprint.pformat(post))

        # check payment result and create payment transaction
        result = request.env['payment.transaction'].sudo().form_feedback(post, 'lyra')
        return_url = self._get_return_url(result, **post)
        return werkzeug.utils.redirect(return_url)

    @http.route('/payment/lyra/ipn', type='http', auth='none', methods=['POST'], csrf=False)
    def lyra_ipn(self, **post):
        _logger.info('Lyra: entering IPN form_feedback with post data %s', pprint.pformat(post))

        # check payment result and create payment transaction
        result = request.env['payment.transaction'].sudo().form_feedback(post, 'lyra')
        return 'Valid payment processed' if result else 'Invalid payment processed'
