# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

import base64
from datetime import datetime
from hashlib import sha1, sha256
import hmac
import logging
from os import path

from pkg_resources import parse_version

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from odoo.tools import convert_xml_import
from odoo.tools import float_round
from odoo.tools import get_lang
from odoo.tools.float_utils import float_compare
from odoo.http import request

from ..controllers.main import LyraController
from ..helpers import constants, tools
from .card import LyraCard
from .language import LyraLanguage
from odoo.addons.payment import utils as payment_utils

import urllib.parse as urlparse
import re

_logger = logging.getLogger(__name__)

class ProviderLyra(models.Model):
    _inherit = 'payment.provider'
    _name = 'payment.provider'

    def _get_notify_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return urlparse.urljoin(base_url, LyraController._notify_url)

    def _get_languages(self):
        languages = constants.LYRA_LANGUAGES
        return [(c, _(l)) for c, l in languages.items()]

    def _lyra_compute_multi_warning(self):
        for provider in self:
            provider.lyra_multi_warning = (constants.LYRA_PLUGIN_FEATURES.get('restrictmulti') == True) if (provider.code == 'lyramulti') else False

    def lyra_get_doc_field_value():
        docs_uri = constants.LYRA_ONLINE_DOC_URI
        doc_field_html = ''
        for lang, doc_uri in docs_uri.items():
            html = '<a href="%s%s">%s</a> '%(doc_uri,'odoo16/sitemap.html', constants.LYRA_DOCUMENTATION.get(lang))
            doc_field_html += html

        return doc_field_html

    def _get_payment_data_entry_mode(self):
        payment_data_entry_mode = constants.LYRA_PAYMENT_DATA_ENTRY_MODE
        if constants.LYRA_PLUGIN_FEATURES.get('smartform') == False:
            del payment_data_entry_mode["smartform"]
            del payment_data_entry_mode["smartform_extended_with_logos"]
            del payment_data_entry_mode["smartform_extended_without_logos"]

        return [(c, _(l)) for c, l in payment_data_entry_mode.items()]

    def _get_default_entry_mode(self):
        module_upgrade = self.env['ir.module.module'].search([('state', '=', 'to upgrade'), ('name', '=', 'payment_lyra')])
        if module_upgrade or (constants.LYRA_PLUGIN_FEATURES.get('smartform') == False):
            return ("redirect")

        return ("smartform")

    sign_algo_help = _('Algorithm used to compute the payment form signature. Selected algorithm must be the same as one configured in the Lyra Expert Back Office.')

    if constants.LYRA_PLUGIN_FEATURES.get('shatwo') == False:
        sign_algo_help += _('The HMAC-SHA-256 algorithm should not be activated if it is not yet available in the Lyra Expert Back Office, the feature will be available soon.')

    providers = [('lyra', _('Lyra Collect - Standard payment'))]
    ondelete_policy = {'lyra': 'set default'}

    if constants.LYRA_PLUGIN_FEATURES.get('multi') == True:
        providers.append(('lyramulti', _('Lyra Collect - Payment in installments')))
        ondelete_policy['lyramulti'] = 'set default'

    code = fields.Selection(selection_add=providers, ondelete = ondelete_policy)

    lyra_doc = fields.Html(string=_('Click to view the module configuration documentation'), default=lyra_get_doc_field_value(), readonly=True)
    lyra_site_id = fields.Char(string=_('Shop ID'), help=_('The identifier provided by Lyra Collect.'), default=constants.LYRA_PARAMS.get('SITE_ID'))
    lyra_key_test = fields.Char(string=_('Key in test mode'), help=_('Key provided by Lyra Collect for test mode (available in Lyra Expert Back Office).'), default=constants.LYRA_PARAMS.get('KEY_TEST'), readonly=constants.LYRA_PLUGIN_FEATURES.get('qualif'))
    lyra_key_prod = fields.Char(string=_('Key in production mode'), help=_('Key provided by Lyra Collect (available in Lyra Expert Back Office after enabling production mode).'), default=constants.LYRA_PARAMS.get('KEY_PROD'))
    lyra_sign_algo = fields.Selection(string=_('Signature algorithm'), help=sign_algo_help, selection=[('SHA-1', 'SHA-1'), ('SHA-256', 'HMAC-SHA-256')], default=constants.LYRA_PARAMS.get('SIGN_ALGO'))
    lyra_notify_url = fields.Char(string=_('Instant Payment Notification URL'), help=_('URL to copy into your Lyra Expert Back Office > Settings > Notification rules.'), default=_get_notify_url, readonly=True)
    lyra_language = fields.Selection(string=_('Default language'), help=_('Default language on the payment page.'), default=constants.LYRA_PARAMS.get('LANGUAGE'), selection=_get_languages)
    lyra_available_languages = fields.Many2many('lyra.language', string=_('Available languages'), column1='code', column2='label', help=_('Languages available on the payment page. If you do not select any, all the supported languages will be available.'))
    lyra_capture_delay = fields.Char(string=_('Capture delay (if applicable)'), help=_('The number of days before the bank capture (adjustable in your Lyra Expert Back Office).'))
    lyra_validation_mode = fields.Selection(string=_('Validation mode (if applicable)'), help=_('If manual is selected, you will have to confirm payments manually in your Lyra Expert Back Office.'), selection=[('-1', _('Lyra Expert Back Office Configuration')), ('0', _('Automatic')), ('1', _('Manual'))])
    lyra_payment_cards = fields.Many2many('lyra.card', string=_('Card types'), column1='code', column2='label', help=_('The card type(s) that can be used for the payment. Select none to use gateway configuration.'))
    lyra_threeds_min_amount = fields.Char(string=_('Manage 3DS'), help=_('Amount below which customer could be exempt from strong authentication. Needs subscription to «Selective 3DS1» or «Frictionless 3DS2» options. For more information, refer to the module documentation.'))
    lyra_redirect_enabled = fields.Selection(string=_('Automatic redirection'), help=_('If enabled, the buyer is automatically redirected to your site at the end of the payment.'), selection=[('0', _('Disabled')), ('1', _('Enabled'))])
    lyra_redirect_success_timeout = fields.Char(string=_('Redirection timeout on success'), help=_('Time in seconds (0-300) before the buyer is automatically redirected to your website after a successful payment.'))
    lyra_redirect_success_message = fields.Char(string=_('Redirection message on success'), help=_('Message displayed on the payment page prior to redirection after a successful payment.'), default=_('Redirection to shop in a few seconds...'))
    lyra_redirect_error_timeout = fields.Char(string=_('Redirection timeout on failure'), help=_('Time in seconds (0-300) before the buyer is automatically redirected to your website after a declined payment.'))
    lyra_redirect_error_message = fields.Char(string=_('Redirection message on failure'), help=_('Message displayed on the payment page prior to redirection after a declined payment.'), default=_('Redirection to shop in a few seconds...'))
    lyra_return_mode = fields.Selection(string=_('Return mode'), help=_('Method that will be used for transmitting the payment result from the payment page to your shop.'), selection=[('GET', 'GET'), ('POST', 'POST')])
    lyra_multi_warning = fields.Boolean(compute='_lyra_compute_multi_warning')

    lyra_multi_count = fields.Char(string=_('Count'), help=_('Installments number'))
    lyra_multi_period = fields.Char(string=_('Period'), help=_('Delay (in days) between installments.'))
    lyra_multi_first = fields.Char(string=_('1st installment'), help=_('Amount of first installment, in percentage of total amount. If empty, all installments will have the same amount.'))

    lyra_test_password = fields.Char(string=_('Test password'), help=_(constants.LYRA_REST_API_KEYS_DESC))
    lyra_prod_password = fields.Char(string=_('Production password'), help=_(constants.LYRA_REST_API_KEYS_DESC))
    lyra_public_test_key = fields.Char(string=_('Public test key'), help=_(constants.LYRA_REST_API_KEYS_DESC))
    lyra_public_production_key = fields.Char(string=_('Public production key'), help=_(constants.LYRA_REST_API_KEYS_DESC))
    lyra_sha256_test_key = fields.Char(string=_('HMAC-SHA-256 test key'), help=_(constants.LYRA_REST_API_KEYS_DESC))
    lyra_sha256_prod_key = fields.Char(string=_('HMAC-SHA-256 production key'), help=_(constants.LYRA_REST_API_KEYS_DESC))
    lyra_rest_api_notify_url = fields.Char(string=_('REST API Notification URL'), help=_('URL to copy into your Lyra Expert Back Office > Settings > Notification rules.'), default=_get_notify_url, readonly=True)

    lyra_payment_data_entry_mode = fields.Selection(string=_('Payment data entry mode'), help=_('Select how the payment data will be entered. Attention, to use the Smartform, you must ensure that you have subscribed to this option with Lyra Collect.'), selection=_get_payment_data_entry_mode, default=_get_default_entry_mode, readonly=not(constants.LYRA_PLUGIN_FEATURES.get('smartform')))
    lyra_smartform_pop_in = fields.Selection(string=_('Display in a pop-in'), help=_('This option allows to display the Smartform in a pop-in.'), selection=[('no', _('No')), ('yes', _('Yes'))], default='no')
    lyra_smartform_theme = fields.Selection(string=_('Theme'), help=_('Select a theme to use to display the Smartform.'), selection=[('neon', 'Neon'), ('classic', 'Classic')], default='neon')
    lyra_smartform_compact_mode = fields.Selection(string=_('Compact mode'), help=_('This option allows to display the Smartform in a compact mode.'), selection=[('0', _('Disabled')), ('1', _('Enabled'))], default='0')
    lyra_smartform_payment_attempts = fields.Char(string=_('Payment attempts number for cards'), help=_('Maximum number of payment by cards retries after a failed payment (between 0 and 2). If blank, the gateway default value is 2.'))

    environment = fields.Char()
    lyra_redirect = False

    @api.model
    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        """ Override of payment to unlist Lyra Collect providers when the currency is not supported. """
        providers = super()._get_compatible_providers(*args, currency_id=currency_id, **kwargs)

        currency = self.env['res.currency'].browse(currency_id).exists()
        if currency and currency.name and tools.find_currency(currency.name) is None:
            providers = providers.filtered(
                lambda p: p.code not in ['lyra', 'lyramulti']
            )

        return providers

    @api.model
    def multi_add(self, filename, noupdate):
        if constants.LYRA_PLUGIN_FEATURES.get('multi') == True:
            module_upgrade = self.env['ir.module.module'].search([('state', '=', 'to upgrade'), ('name', '=', 'payment_lyra')])
            file = path.join(path.dirname(path.dirname(path.abspath(__file__)))) + filename
            mode = 'update' if module_upgrade else 'init'
            convert_xml_import(self._cr, 'payment_lyra', file, None, mode, noupdate)

    def _get_ctx_mode(self):
        ctx_value = 'TEST' if self.state == 'test' else 'PRODUCTION'

        return ctx_value

    def _lyra_generate_sign(self, provider, values):
        key = self.lyra_key_prod if self._get_ctx_mode() == 'PRODUCTION' else self.lyra_key_test

        sign = ''
        for k in sorted(values.keys()):
            if k.startswith('vads_'):
                sign += values[k] + '+'

        sign += key

        if self.lyra_sign_algo == 'SHA-1':
            shasign = sha1(sign.encode('utf-8')).hexdigest()
        else:
            shasign = base64.b64encode(hmac.new(key.encode('utf-8'), sign.encode('utf-8'), sha256).digest()).decode('utf-8')

        return shasign

    def _get_payment_config(self, amount):
        if self.code == 'lyramulti':
            if self.lyra_multi_first:
                first = int(float(self.lyra_multi_first) / 100 * int(amount))
            else:
                first = int(float(amount) / float(self.lyra_multi_count))

            payment_config = u'MULTI:first=' + str(first) + u';count=' + self.lyra_multi_count + u';period=' + self.lyra_multi_period
        else:
            payment_config = u'SINGLE'

        return payment_config

    def lyra_form_generate_values(self, values):
        base_url = request.httprequest.host_url

        # trans_id is the number of 1/10 seconds from midnight.
        now = datetime.now()
        midnight = now.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        delta = int((now - midnight).total_seconds() * 10)
        trans_id = str(delta).rjust(6, '0')

        threeds_mpi = u''
        if self.lyra_threeds_min_amount and float(self.lyra_threeds_min_amount) > values['amount']:
            threeds_mpi = u'2'

        # Check currency.
        if 'currency' in values:
            currency = values['currency']
        else:
            currency = self.env['res.currency'].browse(values['currency_id']).exists()

        currency_num = tools.find_currency(currency.name)
        if currency_num is None:
            _logger.error('The plugin cannot find a numeric code for the current shop currency {}.'.format(currency.name))
            raise ValidationError(_('The shop currency {} is not supported.').format(currency.name))

        # Amount in cents.
        k = int(currency.decimal_places)
        amount = int(float_round(float_round(values['amount'], k) * (10 ** k), 0))

        # List of available languages.
        available_languages = ''
        for value in self.lyra_available_languages:
            available_languages += value.code + ';'

        # List of available payment cards.
        payment_cards = ''
        for value in self.lyra_payment_cards:
            payment_cards += value.code + ';'

        # Validation mode.
        validation_mode = self.lyra_validation_mode if self.lyra_validation_mode != '-1' else ''

        # Enable redirection?
        ProviderLyra.lyra_redirect = True if str(self.lyra_redirect_enabled) == '1' else False

        order_id = re.sub("[^0-9a-zA-Z_-]+", "", values.get('reference'))

        tx_values = dict() # Values to sign in unicode.
        tx_values.update({
            'vads_site_id': self.lyra_site_id,
            'vads_amount': str(amount),
            'vads_currency': currency_num,
            'vads_trans_date': str(datetime.utcnow().strftime("%Y%m%d%H%M%S")),
            'vads_trans_id': str(trans_id),
            'vads_ctx_mode': str(self._get_ctx_mode()),
            'vads_page_action': u'PAYMENT',
            'vads_action_mode': u'INTERACTIVE',
            'vads_payment_config': self._get_payment_config(amount),
            'vads_version': constants.LYRA_PARAMS.get('GATEWAY_VERSION'),
            'vads_url_return': urlparse.urljoin(base_url, LyraController._return_url),
            'vads_order_id': str(order_id),
            'vads_ext_info_order_ref': str(values.get('reference')),
            'vads_contrib': tools._lyra_get_contrib(),

            'vads_language': self.lyra_language or '',
            'vads_available_languages': available_languages,
            'vads_capture_delay': self.lyra_capture_delay or '',
            'vads_validation_mode': validation_mode,
            'vads_payment_cards': payment_cards,
            'vads_return_mode': str(self.lyra_return_mode),
            'vads_threeds_mpi': threeds_mpi
        })

        if ProviderLyra.lyra_redirect:
            tx_values.update({
                'vads_redirect_success_timeout': self.lyra_redirect_success_timeout or '',
                'vads_redirect_success_message': self.lyra_redirect_success_message or '',
                'vads_redirect_error_timeout': self.lyra_redirect_error_timeout or '',
                'vads_redirect_error_message': self.lyra_redirect_error_message or ''
            })

        lyra_tx_values = dict() # Values encoded in UTF-8.

        for key in tx_values.keys():
            if tx_values[key] == ' ':
                tx_values[key] = ''

            lyra_tx_values[key] = tx_values[key].encode('utf-8')
        return lyra_tx_values

    def _get_default_payment_method_id(self, code):
        self.ensure_one()
        if self.code != 'lyra' and self.code != 'lyramulti':
            return super()._get_default_payment_method_id(self, code)

        if self.code == 'lyra':
            return self.env.ref('payment_lyra.payment_method_lyra').id
        if self.code == 'lyramulti':
            return self.env.ref('payment_lyra.payment_method_lyramulti').id

    def _lyra_get_rest_password(self):
        if self.state == 'test':
            return str(self.lyra_test_password)

        return str(self.lyra_prod_password)

    def _lyra_get_rest_public_key(self):
        if self.state == 'test':
            return str(self.lyra_public_test_key)

        return str(self.lyra_public_production_key)

    def _lyra_get_rest_sha256_key(self):
        if self.state == 'test':
            return str(self.lyra_sha256_test_key)

        return str(self.lyra_sha256_prod_key)

    def _lyra_get_javascript_server_url(self):
        return constants.LYRA_PARAMS.get('STATIC_URL') + "js/krypton-client/V4.0/stable/kr-payment-form.min.js"

    def _lyra_get_smartform_stylesheet_url(self):
        return constants.LYRA_PARAMS.get('STATIC_URL') + "js/krypton-client/V4.0/ext/" + self.lyra_smartform_theme + "-reset.css"

    def _lyra_get_smartform_stylesheet_script_url(self):
        return constants.LYRA_PARAMS.get('STATIC_URL') + "js/krypton-client/V4.0/ext/" + self.lyra_smartform_theme + ".js"

    def _lyra_get_return_url(self):
        return urlparse.urljoin(self.env['ir.config_parameter'].get_param('web.base.url'), LyraController._return_url)

    def _lyra_get_smartform_language(self):
        return get_lang(self.env).code[:2]

    def _lyra_get_smartform_payment_means(self):
        cards = []
        for value in self.lyra_payment_cards:
            cards.append(value.code)

        return cards

    def _lyra_get_currency(self, currency_id):
        # Give the iso and the number of decimal toward the smallest monetary unit from the id of the currency.
        currency_number = tools.find_currency(self.env['res.currency'].browse(currency_id).exists().name)
        for currency in constants.LYRA_CURRENCIES:
            if currency[1] == str(currency_number):
                return (currency[0], currency[2])

        raise ValidationError(_('The shop currency {} is not supported.').format(currency.name))

    def _should_build_inline_form(self, is_validation=True):
        if (self.code == 'lyramulti'):
            return False

        if (self.code == 'lyra'):
            if (constants.LYRA_PLUGIN_FEATURES.get('smartform') == True and not str(self.lyra_payment_data_entry_mode) == 'redirect'):
                return True

            return False

        return super()._should_build_inline_form(is_validation=True)
