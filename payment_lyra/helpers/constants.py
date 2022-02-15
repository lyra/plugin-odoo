# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

from odoo import _

# WARN: Do not modify code format here. This is managed by build files.
LYRA_PLUGIN_FEATURES = {
    'multi': True,
    'restrictmulti': False,
    'qualif': False,
    'shatwo': True,
}

LYRA_PARAMS = {
    'GATEWAY_CODE': 'Lyra',
    'GATEWAY_NAME': 'Lyra Collect',
    'BACKOFFICE_NAME': 'Lyra Expert',
    'SUPPORT_EMAIL': 'support-ecommerce@lyra-collect.com',
    'GATEWAY_URL': 'https://secure.lyra.com/vads-payment/',
    'SITE_ID': '12345678',
    'KEY_TEST': '1111111111111111',
    'KEY_PROD': '2222222222222222',
    'CTX_MODE': 'TEST',
    'SIGN_ALGO': 'SHA-256',
    'LANGUAGE': 'en',

    'GATEWAY_VERSION': 'V2',
    'PLUGIN_VERSION': '1.2.3',
    'CMS_IDENTIFIER': 'Odoo_10-14',
}

LYRA_LANGUAGES = {
    'cn': 'Chinese',
    'de': 'German',
    'es': 'Spanish',
    'en': 'English',
    'fr': 'French',
    'it': 'Italian',
    'jp': 'Japanese',
    'nl': 'Dutch',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'sv': 'Swedish',
    'tr': 'Turkish',
}

LYRA_CARDS = {
    'CB': u'CB',
    'E-CARTEBLEUE': u'e-Carte Bleue',
    'MAESTRO': u'Maestro',
    'MASTERCARD': u'Mastercard',
    'VISA': u'Visa',
    'VISA_ELECTRON': u'Visa Electron',
    'VPAY': u'V PAY',
    'AMEX': u'American Express',
    'ALIPAY': u'Alipay',
    'APETIZ': u'Apetiz',
    'AURORE-MULTI': u'Cpay Aurore',
    'BANCONTACT': u'Bancontact Mistercash',
    'CDGP': u'Carte Privilège',
    'CHQ_DEJ': u'Chèque Déjeuner',
    'CONECS': u'Conecs',
    'DINERS': u'Diners',
    'DISCOVER': u'Discover',
    'EDENRED': u'Ticket Restaurant',
    'EDENRED_EC': u'Ticket EcoCheque',
    'EDENRED_SC': u'Ticket Sport & Culture',
    'EDENRED_TC': u'Ticket Compliments',
    'EDENRED_TR': u'Ticket Restaurant',
    'E_CV': u'e-Chèque-Vacances',
    'FULLCB3X': u'Paiement en 3 fois CB',
    'FULLCB4X': u'Paiement en 4 fois CB',
    'GIROPAY': u'Giropay',
    'GOOGLEPAY': u'Google Pay',
    'IDEAL': u'iDEAL',
    'ILLICADO': u'Carte Illicado',
    'ILLICADO_SB': u'Carte Illicado (sandbox)',
    'JCB': u'JCB',
    'KLARNA': u'Klarna',
    'MULTIBANCO': u'Multibanco',
    'MYBANK': u'MyBank',
    'ONEY_3X_4X': u'Paiement en 3 ou 4 fois Oney',
    'ONEY_ENSEIGNE': u'Cartes enseignes Oney',
    'PAYLIB': u'Paylib',
    'PAYPAL': u'PayPal',
    'PAYPAL_SB': u'PayPal Sandbox',
    'POSTFINANCE': u'PostFinance Card',
    'POSTFINANCE_EFIN': u'PostFinance E-Finance',
    'PRZELEWY24': u'Przelewy24',
    'SDD': u'SEPA direct debit',
    'SODEXO': u'Pass Restaurant',
    'SOFORT_BANKING': u'Sofort',
    'UNION_PAY': u'UnionPay',
    'WECHAT': u'WeChat Pay',
}

LYRA_CURRENCIES = [
    ['EUR', '978', 2],
    ['GBP', '826', 2],
    ['CAD', '124', 2],
    ['JPY', '392', 0],
    ['DKK', '208', 2],
    ['PLN', '985', 2],
    ['USD', '840', 2],
    ['CHF', '756', 2],
    ['NOK', '578', 2],
]
