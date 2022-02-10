# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

from odoo import _

from .constants import LYRA_CURRENCIES

def find_currency(iso):
    for currency in LYRA_CURRENCIES:
        if currency[0] == iso:
            return currency[1]

    return None

def lang_translate(callback, v):
    return _(v)
