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
    @http.route("/payment/lyra/getTemporaryFormToken", type="http", auth='public', methods=['POST'], csrf=False)
    def lyra_create_temporary_form_token(self, **post):
        request_data = json.loads(request.httprequest.data.decode('utf-8'))

        # Creation of a super user in the class payment_provider to get the needed function.
        provider_id = request_data["paymentOptionId"]
        payment_provider = request.env['payment.provider'].sudo().browse(provider_id).exists()

        if payment_provider.lyra_payment_data_entry_mode == "redirect":
            return json.dumps({ "formToken": False })

        currency = payment_provider._lyra_get_currency(request_data['currencyId'])

        amount = float(request_data['amount'])
        amount = int(float_round(float_round(amount, int(currency[1])) * (10 ** int(currency[1])), 0))

        partner_id =  request_data['partnerId']
        partner = payment_provider.env['res.partner'].browse(partner_id)

        values = {
            "amount": amount,
            "currency": currency[0],
            "customer": {
                "email": partner.email,
                "reference":  partner_id,
            },
            "transactionOptions": {
                "cardOptions": {
                }
            }
        }

        validation_mode = payment_provider.lyra_validation_mode
        if validation_mode == "1":
            values["transactionOptions"]["cardOptions"]["manualValidation"] = "YES"
        elif validation_mode == "0":
            values["transactionOptions"]["cardOptions"]["manualValidation"] = "NO"

        capture_delay = payment_provider.lyra_capture_delay
        if capture_delay and capture_delay.isdigit():
            values["transactionOptions"]["cardOptions"]["captureDelay"] = capture_delay

        retry = payment_provider.lyra_smartform_payment_attempts
        if retry and retry.isdigit():
            values["transactionOptions"]["cardOptions"]["retry"] = retry

        cards = payment_provider._lyra_get_smartform_payment_means()
        if cards != []:
            values['paymentMethods'] = tuple(cards)

        values["contrib"] = tools._lyra_get_contrib()

        form_token = self.lyra_create_form_token(values, payment_provider)

        # Getting Smartform configuration.
        data_entry_mode = payment_provider.lyra_payment_data_entry_mode
        pop_in = payment_provider.lyra_smartform_pop_in
        compact = payment_provider.lyra_smartform_compact_mode

        return json.dumps({ "formToken": form_token, "publicKey": payment_provider._lyra_get_rest_public_key(), "dataEntryMode": data_entry_mode, "popin": pop_in, "compact": compact })

    @http.route("/payment/lyra/refreshFormToken", type="http", auth='public', methods=['POST'], csrf=False)
    def lyra_refresh_form_token(self, **post):
        processing_values = json.loads(request.httprequest.data.decode('utf-8'))
        provider_id = processing_values["provider_id"]
        reference = processing_values["reference"]

        # Creation of a super user of the payment_transaction class to acces the _get_specific_rendering_values function.
        payment_transaction = request.env['payment.transaction'].sudo().search([('reference', '=', reference)]).exists()
        payment_provider = request.env['payment.provider'].sudo().browse(provider_id).exists()

        processed_values = payment_transaction._get_specific_rendering_values(processing_values)
        currency = payment_provider._lyra_get_currency(processing_values["currency_id"])[0]

        form_token = self.lyra_generate_form_token(processed_values, payment_provider, currency)

        pop_in = payment_provider.lyra_smartform_pop_in
        compact = payment_provider.lyra_smartform_compact_mode

        return json.dumps({ "formToken": form_token, "popin": pop_in, "compact": compact })

    def lyra_generate_form_token(self, values, payment_provider, currency):
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

        retry = payment_provider.lyra_smartform_payment_attempts
        if retry and retry.isdigit():
            params["transactionOptions"]["cardOptions"]["retry"] = retry

        cards = payment_provider._lyra_get_smartform_payment_means()
        if cards != []:
            params['paymentMethods'] = tuple(cards)

        return self.lyra_create_form_token(params, payment_provider)

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

                _logger.info("Form token created successfully" + msg)

                return response.json().get("answer", {}).get("formToken")
        except Exception as exc:
            _logger.error(exc)

        return False