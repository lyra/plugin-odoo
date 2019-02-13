# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra-network.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

from odoo import models, fields

class LyraLanguage(models.Model):
    _name = "lyra.language"
    _description = "Lyra language"
    _rec_name = "label"

    code = fields.Char()
    label = fields.Char(translate=True)