# Part of Odoo. See LICENSE file for full copyright and licensing details.
import pytest
from odoo.exceptions import ValidationError
from odoo.tests import tagged, HttpCase
from odoo.tools import mute_logger

from .common import LyraCommon
from ..controllers.main import LyraController

from odoo.addons.payment.tests.http_common import PaymentHttpCommon


@tagged("post_install", "-at_install")
@pytest.mark.skip(
    reason=(
        "No way of currently testing this with pytest-odoo because:\n"
        "* that require an open odoo port\n"
        "* the open port should use the same pgsql transaction\n"
        "* payment.transaction class must be mocked\n\n"
        "Please use odoo --test-enable to launch those test"
    )
)
class LyraHttpTest(LyraCommon, HttpCase):
    @classmethod
    def setUpClass(cls):
        @classmethod
        def base_url(cls):
            """LyuraCommon depends on PaymentCommon > PaymentTestUtils
            which define base_url as string method
            """
            return cls.env["ir.config_parameter"].get_param("web.base.url")

        cls.base_url = base_url
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.PaymentTransaction = self.env["payment.transaction"]
        # _handle_feedback_data is tested in LyraTest class test case
        # here we have to ensure end points (return and notify)
        # properly call this method parent method
        # _handle_feedback_data
        # ├── _get_tx_from_feedback_data
        # ├── _process_feedback_data
        # └── _execute_callback
        self.calls = 0

        def handle_feedback_data(_, provider, data):
            self.assertEqual(provider, "lyra")
            self.assertEqual(data, {"vads_test": "test-value"})
            self.calls += 1
            return self.PaymentTransaction.new({"reference": "ABC"})

        self.PaymentTransaction._patch_method(
            "_handle_feedback_data", handle_feedback_data
        )
        self.addCleanup(self.PaymentTransaction._revert_method, "_handle_feedback_data")

    def test_return_get(self):
        url = self._build_url(LyraController._return_url)
        response = self.opener.get(url + "?vads_test=test-value")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.calls, 1)
        response = self.opener.post(url, data={"vads_test": "test-value"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.calls, 2)

    def test_notify_post(self):
        url = self._build_url(LyraController._notify_url)
        response = self.opener.post(url, data={"vads_test": "test-value"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.calls, 1)


@tagged("post_install", "-at_install")
class LyraTest(LyraCommon):
    def assert_redirect_to_lyra_standard(self, **extra_expected_values):
        return_url = self._build_url(LyraController._return_url)
        expected_values = {
            "vads_action_mode": "INTERACTIVE",
            "vads_available_languages": "",
            "vads_capture_delay": "",
            "vads_contrib": "Odoo_15_2.0.0/15.0",
            "vads_ctx_mode": "TEST",
            "vads_currency": "978",
            "vads_cust_address": "Huge Street 2/543",
            "vads_cust_city": "Sin City",
            "vads_cust_country": "BE",
            "vads_cust_email": "norbert.buyer@example.com",
            "vads_cust_first_name": "Norbert",
            "vads_cust_last_name": "Buyer",
            "vads_cust_phone": "0032 12 34 56 78",
            "vads_cust_state": "",
            "vads_cust_zip": "1000",
            "vads_language": "en",
            "vads_order_id": "Test Transaction",
            "vads_page_action": "PAYMENT",
            "vads_payment_cards": "",
            "vads_payment_config": "SINGLE",
            "vads_return_mode": "GET",
            "vads_ship_to_city": "",
            "vads_ship_to_country": "",
            "vads_ship_to_first_name": "",
            "vads_ship_to_last_name": "",
            "vads_ship_to_phone_num": "",
            "vads_ship_to_state": "",
            "vads_ship_to_street": "",
            "vads_ship_to_zip": "",
            "vads_site_id": "12345678",
            "vads_threeds_mpi": "",
            "vads_validation_mode": "",
            "vads_version": "V2",
            "vads_redirect_error_message": "Redirection to shop in a few seconds...",
            "vads_redirect_error_timeout": "5",
            "vads_redirect_success_message": "Redirection to shop in a few seconds...",
            "vads_redirect_success_timeout": "5",
            "vads_url_return": return_url,
            # following values could change until mocking few methods
            # worth to comment in the mean time in test the subset
            # 'signature': 'hayjQA7We7h+aNAjgkuOxKer1cNr0JS6yGsd8HGF7Ec=',
            # 'vads_cust_id': '208',
            # 'vads_trans_date': '20220107110029',
            # 'vads_trans_id': '396291',
        }
        expected_values.update(**extra_expected_values)

        tx_sudo = self.create_transaction(flow="redirect")
        with mute_logger("odoo.addons.payment.models.payment_transaction"):
            processing_values = tx_sudo._get_processing_values()
        form_info = self._extract_values_from_html_form(
            processing_values["redirect_form_html"]
        )

        self.assertEqual(form_info["action"], "https://secure.lyra.com/vads-payment/")
        self.maxDiff = None
        # assertDictContainsSubset is deprecated from version 3.2 and
        # self.assertDictContainsSubset(
        #     expected_values,
        #     form_info["inputs"],
        self.assertEqual(
            form_info["inputs"],
            {**form_info["inputs"], **expected_values},
            "Lyra: invalid inputs specified in the redirect form.",
        )

    def test_redirect_to_lyra_standard(self):
        self.amount = 1111.11
        self.assert_redirect_to_lyra_standard(vads_amount="111111")

    def test_redirect_to_lyra_vads_ctx_mode(self):
        self.lyra.state = "enabled"
        self.amount = 4
        self.assert_redirect_to_lyra_standard(
            vads_ctx_mode="PRODUCTION", vads_amount="400"
        )

    def test_wrong_currency_get_specific_rendering_values(self):
        self.currency = self.currency_vuv

        with mute_logger("odoo.addons.payment_lyra.models.payment_transaction"):
            with self.assertRaisesRegex(
                ValidationError,
                r"The currency VUV is not supported by lyra payment gateway\.",
            ):
                self.assert_redirect_to_lyra_standard()

    def test_redirect_to_lyra_vads_langauge(self):
        self.amount = 4
        self.reference = "TO1"
        fr_BE = self.env.ref("base.lang_fr_BE")
        fr_BE.active = True
        self.partner.lang = "fr_BE"
        self.lyra.lyra_available_languages = self.env["lyra.language"].search(
            [("code", "in", ["fr", "en"])]
        )
        self.lyra.lyra_language = "en"
        self.assert_redirect_to_lyra_standard(
            vads_order_id="TO1",
            vads_amount="400",
            vads_language="fr",
            vads_available_languages="en;fr",
        )

        self.reference = "TO2"
        hu_HU = self.env.ref("base.lang_hu")
        hu_HU.active = True
        self.partner.lang = "hu_HU"
        self.lyra.lyra_available_languages = self.env["lyra.language"].search(
            [("code", "in", ["fr", "en"])]
        )
        self.lyra.lyra_language = "ru"
        # this a bit a non sens but let assume odoo configurator are properly
        # knowing why they do that, here we fall back to default language as long hu is
        # not suported by lyra (even if ru is not list in available languages)
        self.assert_redirect_to_lyra_standard(
            vads_order_id="TO2",
            vads_amount="400",
            vads_language="ru",
            vads_available_languages="en;fr",
        )

    def test_redirect_to_lyra_vads_capture_delay(self):
        self.lyra.lyra_capture_delay = "2"
        self.amount = 4
        self.assert_redirect_to_lyra_standard(vads_capture_delay="2", vads_amount="400")

    def test_redirect_to_lyra_vads_payment_cards(self):
        self.amount = 4
        self.lyra.lyra_payment_cards = self.env["lyra.card"].search(
            [("code", "in", ["EDENRED_EC", "VISA"])]
        )
        self.assert_redirect_to_lyra_standard(
            vads_payment_cards="EDENRED_EC;VISA", vads_amount="400"
        )

    def test_redirect_to_lyra_redirect_enabled(self):
        self.lyra.lyra_redirect_enabled = "1"
        self.lyra.lyra_redirect_success_timeout = "22"
        self.lyra.lyra_redirect_success_message = "success"
        self.lyra.lyra_redirect_error_timeout = "33"
        self.lyra.lyra_redirect_error_message = "error"
        self.amount = 4
        self.assert_redirect_to_lyra_standard(
            vads_redirect_success_timeout=self.lyra.lyra_redirect_success_timeout,
            vads_redirect_success_message=self.lyra.lyra_redirect_success_message,
            vads_redirect_error_timeout=self.lyra.lyra_redirect_error_timeout,
            vads_redirect_error_message=self.lyra.lyra_redirect_error_message,
            vads_amount="400",
        )

    def test_redirect_to_lyra_threeds_min_amount(self):
        self.lyra.lyra_threeds_min_amount = 5
        self.amount = 4
        self.reference = "TO1"
        self.assert_redirect_to_lyra_standard(
            vads_order_id="TO1", vads_amount="400", vads_threeds_mpi="2"
        )
        self.amount = 6
        self.reference = "TO2"
        self.assert_redirect_to_lyra_standard(
            vads_order_id="TO2", vads_amount="600", vads_threeds_mpi=""
        )

    def test_get_compatible_acquirers(self):
        acquierers = self.env["payment.acquirer"]._get_compatible_acquirers(
            self.env.company.id, self.partner.id, currency_id=self.currency_euro.id
        )
        self.assertTrue("lyra" in acquierers.mapped("provider"))
        acquierers = self.env["payment.acquirer"]._get_compatible_acquirers(
            self.env.company.id, self.partner.id, currency_id=self.currency_vuv.id
        )
        self.assertTrue("lyra" not in acquierers.mapped("provider"))

    def test_signature(self):
        data = {
            "signature": "OH/MI+zozsepk3XZWDJdBPyOgidXRUVbyjIhyKgD9nk=",
            "vads_acquirer_network": "CB",
            "vads_action_mode": "INTERACTIVE",
            "vads_amount": "163500",
            "vads_auth_mode": "FULL",
            "vads_auth_number": "3fe04e",
            "vads_auth_result": "00",
            "vads_bank_label": "Banque de démo et de l'innovation",
            "vads_bank_product": "MSI",
            "vads_brand_management": '{"userChoice":false,"brandList":"CB|MAESTRO","brand":"CB"}',
            "vads_capture_delay": "0",
            "vads_card_brand": "CB",
            "vads_card_country": "US",
            "vads_card_number": "500055XXXXXX0011",
            "vads_change_rate": "1.1334000000",
            "vads_contract_used": "1234567",
            "vads_contrib": "Odoo_10-14_1.2.1/'14.0",
            "vads_ctx_mode": "TEST",
            "vads_currency": "840",
            "vads_cust_address": "25 rue billing reste adresse billing",
            "vads_cust_city": "orléans",
            "vads_cust_country": "FR",
            "vads_cust_email": "petrus-v@hormail.fr",
            "vads_cust_first_name": "Pïerre",
            "vads_cust_id": "41",
            "vads_cust_last_name": "Verkest",
            "vads_cust_name": "Pïerre Verkest",
            "vads_cust_phone": "0606060606",
            "vads_cust_state": "",
            "vads_cust_zip": "45000",
            "vads_effective_amount": "144256",
            "vads_effective_creation_date": "20220107142526",
            "vads_effective_currency": "978",
            "vads_expiry_month": "6",
            "vads_expiry_year": "2023",
            "vads_extra_result": "",
            "vads_language": "en",
            "vads_occurrence_type": "UNITAIRE",
            "vads_operation_type": "DEBIT",
            "vads_order_id": "S00036-6",
            "vads_page_action": "PAYMENT",
            "vads_payment_certificate": "659ab61d544a83ca7bf6202a76a7399a6f74e6b9",
            "vads_payment_config": "SINGLE",
            "vads_payment_src": "EC",
            "vads_pays_ip": "FR",
            "vads_presentation_date": "20220107142526",
            "vads_result": "00",
            "vads_sequence_number": "1",
            "vads_site_id": "44387878",
            "vads_threeds_auth_type": "CHALLENGE",
            "vads_threeds_cavv": "Q**************************=",
            "vads_threeds_cavvAlgorithm": "2",
            "vads_threeds_eci": "05",
            "vads_threeds_enrolled": "Y",
            "vads_threeds_error_code": "",
            "vads_threeds_exit_status": "10",
            "vads_threeds_sign_valid": "1",
            "vads_threeds_status": "Y",
            "vads_threeds_xid": "UmU0QjZGN29UVGFtT3R2dE1kN0U=",
            "vads_tid": "001",
            "vads_trans_date": "20220107142526",
            "vads_trans_id": "519266",
            "vads_trans_status": "AUTHORISED",
            "vads_trans_uuid": "5b12dd14c81b4314ac9c5136d922dbdb",
            "vads_validation_mode": "0",
            "vads_version": "V2",
            "vads_warranty_result": "YES",
        }
        # self.lyra_key_prod if self.state == 'enabled' else self.lyra_key_test
        self.lyra.state = "enabled"
        self.lyra.lyra_key_prod = "test-lyra-secret"
        self.lyra.lyra_key_test = "test-wrong-key"
        self.assertEqual(self.lyra._lyra_build_sign(data), data["signature"])
        self.lyra.state = "test"

        self.assertNotEqual(self.lyra._lyra_build_sign(data), data["signature"])

        self.lyra.lyra_key_test = "test-lyra-secret"
        self.lyra.lyra_key_prod = "test-wrong-key"
        self.assertEqual(self.lyra._lyra_build_sign(data), data["signature"])
        self.lyra.state = "enabled"
        self.assertNotEqual(self.lyra._lyra_build_sign(data), data["signature"])

    def _prepare_data(self, vads_order_id="SO004", **kwargs):
        self.amount = 1442.56
        self.reference = vads_order_id

        # typical data posted by lyra after client has successfully paid
        lyra_post_data = {
            "vads_amount": "224000",
            "vads_auth_mode": "FULL",
            "vads_auth_number": "3fe19a",
            "vads_auth_result": "00",
            "vads_capture_delay": "0",
            "vads_card_brand": "CB",
            "vads_card_number": "597010XXXXXX0018",
            "vads_payment_certificate": "b55c099bf83dc6ea777cd3f053de6e2728be7990",
            "vads_ctx_mode": "TEST",
            "vads_currency": "840",
            "vads_effective_amount": "144256",
            "vads_effective_currency": "978",
            "vads_site_id": "44387878",
            "vads_trans_date": "20220107135322",
            "vads_trans_id": "500021",
            "vads_trans_uuid": "bd6fe2b43df34534b3b12fffcf0f078f",
            "vads_validation_mode": "0",
            "vads_version": "V2",
            "vads_warranty_result": "NO",
            "vads_payment_src": "EC",
            "vads_order_id": self.reference,
            "vads_cust_email": "petrus-v@hormail.fr",
            "vads_cust_id": "41",
            "vads_cust_name": "Pierre+Verkest",
            "vads_cust_first_name": "Pierre",
            "vads_cust_last_name": "Verkest",
            "vads_cust_address": "25+rue+billing+reste+adresse+billing",
            "vads_cust_zip": "45000",
            "vads_cust_city": "orleans",
            "vads_cust_country": "FR",
            "vads_cust_phone": "0606060606",
            "vads_contrib": "Odoo_10-14_2.0.0/15.0",
            "vads_cust_state": "",
            "vads_tid": "001",
            "vads_sequence_number": "1",
            "vads_acquirer_network": "CB",
            "vads_contract_used": "1234567",
            "vads_trans_status": "AUTHORISED",
            "vads_expiry_month": "6",
            "vads_expiry_year": "2023",
            "vads_bank_label": "Banque+de+démo+et+de+l'innovation",
            "vads_bank_product": "MCW",
            "vads_change_rate": "1.1334000000",
            "vads_pays_ip": "FR",
            "vads_presentation_date": "20220107135322",
            "vads_effective_creation_date": "20220107135322",
            "vads_occurrence_type": "UNITAIRE",
            "vads_operation_type": "DEBIT",
            "vads_result": "00",
            "vads_extra_result": "",
            "vads_card_country": "FR",
            "vads_language": "en",
            "vads_brand_management": '{"userChoice":"false", "brandList": "MASTERCARD", "brand": "CB"}',
            "vads_action_mode": "INTERACTIVE",
            "vads_payment_config": "SINGLE",
            "vads_page_action": "PAYMENT",
            "vads_threeds_enrolled": "",
            "vads_threeds_auth_type": "",
            "vads_threeds_eci": "",
            "vads_threeds_xid": "",
            "vads_threeds_cavvAlgorithm": "",
            "vads_threeds_status": "",
            "vads_threeds_sign_valid": "",
            "vads_threeds_error_code": "15",
            "vads_threeds_exit_status": "15",
            "vads_threeds_cavv": "",
            "signature": "M+QC8YuSApE8ZZwJkk8qtX64kfbWBwuL0hPtzrXpD/0=",
        }
        lyra_post_data.update(**kwargs)
        return lyra_post_data

    def _handle_redirec_flow_tx(self, **kwargs):
        lyra_post_data = self._prepare_data(**kwargs)
        tx = self.create_transaction(flow="redirect")
        tx._handle_feedback_data("lyra", lyra_post_data)
        return tx

    def test_cancel_return_from_lyra_gateway(self):
        with mute_logger("odoo.addons.payment_lyra.models.payment_transaction"):
            tx = self._handle_redirec_flow_tx(
                vads_order_id="SO004-2",
                vads_trans_status="ABANDONED",
                signature="VQye6LZjOdVmKfiBQDKwWRbF/0lnTOsUc/cfKQxCZ9g=",
            )
        self.assertEqual(
            tx.state,
            "cancel",
            "lyra: unexpected status code should put tx in cancel state",
        )

    def test_pending_return_from_lyra_gateway(self):
        with mute_logger("odoo.addons.payment_lyra.models.payment_transaction"):
            tx = self._handle_redirec_flow_tx(
                vads_order_id="SO004-2",
                vads_trans_status="AUTHORISED_TO_VALIDATE",
                signature="WBn9hDJvrKKx9Fb/lHd5RJ5IQP6d916vimjXFgGbeTg=",
            )

        self.assertEqual(
            tx.state,
            "pending",
            "lyra: unexpected status code should put tx in pending state",
        )

    def test_error_return_from_lyra_gateway(self):
        with mute_logger("odoo.addons.payment_lyra.models.payment_transaction"):
            tx = self._handle_redirec_flow_tx(
                vads_order_id="SO004-2",
                vads_trans_status="UNEXISTING_STATUS",
                signature="yidJgzNexlmR9xPyTs6HmspJwszYlWcpFpWN+gwMZfw=",
            )
        self.assertEqual(
            tx.state,
            "error",
            "lyra: unexpected status code should put tx in error state",
        )

    def test_wrong_signature(self):
        with self.assertRaisesRegex(
            ValidationError, r"Lyra: Expected signature.*but received wrong_signature\."
        ):
            self._handle_redirec_flow_tx(
                vads_order_id="SO004-2", signature="wrong_signature"
            )

    def test_unkown_transaction(self):
        lyra_post_data = self._prepare_data(vads_order_id="SO0055")

        with self.assertRaisesRegex(
            ValidationError, r"Lyra: No transaction found matching reference SO0055\."
        ):  # unknown transaction
            self.env["payment.transaction"]._handle_feedback_data(
                "lyra", lyra_post_data
            )

        lyra_post_data = self._prepare_data(vads_order_id=None)
        with self.assertRaisesRegex(
            ValidationError, r"Lyra: No transaction found matching reference None\."
        ):
            self.env["payment.transaction"]._handle_feedback_data(
                "lyra", lyra_post_data
            )

    def test_return_from_lyra_gateway(self):
        tx = self._handle_redirec_flow_tx(
            vads_trans_uuid="bd6fe2b43df34534b3b12fffcf0f078f",
        )
        self.assertEqual(
            tx.state, "done", "Lyra: validation did not put tx into done state"
        )
        self.assertEqual(
            tx.acquirer_reference,
            "bd6fe2b43df34534b3b12fffcf0f078f",
            "Lyra: validation did not update tx payid",
        )
