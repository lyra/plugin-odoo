# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

{
    'name': 'Lyra Payment Acquirer',
    'version': '1.1.0-beta1',
    'summary': 'Accept payments with Lyra secure payment gateway.',
    'category': 'Accounting',
    'author': 'Lyra Network',
    'website': 'https://www.lyra.com/',
    'license': 'AGPL-3',
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_lyragw_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
}
