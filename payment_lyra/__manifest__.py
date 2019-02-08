# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra-network.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

{
    'name': 'Lyra Payment Acquirer',
    'version': '1.0.0',
    'summary': 'Payment Acquirer: Lyra Implementation',
    'category': 'Payment Acquirer',
    'author': 'Lyra Network',
    'website': 'https://www.lyra-network.com/',
    'license': 'AGPL-3',
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_lyra_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
}
