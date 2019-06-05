# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

from odoo import models, fields, api
from ..helpers import constants

class LyragwCard(models.Model):
    _name = 'lyragw.card'
    _description = 'Lyra payment card'
    _rec_name = 'label'
    _order = 'label'

    code = fields.Char()
    label = fields.Char()

    @api.model_cr
    def init(self):
        cards = constants.LYRAGW_CARDS

        for c, l in cards.items():
            card = self.search([('code', '=', c)])

            if not card:
                self.create({'code': c, 'label': l})
