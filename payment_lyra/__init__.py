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

from .helpers import constants
from odoo.addons.payment import setup_provider, reset_payment_provider

def post_init_hook(env):
    setup_provider(env, 'lyra')

    if constants.LYRA_PLUGIN_FEATURES.get('multi') == True:
        setup_provider(env, 'lyramulti')

def uninstall_hook(env):
    reset_payment_provider(env, 'lyra')

    if constants.LYRA_PLUGIN_FEATURES.get('multi') == True:
        reset_payment_provider(env, 'lyramulti')