# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

from odoo import _

LYRA_PLUGIN_FEATURES = {
    'multi' : True,
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
    'PLUGIN_VERSION': '1.2.0',
    'CMS_IDENTIFIER': 'Odoo_10-12',
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
    'E-CARTEBLEUE': u'E-CARTEBLEUE',
    'MAESTRO': u'Maestro',
    'MASTERCARD': u'Mastercard',
    'VISA': u'Visa',
    'VISA_ELECTRON': u'Visa Electron',
    'VPAY': u'V PAY',
    'AMEX': u'American Express',
    'CONECS': u'Titre-Restaurant Dématérialisé Conecs',
    'APETIZ': u'Titre-Restaurant Dématérialisé Apetiz',
    'CHQ_DEJ': u'Titre-Restaurant Dématérialisé Chèque Déjeuner',
    'KLARNA': u'Klarna Internet Banking',
    'SODEXO': u'Titre-Restaurant Dématérialisé Sodexo',
    'EDENRED': u'Ticket Restaurant',
    'PAYPAL': u'PayPal',
    'PAYPAL_SB': u'PayPal - Sandbox',
    'ALIPAY': u'Alipay',
    'BANCONTACT': u'Bancontact Mistercash',
    'GIROPAY': u'Giropay',
    'IDEAL': u'iDEAL',
    'MULTIBANCO': u'Multibanco',
    'MYBANK': u'MyBank',
    'ONEY': u'FacilyPay Oney',
    'ONEY_SANDBOX': u'FacilyPay Oney - Sandbox',
    'PRZELEWY24': u'Przelewy24',
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
