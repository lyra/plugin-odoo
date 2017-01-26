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
        request.env['payment.transaction'].sudo().form_feedback(post, 'payzen')
        return_url = post.pop('return_url', '')
        if not return_url:
            data = '' + post.pop('ADD_RETURNDATA', '{}').replace("'", "\"")
            custom = json.loads(data)
            return_url = custom.pop('return_url', '/')
        return werkzeug.utils.redirect(return_url)
