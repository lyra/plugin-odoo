# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

import logging
import base64
import requests
import json

from odoo.tools import float_round
from odoo import http
from odoo.http import request

from ..helpers import tools, constants
_logger = logging.getLogger(__name__)

class LyraRestController(http.Controller):
    @http.route("/payment/lyra/createFormToken", type="http", auth='public', methods=['POST'], csrf=False)
    def lyra_refresh_form_token(self, **post):
        processing_values = json.loads(request.httprequest.data.decode('utf-8'))
        provider_id = processing_values["provider_id"]
        payment_provider = request.env['payment.provider'].sudo().browse(provider_id).exists()

        # On payment method selection, we have only order ID.
        if "order_id" in processing_values:
            processed_values = payment_provider.lyra_generate_values_from_order(processing_values)
        else:
            # On payment submit, we have transaction data.
            payment_transaction = request.env['payment.transaction'].sudo().search([('reference', '=', processing_values["reference"])]).exists()

            sale_order = payment_transaction.sale_order_ids[0]
            sale_order._check_cart_is_ready_to_be_paid()

            # Check amount coherence.
            compare_amounts = sale_order.currency_id.compare_amounts
            if (compare_amounts(float(processing_values['amount']), sale_order.amount_total)):
                return json.dumps({ "formToken": "NO_UPDATE" })

            processed_values = payment_transaction._get_specific_rendering_values(processing_values)
            processed_values["vads_order_id"] = processing_values["reference"].rpartition('-')[0]

        currency = payment_provider._lyra_get_currency(processing_values["currency_id"])[0]

        params = self.generate_form_token_data(processed_values, payment_provider, currency)
        form_token =  self.lyra_create_form_token(params, payment_provider)
        return json.dumps({ "formToken": form_token })

    def generate_form_token_data(self, values, payment_provider, currency):
        params = {
            "amount": values["vads_amount"],
            "currency": currency,
            "orderId": values["vads_order_id"],
            "customer": {
                "email": values["vads_cust_email"],
                "reference": values["vads_cust_id"],
                "billingDetails": {
                    "firstName": values["vads_cust_first_name"],
                    "lastName": values["vads_cust_last_name"],
                    "address": values["vads_cust_address"],
                    "zipCode": values["vads_cust_zip"],
                    "state": values["vads_cust_state"],
                    "city": values["vads_cust_city"],
                    "phoneNumber": values["vads_cust_phone"],
                    "country": values["vads_cust_country"],
                    "language": values["vads_language"],
                }
            },
            "shipingDetails": {
                "firstName": values["vads_ship_to_first_name"],
                "lastName": values["vads_ship_to_last_name"],
                "address": values["vads_ship_to_street"],
                "zipCode": values["vads_ship_to_zip"],
                "city": values["vads_ship_to_city"],
                "state": values["vads_ship_to_state"],
                "phoneNumber": values["vads_ship_to_phone_num"],
                "country": values["vads_ship_to_country"],
            },
            "transactionOptions": {
                "cardOptions": {
                    "paymentSource": "EC"
                }
            },
            "contrib": values["vads_contrib"],
        }

        validation_mode = payment_provider.lyra_validation_mode
        if validation_mode == "1":
            params["transactionOptions"]["cardOptions"]["manualValidation"] = "YES"
        elif validation_mode == "0":
            params["transactionOptions"]["cardOptions"]["manualValidation"] = "NO"

        capture_delay = payment_provider.lyra_capture_delay
        if capture_delay and capture_delay.isdigit():
            params["transactionOptions"]["cardOptions"]["captureDelay"] = capture_delay

        retry = payment_provider.lyra_embedded_payment_attempts
        if retry and retry.isdigit():
            params["transactionOptions"]["cardOptions"]["retry"] = retry

        cards = payment_provider._lyra_get_embedded_payment_means()
        if cards != []:
            params['paymentMethods'] = tuple(cards)

        return params

    def lyra_create_form_token(self, values, payment_provider):
        try:
            identification = payment_provider.lyra_site_id + ":" + payment_provider._lyra_get_rest_password()
            headers = {
                "Authorization": "Basic " + base64.b64encode((identification.encode('utf-8'))).decode('utf-8'),
                "Content-Type": "application/json"
            }

            request_url = constants.LYRA_PARAMS.get('REST_URL') + 'V4/Charge/CreatePayment'

            response = requests.post(url = request_url, json = values, headers = headers)
            if response.json().get("status") != "SUCCESS":
                _logger.error("Error while creating form token: " + response.json().get("answer", {}).get("errorMessage") + "(" + response.json().get("answer", {}).get("errorCode") + ").")
                if "detailedErrorMessage" in response.json().get("answer", {}) and response.json().get("answer", {}).get("detailedErrorMessage") is not None:
                    _logger.error("Detailed message: " + response.json().get("answer", {}).get("detailedErrorMessage") + "(" + response.json().get("answer", {}).get("detailedErrorCode") + ").")
            else:
                msg = ""
                if "orderId" in values:
                    msg = " for order #" + values['orderId']

                _logger.info("Form token created successfully {} with data: {}".format(msg, values))

                return response.json().get("answer", {}).get("formToken")
        except Exception as exc:
            _logger.error(exc)

        return False