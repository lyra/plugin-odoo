# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.payment.tests.common import PaymentCommon


class LyraCommon(PaymentCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.lyra = cls._prepare_acquirer(
            "lyra",
            update_values={
                "lyra_redirect_enabled": "1",
            },
        )

        # Override defaults
        cls.acquirer = cls.lyra
        cls.currency = cls.currency_euro

        # Vanuatu vatu VT not supported by Lyra
        cls.currency_vuv = cls._prepare_currency("VUV")
