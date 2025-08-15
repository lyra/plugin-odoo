# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

{
    'name': 'Lyra Collect Payment Provider',
    'version': '4.2.0',
    'summary': 'Accept payments with Lyra Collect secure payment gateway.',
    'category': 'Accounting/Payment Providers',
    'author': 'Lyra Network',
    'website': 'https://www.lyra.com/',
    'license': 'AGPL-3',
    'depends': ['payment','sale'],
    'data': [
        'views/payment_provider_views.xml',
        'views/payment_lyra_templates.xml',
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_lyra/static/src/**/*'
        ]
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'images': ['static/description/icon.png'],
    'application': True,
    'installable': True
}
