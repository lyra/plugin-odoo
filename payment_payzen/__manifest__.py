# coding: utf-8
#
# This file is part of PayZen Payment Module for Odoo.
# Copyright Lyra Network. All rights reserved.
# See COPYING.txt for license details.

{
    'name': 'PayZen Payment Acquirer',
    'version': '1.0.0',
    'summary': 'Payment Acquirer: PayZen Implementation',
    'category': 'Payment Acquirer',
    'author': 'Lyra Network',
    'website': 'https://www.lyra-network.com/',
    'license': 'AGPL-3',
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_payzen_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
}
