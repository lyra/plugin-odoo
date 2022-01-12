# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import urllib.parse as urlparse
from hashlib import sha1, sha256
import base64
import hmac
import math
from ..helpers import constants
from ..controllers.main import LyraController
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    def _get_notify_url(self):
        base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        return urlparse.urljoin(base_url, LyraController._notify_url)

    def _get_languages(self):
        languages = constants.LYRA_LANGUAGES
        return [(c, l) for c, l in languages.items()]

    # TODO: manage lyra multi provider
    # To be considered (like in alipay) using a differnet payment_method ?? not sure to
    # understand the impact at the time writing
    provider = fields.Selection(
        selection_add=[("lyra", "Lyra Collect - Standard payment")],
        ondelete={"lyra": "set default"},
    )
    lyra_site_id = fields.Char(
        string="Shop ID",
        help="The identifier provided by Lyra Collect.",
        default=constants.LYRA_PARAMS.get("SITE_ID"),
    )
    lyra_key_test = fields.Char(
        string="Key in test mode",
        help=(
            "Key provided by Lyra Collect for test mode "
            "(available in Lyra Expert Back Office)."
        ),
        default=constants.LYRA_PARAMS.get("KEY_TEST"),
    )
    lyra_key_prod = fields.Char(
        string="Key in production mode",
        help="Key provided by Lyra Collect (available in Lyra Expert Back Office after enabling production mode).",
        default=constants.LYRA_PARAMS.get("KEY_PROD"),
    )
    lyra_sign_algo = fields.Selection(
        string="Signature algorithm",
        help="Algorithm used to compute the payment form signature. Selected algorithm must be the same as one configured in the Lyra Expert Back Office.",
        selection=[("SHA-1", "SHA-1"), ("SHA-256", "HMAC-SHA-256")],
        default=constants.LYRA_PARAMS.get("SIGN_ALGO"),
    )
    lyra_notify_url = fields.Char(
        string="Instant Payment Notification URL",
        help="URL to copy into your Lyra Expert Back Office > Settings > Notification rules.",
        default=_get_notify_url,
        readonly=True,
    )
    lyra_gateway_url = fields.Char(
        string="Payment page URL",
        help="Link to the payment page.",
        default=constants.LYRA_PARAMS.get("GATEWAY_URL"),
    )
    lyra_language = fields.Selection(
        string="Default language",
        help="Default language on the payment page.",
        default=constants.LYRA_PARAMS.get("LANGUAGE"),
        selection=_get_languages,
        required=True,
    )
    lyra_available_languages = fields.Many2many(
        "lyra.language",
        string="Available languages",
        column1="code",
        column2="label",
        help="Languages available on the payment page. If you do not select any, all the supported languages will be available.",
    )
    lyra_capture_delay = fields.Char(
        string="Capture delay",
        help="The number of days before the bank capture (adjustable in your Lyra Expert Back Office).",
    )
    lyra_validation_mode = fields.Selection(
        string="Validation mode",
        help="If manual is selected, you will have to confirm payments manually in your Lyra Expert Back Office.",
        selection=[
            ("-1", "Lyra Expert Back Office Configuration"),
            ("0", "Automatic"),
            ("1", "Manual"),
        ],
    )
    lyra_payment_cards = fields.Many2many(
        "lyra.card",
        string="Card types",
        column1="code",
        column2="label",
        help="The card type(s) that can be used for the payment. Select none to use gateway configuration.",
    )
    lyra_threeds_min_amount = fields.Char(
        string="Disable 3DS",
        help="Amount below which 3DS will be disabled. Needs subscription to selective 3DS option. For more information, refer to the module documentation.",
    )
    lyra_redirect_enabled = fields.Selection(
        string="Automatic redirection",
        help="If enabled, the buyer is automatically redirected to your site at the end of the payment.",
        selection=[("0", "Disabled"), ("1", "Enabled")],
    )
    lyra_redirect_success_timeout = fields.Char(
        string="Redirection timeout on success",
        help="Time in seconds (0-300) before the buyer is automatically redirected to your website after a successful payment.",
    )
    lyra_redirect_success_message = fields.Char(
        string="Redirection message on success",
        help="Message displayed on the payment page prior to redirection after a successful payment.",
        default="Redirection to shop in a few seconds...",
    )
    lyra_redirect_error_timeout = fields.Char(
        string="Redirection timeout on failure",
        help="Time in seconds (0-300) before the buyer is automatically redirected to your website after a declined payment.",
    )
    lyra_redirect_error_message = fields.Char(
        string="Redirection message on failure",
        help="Message displayed on the payment page prior to redirection after a declined payment.",
        default="Redirection to shop in a few seconds...",
    )
    lyra_return_mode = fields.Selection(
        string="Return mode",
        help="Method that will be used for transmitting the payment result from the payment page to your shop.",
        selection=[("GET", "GET"), ("POST", "POST")],
    )
    # lyra_multi_warning = fields.Boolean(compute='_lyra_compute_multi_warning')
    # lyra_multi_count = fields.Char(string='Count', help='Total number of payments.')
    # lyra_multi_period = fields.Char(string='Period', help='Delay (in days) between payments.')
    # lyra_multi_first = fields.Char(string='1st payment', help='Amount of first payment, in percentage of total amount. If empty, all payments will have the same amount.')

    @api.model
    def _get_compatible_acquirers(self, *args, currency_id=None, **kwargs):
        """Override of payment to unlist lyra acquirers for unsupported currencies."""
        acquirers = super()._get_compatible_acquirers(
            *args, currency_id=currency_id, **kwargs
        )
        currency = self.env["res.currency"].browse(currency_id).exists()
        if currency and currency.name not in [
            cur[0] for cur in constants.LYRA_CURRENCIES
        ]:
            acquirers = acquirers.filtered(lambda a: a.provider != "lyra")

        return acquirers

    def _lyra_build_sign(self, values):
        key = self.lyra_key_prod if self.state == "enabled" else self.lyra_key_test
        sign = ""
        for k in sorted(values.keys()):
            if k.startswith("vads_"):
                sign += values[k] + "+"

        sign += key

        if self.lyra_sign_algo == "SHA-1":
            shasign = sha1(sign.encode("utf-8")).hexdigest()
        else:
            shasign = base64.b64encode(
                hmac.new(key.encode("utf-8"), sign.encode("utf-8"), sha256).digest()
            ).decode("utf-8")

        return shasign

    def _lyra_get_api_url(self):
        # same gateway in prod and test
        return self.lyra_gateway_url

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != "lyra":
            return super()._get_default_payment_method_id()
        return self.env.ref("payment_lyra.payment_method_lyra").id
