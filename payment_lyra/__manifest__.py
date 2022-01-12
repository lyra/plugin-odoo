# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

{
    "name": "Lyra Collect Payment Acquirer",
    "version": "2.0.0",
    "summary": "Accept payments with Lyra Collect secure payment gateway.",
    "category": "Accounting",
    "author": "Lyra Network",
    "website": "https://www.lyra.com/",
    "license": "AGPL-3",
    "depends": ["payment"],
    "data": [
        "views/payment_views.xml",
        "views/payment_lyra_templates.xml",
        "data/payment_acquirer_data.xml",
        # TODO: Manage lyramulti
        # 'data/payment_acquirer_data_multi.xml',
        "security/ir.model.access.csv",
    ],
    "images": ["static/description/icon.png"],
    "installable": True,
    "uninstall_hook": "uninstall_hook",
}
