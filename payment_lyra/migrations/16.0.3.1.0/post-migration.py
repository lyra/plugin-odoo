# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

from odoo.http import request
from odoo.addons.payment_lyra.helpers import constants

def migrate(cr, version):
    if constants.LYRA_PLUGIN_FEATURES.get('smartform') == True:
        cr.execute("""
            UPDATE payment_provider
            SET inline_form_view_id = (SELECT id
            FROM ir_ui_view
            WHERE name = 'lyra_inline_smartform')
            WHERE code = 'lyra';
        """)