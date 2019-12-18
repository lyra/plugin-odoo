# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

from odoo import models, fields
from ..helpers import constants

class LyraCard(models.Model):
    _name = 'lyra.card'
    _description = 'Lyra Collect payment card'
    _rec_name = 'label'
    _order = 'label'

    code = fields.Char()
    label = fields.Char()

    def init(self):
        cards = constants.LYRA_CARDS

        for c, l in cards.items():
            card = self.search([('code', '=', c)])

            if not card:
                self.create({'code': c, 'label': l})
