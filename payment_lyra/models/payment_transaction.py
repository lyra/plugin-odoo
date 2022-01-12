# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from werkzeug import urls
from datetime import datetime
from odoo import _, api, models, release
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare
from ..helpers import tools, constants
import urllib.parse as urlparse
from odoo.tools import float_round
from odoo.addons.payment_lyra.controllers.main import LyraController

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    # PV: do we really wan't to save those kind of information in case
    # of direct payment ? that cans be sencitive data ?
    # I'have the feeling that we should manage lyramulti using payment.token model,
    # not sure how this is handle by lyra, it would be great to get a token in case
    # of lyramulti and use it for later payments I suppose instead of saving following
    # sensitive data
    # payzen_trans_status = fields.Char(_('Transaction status'))
    # payzen_card_brand = fields.Char(_('Means of payment'))
    # payzen_card_number = fields.Char(_('Card number'))
    # payzen_expiration_date = fields.Char(_('Expiration date'))
    # payzen_auth_result = fields.Char(_('Authorization result'))
    # payzen_raw_data = fields.Text(string=_('Transaction log'), readonly=True)

    def _get_specific_rendering_values(self, processing_values):
        """Override of payment to return lyra-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values:
          The generic and specific processing values of the transaction
        :return: The dict of acquirer-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != "lyra":
            return res

        base_url = self.acquirer_id.get_base_url()

        # trans_id is the number of 1/10 seconds from midnight.
        now = datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        delta = int((now - midnight).total_seconds() * 10)
        trans_id = str(delta).rjust(6, "0")

        threeds_mpi = ""
        if (
            self.acquirer_id.lyra_threeds_min_amount
            and float(self.acquirer_id.lyra_threeds_min_amount) > self.amount
        ):
            threeds_mpi = "2"

        # Check currency.
        currency_num = tools.find_currency(self.currency_id.name)
        if currency_num is None:
            _logger.error(
                "Lyra plugin cannot find a numeric code for the "
                "current shop currency %s.",
                self.currency_id.name,
            )
            raise ValidationError(
                _("The currency %s is not supported by lyra payment gateway.")
                % (self.currency_id.name,)
            )

        # Amount in cents.
        k = int(self.currency_id.decimal_places)
        amount = int(float_round(self.amount * (10 ** k), 0))

        def partner_split_name(partner_name):
            return " ".join(partner_name.split()[:-1]), " ".join(
                partner_name.split()[-1:]
            )

        first_name, last_name = partner_split_name(self.partner_name)
        partner_lang_iso_code = self.partner_id.lang[:2]

        rendering_values = {
            "notify_url": urls.url_join(base_url, LyraController._notify_url),
            "return_url": urls.url_join(base_url, LyraController._return_url),
            "vads_site_id": self.acquirer_id.lyra_site_id,
            "vads_amount": str(amount),
            "vads_currency": str(currency_num),
            "vads_trans_date": str(datetime.utcnow().strftime("%Y%m%d%H%M%S")),
            "vads_trans_id": str(trans_id),
            "vads_ctx_mode": "PRODUCTION"
            if self.acquirer_id.state == "enabled"
            else "TEST",
            "vads_page_action": "PAYMENT",
            "vads_action_mode": "INTERACTIVE",
            # TODO: manage lyramulti
            "vads_payment_config": "SINGLE",
            "vads_version": constants.LYRA_PARAMS.get("GATEWAY_VERSION"),
            "vads_url_return": urlparse.urljoin(base_url, LyraController._return_url),
            "vads_order_id": self.reference,
            "vads_contrib": (
                f"{constants.LYRA_PARAMS.get('CMS_IDENTIFIER')}_"
                f"{constants.LYRA_PARAMS.get('PLUGIN_VERSION')}/"
                f"{release.version}"
            ),
            "vads_language": partner_lang_iso_code
            if partner_lang_iso_code
            in self.acquirer_id.lyra_available_languages.mapped("code")
            else self.acquirer_id.lyra_language,
            "vads_available_languages": ";".join(
                self.acquirer_id.lyra_available_languages.mapped("code")
            ),
            "vads_capture_delay": self.acquirer_id.lyra_capture_delay or "",
            "vads_validation_mode": (
                self.acquirer_id.lyra_validation_mode
                if self.acquirer_id.lyra_validation_mode != "-1"
                else ""
            ),
            "vads_payment_cards": ";".join(
                self.acquirer_id.lyra_payment_cards.mapped("code")
            ),
            "vads_return_mode": str(self.acquirer_id.lyra_return_mode),
            "vads_threeds_mpi": threeds_mpi,
            # Customer info.
            "vads_cust_id": str(self.partner_id.id),
            "vads_cust_first_name": first_name[0:62] or "",
            "vads_cust_last_name": last_name[0:62] or "",
            "vads_cust_address": self.partner_address
            and self.partner_address[0:254]
            or "",
            "vads_cust_zip": self.partner_zip and self.partner_zip[0:62] or "",
            "vads_cust_city": self.partner_city and self.partner_city[0:62] or "",
            "vads_cust_state": self.partner_state_id
            and self.partner_state_id.name[0:62]
            or "",
            "vads_cust_country": self.partner_country_id
            and self.partner_country_id.code.upper()
            or "",
            "vads_cust_email": self.partner_email and self.partner_email[0:126] or "",
            "vads_cust_phone": self.partner_phone and self.partner_phone[0:31] or "",
            # PV: not sure we are always in e-commerce use case with shipping
            # and there fore not sure to understand why the payment gateway require
            # shipping informations  Shipping info.
            # ... but require empty value for lyra signature control
            "vads_ship_to_first_name": "",
            "vads_ship_to_last_name": "",
            "vads_ship_to_street": "",
            "vads_ship_to_zip": "",
            "vads_ship_to_city": "",
            "vads_ship_to_state": "",
            "vads_ship_to_country": "",
            "vads_ship_to_phone_num": "",
        }
        if self.acquirer_id.lyra_redirect_enabled == "1":
            rendering_values.update(
                {
                    "vads_redirect_success_timeout": self.acquirer_id.lyra_redirect_success_timeout,
                    "vads_redirect_success_message": self.acquirer_id.lyra_redirect_success_message,
                    "vads_redirect_error_timeout": self.acquirer_id.lyra_redirect_error_timeout,
                    "vads_redirect_error_message": self.acquirer_id.lyra_redirect_error_message,
                }
            )

        sign = self.acquirer_id._lyra_build_sign(rendering_values)
        rendering_values.update(
            {
                "lyra_signature": sign,
                "api_url": self.acquirer_id._lyra_get_api_url(),
            }
        )
        return rendering_values

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        """Override of payment to find the transaction based on lyra data.

        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The feedback data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if inconsistent data were received
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != "lyra":
            return tx
        reference = data.get("vads_order_id")
        tx = self.search([("reference", "=", reference), ("provider", "=", "lyra")])
        if not tx:
            raise ValidationError(
                _("Lyra: No transaction found matching reference %s.") % (reference,)
            )

        # Verify signature (done here because we need the reference to get the acquirer)
        sign_check = tx.acquirer_id._lyra_build_sign(data)
        sign = data.get("signature")
        if sign.upper() != sign_check.upper():
            raise ValidationError(
                _("Lyra: Expected signature %(sc)s but received %(sign)s.")
                % dict(sc=sign_check, sign=sign)
            )

        return tx

    def _process_feedback_data(self, data):
        """Override of payment to process the transaction based on lyra data.

        Note: self.ensure_one()

        :param dict data: The feedback data sent by the provider
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        super()._process_feedback_data(data)
        if self.provider != "lyra":
            return
        self = self.with_context(lang=self.partner_id.lang)

        # PV: TODO sort out if we could use odoo authorized state while receiving authorized status
        # from payzen service
        payzen_statuses = {
            "success": ["AUTHORISED", "CAPTURED", "ACCEPTED"],
            "pending": [
                "AUTHORISED_TO_VALIDATE",
                "WAITING_AUTHORISATION",
                "WAITING_AUTHORISATION_TO_VALIDATE",
                "INITIAL",
                "UNDER_VERIFICATION",
                "WAITING_FOR_PAYMENT",
                "PRE_AUTHORISED",
            ],
            "cancel": ["ABANDONED"],
        }
        # TODO: lyramulti save required data to manage next payments
        self.acquirer_reference = data.get("vads_trans_uuid")
        status = data.get("vads_trans_status")

        # from https://payzen.io/en-EN/form-payment/reference/vads-result.html
        vad_result = {
            "00": _("Action successfully completed."),
            "02": _("The merchant must contact the cardholder’s bank. (Deprecated)"),
            "05": _("Action rejected."),
            "17": _("Action canceled by the buyer."),
            "30": _(
                "Request format error. To be associated with the value of the vads_extra_result field."
            ),
            "96": _("Technical error."),
        }.get(
            data.get("vads_result"),
            data.get(
                "vads_result",
                _("Expected vads_result key which is not set by lyra the service"),
            ),
        )

        if status in payzen_statuses["success"]:
            self._set_done()
        elif status in payzen_statuses["pending"]:
            self._set_pending()
        elif status in payzen_statuses["cancel"]:
            self._set_canceled(
                state_message=_("Payment for transaction #%s is cancelled (%s).")
                % (self.reference, vad_result),
            )
        else:
            auth_result = data.get("vads_auth_result")
            auth_message = _(
                "See the transaction details for more information (%s)."
            ) % (auth_result,)

            _logger.info(
                "PayZen payment error, transaction status: %s, authorization result: %s.",
                status,
                auth_result,
            )
            self._set_error(
                _("Payment for transaction #%s has been refused (%s). Auth result: %s.")
                % (
                    self.reference,
                    vad_result,
                    auth_message,
                ),
            )
