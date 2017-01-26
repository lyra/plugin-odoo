# -*- coding: utf-8 -*-

import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

try:
    import simplejson as json
except ImportError:
    import json


class PayzenController(http.Controller):
    _return_url = '/payment/payzen/return'

    @http.route(['/payment/payzen/return', ], type='http', auth='none')
    def payzen_return(self, **post):
        _logger.info('Payzen: entering form_feedback with post data %s', pprint.pformat(post))  # debug
        request.env['payment.transaction'].sudo().form_feedback(post, 'payzen')
        return werkzeug.utils.redirect(post.pop('return_url', '/'))
