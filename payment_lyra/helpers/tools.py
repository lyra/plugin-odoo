# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

from .constants import LYRA_CURRENCIES, LYRA_PARAMS
from datetime import datetime
from odoo import release

import hashlib
import hmac
import json

null = None
true = True
false = False

def find_currency(iso):
    for currency in LYRA_CURRENCIES:
        if currency[0] == iso:
            return currency[1]

    return None

def _lyra_get_contrib():
    return LYRA_PARAMS.get('CMS_IDENTIFIER') + u'_' + LYRA_PARAMS.get('PLUGIN_VERSION') + u'/' + release.version

def generate_trans_id():
    # trans_id is the number of 1/10 seconds from midnight.
    now = datetime.now()
    midnight = now.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
    delta = int((now - midnight).total_seconds() * 10)

    return str(delta).rjust(6, '0')

def lang_translate(callback, v):
    return v

def check_hash(post, key):
    return hmac.new(key.encode("utf-8"), eval(json.dumps(post, ensure_ascii=False)).get("kr-answer").encode("utf-8"), hashlib.sha256).hexdigest() == eval(json.dumps(post, ensure_ascii=False)).get("kr-hash")

def check_rest_response(post):
    return 'kr-hash' in post and 'kr-hash-algorithm' in post and 'kr-answer' in post

def order_cycle_closed(post):
    answer = eval(json.dumps(post, ensure_ascii=False)).get("kr-answer")
    order_cycle = eval(answer).get('orderCycle')

    return order_cycle and (order_cycle == 'CLOSED')

def convert_rest_result(post):
    if (not post):
        return {}

    answer = eval(json.dumps(post, ensure_ascii=False)).get("kr-answer")

    response = {}
    response['vads_url_check_src'] = eval(answer).get('kr-src')
    response['vads_order_cycle'] = eval(answer).get('orderCycle')
    response['vads_order_status'] = eval(answer).get('orderStatus')

    transactions = eval(answer).get("transactions")
    if (not transactions):
        transactions = answer
    else:
        transactions = transactions[0]

    response["vads_result"] = transactions.get("errorCode", '00')
    response["vads_extra_result"] = transactions.get("detailedErrorCode")
    response["vads_trans_status"] = transactions.get("detailedStatus")
    response["vads_trans_uuid"] = transactions.get("uuid")
    response["vads_operation_type"] = transactions.get("operationType")
    response["vads_effective_creation_date"] = transactions.get("creationDate")
    response["vads_payment_config"] = "SINGLE"

    customer = eval(answer).get("customer", False)
    if customer:
        billing_details = customer.get("billingDetails", False)
        if billing_details:
            response['vads_language'] = billing_details.get("language").lower()

    response["vads_amount"] = transactions.get("amount")
    response["vads_currency"] = find_currency(transactions.get("currency"))

    payment_method_token = transactions.get("paymentMethodToken", False)
    if payment_method_token:
        response["vads_identifier"] = payment_method_token
        response["vads_identifier_status"] = 'CREATED'

    order_details = eval(answer).get("orderDetails", False)
    if order_details:
       response["vads_order_id"] = order_details["orderId"]

    metadata = transactions.get("metadata", False)
    if metadata:
        for key, value in metadata:
            response["vads_ext_info_" + key] = value

    transaction_details = transactions.get("transactionDetails", False)
    if transaction_details:
        response['vads_sequence_number'] = transaction_details.get("sequenceNumber")

        effective_amount = transaction_details.get("effectiveAmount", False)
        effective_currency = find_currency(transaction_details["effectiveCurrency"]) if "effectiveCurrency" in transaction_details and transaction_details["effectiveCurrency"] else False

        if (effective_amount and effective_currency):
            if (effective_currency != response["vads_currency"]):
                response["vads_change_rate"] = round(effective_amount/response["vads_amount"], 4)

                response["vads_effective_amount"] = response["vads_amount"]
                response["vads_effective_currency"] = response["vads_currency"]
                response["vads_amount"] = effective_amount
                response["vads_currency"] = effective_currency

            else:
                response['effective_amount'] = effective_amount
                response['effective_currency'] = effective_currency

        response["vads_warranty_result"] = transaction_details["liabilityShift"]

        card_details = transaction_details.get("cardDetails", False)
        if card_details:
            response['vads_trans_id'] = card_details.get("legacyTransId")
            response['vads_presentation_date'] = card_details.get("expectedCaptureDate")

            response['vads_card_brand'] = card_details.get("effectiveBrand")
            response['vads_card_number'] = card_details.get("pan")
            response['vads_expiry_month'] = str(card_details.get("expiryMonth"))
            response['vads_expiry_year'] = str(card_details.get("expiryYear"))

            response['vads_payment_option_code'] = card_details.get("installmentNumber")

            autorization_response = card_details.get("authorizationResponse", False)
            if autorization_response:
                response['vads_auth_result'] = autorization_response.get("authorizationResult")
                response['vads_authorized_amount'] = autorization_response.get("amount")

            authentication_response = card_details.get("authenticationResponse", False)
            threeds_response = card_details.get("threeDSResponse", False)

            if authentication_response:
                value = authentication_response.get("value", False)
                if value:
                    response['vads_threeds_status'] = value.get("status")
                    response['vads_threeds_auth_type'] = value.get("authenticationType")

                    authentication_value = value.get("authenticationValue", False)
                    if authentication_value:
                        response["vads_threeds_cavv"] = authentication_value.get("value")
            elif threeds_response:
                authentication_result_data = threeds_response.get("authenticationResultData", False)
                if authentication_result_data:
                    response["vads_threeds_cavv"] = authentication_result_data.get("cavv")
                    response["vads_threeds_status"] = authentication_result_data.get("status")
                    response["vads_threeds_auth_type"] = authentication_result_data.get("threeds_auth_type")

        fraud_management = transaction_details.get("fraudManagement", False)
        if fraud_management:
            risk_control = fraud_management.get("riskControl", False)
            if risk_control:
                response['vads_risk_control'] = ""
                for value in risk_control:
                    response['vads_risk_control'] += "{" + value['name']+ "}={" + value['result'] + "};"

            risk_assessments = fraud_management.get("riskAssessments", False)
            if risk_assessments:
                response["vads_risk_assessment_result"] = risk_assessments.get("results")

    return response
