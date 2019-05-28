# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

from .constants import LYRAGW_CURRENCIES

def find_currency(iso):
    for currency in LYRAGW_CURRENCIES:
        if (currency[0] == iso):
            return currency[1];

    return NUL
