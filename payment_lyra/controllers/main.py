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

import requests

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class LyraController(http.Controller):
    _notify_url = "/payment/lyra/ipn"
    _return_url = "/payment/lyra/return"

    @http.route(
        _return_url, type="http", auth="public", methods=["POST", "GET"], csrf=False
    )
    def lyra_return_from_redirect(self, **data):
        _logger.info("received lyra return data:\n%s", pprint.pformat(data))
        # IPN call has been probably called first, anyway we assume _handle_feedback_data
        # to be indempotent
        request.env["payment.transaction"].sudo()._handle_feedback_data("lyra", data)
        return request.redirect("/payment/status")

    @http.route(_notify_url, type="http", auth="public", methods=["POST"], csrf=False)
    def lyra_ipn_notify(self, **post):
        _logger.info("received lyra notification data:\n%s", pprint.pformat(post))
        tx = (
            request.env["payment.transaction"]
            .sudo()
            ._handle_feedback_data("lyra", post)
        )
        # An ir cron managed the order state if end user do not come back
        # to the user interface calling tx._cron_finalize_post_processing
        return _(
            'Odoo "%s" payment transaction has been updated to the "%s" state.'
        ) % (
            tx.reference,
            tx.state,
        )
