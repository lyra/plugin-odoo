# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

from . import controllers
from . import models

try:
    from odoo.addons.payment import reset_payment_acquirer
except Exception:
    pass


def uninstall_hook(cr, registry):
    if reset_payment_acquirer:
        reset_payment_acquirer(cr, registry, "lyra")
