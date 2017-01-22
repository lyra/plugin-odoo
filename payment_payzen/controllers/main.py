# -*- coding: utf-8 -*-
try:
    import simplejson as json
except ImportError:
    import json

import logging
import pprint
import werkzeug

from openerp import http, SUPERUSER_ID
from openerp.http import request

_logger = logging.getLogger(__name__)


class PayzenController(http.Controller):
    _return_url = '/payment/payzen/return'

    @http.route(['/payment/payzen/return',], type='http', auth='none')
    def payzen_return(self, **post):
        request.registry['payment.transaction'].form_feedback(request.cr, SUPERUSER_ID, post, 'payzen', context=request.context)
        return_url = post.pop('return_url', '')
        if not return_url:
            data ='' + post.pop('ADD_RETURNDATA', '{}').replace("'", "\"")
            custom = json.loads(data)
            return_url = custom.pop('return_url', '/')
        return werkzeug.utils.redirect(return_url)
