# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

from odoo import models, fields, api
from .helpers import constants

class LyraCard(models.Model):
    _name = "lyra.card"
    _description = "Lyra payment card"
    _rec_name = "label"

    code = fields.Char()
    label = fields.Char(translate=True)

    @api.model_cr
    def init(self):
        cards = constants.LYRA_CARDS

        for key in cards.keys():
            value = {"code": key, "label": cards[key]}
            self.create(value)