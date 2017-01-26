# -*- coding: utf-'8' "-*-"
from hashlib import sha1
import logging
import urlparse


from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_payzen.controllers.main import PayzenController
from odoo import models, api, fields, _
from odoo.tools import float_round, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_compare, float_repr
from datetime import datetime


_logger = logging.getLogger(__name__)

currency_code = {
    'EUR': 978,
    'USD': 840,
    'CAD': 124,
    'XPF': 953,
}


class AcquirerPayzen(models.Model):
    _inherit = 'payment.acquirer'

    def _get_payzen_urls(self, environment):
        if environment == 'prod':
            return {
                'payzen_form_url': 'https://demo.payzen.eu/vads-payment/',
            }
        else:
            return {
                'payzen_form_url': 'https://demo.payzen.eu/vads-payment/',
            }

    provider = fields.Selection(selection_add=[('payzen', 'Payzen')])
    payzen_websitekey = fields.Char(string='Website ID',
                                    required_if_provider='payzen')
    payzen_secretkey = fields.Char(string='SecretKey',
                                   required_if_provider='payzen')

    def _payzen_generate_digital_sign(self, acquirer, vads_values):
        signature = ''
        for key in sorted(vads_values.iterkeys()):
            if key.startswith('vads_'):
                signature += str(vads_values[key]).decode('utf-8') + '+'

        signature += self.payzen_secretkey
        shasign = sha1(signature.encode('utf-8')).hexdigest()

        return shasign

    @api.multi
    def payzen_form_generate_values(self, values):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')

        self.env.cr.execute("select MAX(id) FROM sale_order")
        x = self.env.cr.fetchall()
        trans_id = str(x[0][0]).rjust(6, '0')

        if self.environment == 'test':
            mode = 'TEST'
        elif self.environment == 'prod':
            mode = 'PRODUCTION'

        payzen_tx_values = dict(values)
        payzen_tx_values.update({
            'vads_site_id': self.payzen_websitekey,
            'vads_amount': int(values['amount'] * 100) and values['currency'].decimal_places == 2 or int(values['amount']),
            'vads_currency': currency_code.get(
                values['currency'].name, 0),
            'vads_trans_date': datetime.utcnow().strftime(
                "%Y%m%d%H%M%S"),
            'vads_trans_id': trans_id,
            'vads_ctx_mode': mode,
            'vads_page_action': 'PAYMENT',
            'vads_action_mode': 'INTERACTIVE',
            'vads_payment_config': 'SINGLE',
            'vads_version': 'V2',
            'vads_url_return': urlparse.urljoin(
                base_url, PayzenController._return_url),
            'vads_return_mode': 'GET',
            'vads_order_id': values.get('reference'),
            # customer info
            'vads_cust_name': values.get('partner_name') and values.get('partner_name')[0:126].encode('utf-8') or '',
            'vads_cust_first_name': values.get('partner_first_name') and values.get('partner_first_name')[0:62].encode('utf-8') or '',
            'vads_cust_last_name': values.get('partner_last_name') and values.get('partner_last_name')[0:62].encode('utf-8') or '',
            'vads_cust_address': values.get('partner_address') and values.get('partner_address')[0:254].encode('utf-8'),
            'vads_cust_zip': values.get('partner_zip') and values.get('partner_zip')[0:62].encode('utf-8') or '',
            'vads_cust_city': values.get('partner_city') and values.get('partner_city')[0:62].encode('utf-8') or '',
            'vads_cust_state': values.get('partner_state') and values.get('partner_state').name[0:62].encode('utf-8') or '',
            'vads_cust_country': values.get('partner_country').code and values.get('partner_country').code.upper() or '',
            'vads_cust_email': values.get('partner_email') and values.get('partner_email')[0:126].encode('utf-8') or '',
            'vads_cust_phone': values.get('partner_phone') and values.get('partner_phone')[0:31].encode('utf-8') or '',
        })

        payzen_tx_values['payzen_signature'] = self._payzen_generate_digital_sign(self, payzen_tx_values)
        return payzen_tx_values

    @api.multi
    def payzen_get_form_action_url(self):
        return self._get_payzen_urls(self.environment)['payzen_form_url']


_AUTH_RESULT = {
    "00": u"transaction approuvée ou traitée avec succès",
    "02": u"contacter l’émetteur de carte",
    "03": u"accepteur invalide",
    "04": u"conserver la carte",
    "05": u"ne pas honorer",
    "07": u"conserver la carte, conditions spéciales",
    "08": u"approuver après identification",
    "12": u"transaction invalide",
    "13": u"montant invalide",
    "14": u"numéro de porteur invalide",
    "15": u"Emetteur de carte inconnu",
    "17": u"Annulation client",
    "19": u"Répéter la transaction ultérieurement",
    "20": u"Réponse erronée (erreur dans le domaine serveur)",
    "24": u"Mise à jour de fichier non supportée",
    "25": u"Impossible de localiser l’enregistrement dans le fichier",
    "26": u"Enregistrement dupliqué, ancien enregistrement remplacé",
    "27": u"Erreur en « edit » sur champ de lise à jour fichier",
    "28": u"Accès interdit au fichier",
    "29": u"Mise à jour impossible",
    "30": u"erreur de format",
    "31": u"identifiant de l’organisme acquéreur inconnu",
    "33": u"date de validité de la carte dépassée",
    "34": u"suspicion de fraude",
    "38": u"Date de validité de la carte dépassée",
    "41": u"carte perdue",
    "43": u"carte volée",
    "51": u"provision insuffisante ou crédit dépassé",
    "54": u"date de validité de la carte dépassée",
    "55": u"Code confidentiel erroné",
    "56": u"carte absente du fichier",
    "57": u"transaction non permise à ce porteur",
    "58": u"transaction interdite au terminal",
    "59": u"suspicion de fraude",
    "60": u"l’accepteur de carte doit contacter l’acquéreur",
    "61": u"montant de retrait hors limite",
    "63": u"règles de sécurité non respectées",
    "68": u"réponse non parvenue ou reçue trop tard",
    "75": u"Nombre d’essais code confidentiel dépassé",
    "76": u"Porteur déjà en opposition, ancien enregistrement conservé",
    "90": u"arrêt momentané du système",
    "91": u"émetteur de cartes inaccessible",
    "94": u"transaction dupliquée",
    "96": u"mauvais fonctionnement du système",
    "97": u"échéance de la temporisation de surveillance globale",
    "98": u"serveur indisponible routage réseau demandé à nouveau",
    "99": u"incident domaine initiateur",
}


class TxPayzen(models.Model):
    _inherit = 'payment.transaction'

    state_message = fields.Text(string='Transaction log')
    authresult_message = fields.Char(string='Transaction error')

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _payzen_form_get_tx_from_data(self, data):

        shasign, result, reference = data.get('signature'), data.get('vads_result'), data.get('vads_order_id')
        if not reference or not shasign or not result:
            error_msg = 'Payzen : received bad data %s' % (data)
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = 'Payzen: received data for reference %s' % (reference)
            if not tx:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        # verify shasign
        shasign_check = tx.acquirer_id._payzen_generate_digital_sign('out', data)
        if shasign_check.upper() != shasign.upper():
            error_msg = _('Payzen: invalid shasign, received %s, computed %s, for data %s') % (shasign, shasign_check, data)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _payzen_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        # check what is bought
        if float_compare(float(data.get('amount', '0.0')), self.amount, 2) != 0:
            invalid_parameters.append(('amount', data.get('amount'), '%.2f' % self.amount))

        if data.get('currency') != self.currency_id.name:
            invalid_parameters.append(('currency', data.get('currency'), self.currency_id.name))

        return invalid_parameters

    def _payzen_form_validate(self, data):
        payzen_status = {'valide': ['00'],
                         'cancel': ['17', ''],
                         }
        status_code = data.get('vads_auth_result')
        if status_code in payzen_status['valide']:
            self.write({
                'state': 'done',
                'state_message': '%s' % (data),
            })
            return True
        elif status_code in payzen_status['cancel']:
            self.write({
                'state': 'cancel',
                'state_message': '%s' % (data),
            })
            return True
        else:
            authresult_message = ''
            if status_code in _AUTH_RESULT:
                authresult_message = _AUTH_RESULT[status_code]
            error = 'Payzen error'
            _logger.info(error)
            self.write({
                'state': 'error',
                'state_message': '%s' % (data),
                'authresult_message': authresult_message,
            })
            return False
