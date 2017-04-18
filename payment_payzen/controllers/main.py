# -*- coding: utf-8 -*-

import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class PayzenController(http.Controller):
    _notify_url = '/payment/payzen/ipn/'
    _return_url = '/payment/payzen/return'

    def _get_return_url(self, result, **post):
        return_url = post.pop('return_url', '')
        if not return_url:
            return_url = '/shop/payment/validate' if result else '/shop/cart'
        return return_url

    @http.route(['/payment/payzen/return', ], type='http', auth='none')
    def payzen_return(self, **post):
        _logger.info('PayZen: entering form_feedback with post data %s', pprint.pformat(post))  # debug

        # check payment result and create payment transaction
        result = request.env['payment.transaction'].sudo().form_feedback(post, 'payzen')
        return_url = self._get_return_url(result, **post)
        return werkzeug.utils.redirect(return_url)

    @http.route('/payment/payzen/ipn/', type='http', auth='none', methods=['POST'], csrf=False)
    def payzen_ipn(self, **post):
        _logger.info('PayZen: entering IPN form_feedback with post data %s', pprint.pformat(post))  # debug

        # check payment result and create payment transaction
        result = request.env['payment.transaction'].sudo().form_feedback(post, 'payzen')
        return 'Valid payment processed' if result else 'Invalid payment processed'
