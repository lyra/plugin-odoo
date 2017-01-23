# -*- coding: utf-'8' "-*-"
from hashlib import sha1
import logging
import urlparse


from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_payzen.controllers.main import PayzenController
from odoo import models, api, fields, exceptions
from odoo.tools.float_utils import float_compare
from datetime import datetime


_logger = logging.getLogger(__name__)

currency_code = {
    'EUR': 978,
    'USD': 840,
    'CAD': 124,
}


class AcquirerPayzen(models.Model):
    _inherit = 'payment.acquirer'

    def _get_payzen_urls(self, environment, context=None):
        if environment == 'prod':
            return {
                'payzen_form_url': 'https://secure.payzen.eu/vads-payment/',
            }
        else:
            return {
                'payzen_form_url': 'https://secure.payzen.eu/vads-payment/',
            }

    provider = fields.Selection(selection_add=[('payzen', 'Payzen')])
    payzen_websitekey = fields.Char(string='Website ID',
                                    required_if_provider='payzen')
    payzen_secretkey = fields.Char(string='SecretKey',
                                   required_if_provider='payzen')

    def _payzen_generate_digital_sign(self, acquirer, vads_values):
        signature = ''
        for key in sorted(vads_values.iterkeys()):
            if key.find('payzen_vads_') == 0:
                signature += str(vads_values[key]).decode('utf-8') + '+'
        signature += acquirer.payzen_secretkey
        shasign = sha1(signature.encode('utf-8')).hexdigest()
        return shasign

    def payzen_form_generate_values(self, id,
                                    partner_values, tx_values, context=None):
        base_url = self.pool['ir.config_parameter'].get_param('web.base.url')
        acquirer = self.browse(id, context=context)

        cr.execute("select MAX(id) FROM sale_order")
        x = cr.fetchall()
        trans_id = str(x[0][0]).rjust(6, '0')

        if acquirer.environment == 'test':
            mode = 'TEST'
        elif acquirer.environment == 'prod':
            mode = 'PRODUCTION'
        payzen_tx_values = dict(tx_values)
        payzen_tx_values.update({
            'payzen_vads_site_id': acquirer.payzen_websitekey,
            'payzen_vads_amount': int(tx_values['amount'] * 100),
            'payzen_vads_currency': currency_code.get(
                tx_values['currency'].name, 0),
            'payzen_vads_trans_date': datetime.utcnow().strftime(
                "%Y%m%d%H%M%S"),
            'payzen_vads_trans_id': trans_id,
            'payzen_vads_ctx_mode': mode,
            'payzen_vads_page_action': 'PAYMENT',
            'payzen_vads_action_mode': 'INTERACTIVE',
            'payzen_vads_payment_config': 'SINGLE',
            'payzen_vads_version': 'V2',
            'payzen_vads_url_return': urlparse.urljoin(
                base_url, PayzenController._return_url),
            'payzen_vads_return_mode': 'GET',
            'payzen_vads_order_id': tx_values.get('reference'),
            # customer info
            'payzen_vads_cust_name': partner_values['name'] and partner_values['name'][0:126].encode('utf-8') or '',
            'payzen_vads_cust_first_name': partner_values['first_name'] and partner_values['first_name'][0:62].encode('utf-8') or '',
            'payzen_vads_cust_last_name': partner_values['last_name'] and partner_values['last_name'][0:62].encode('utf-8') or '',
            'payzen_vads_cust_address': partner_values['address'] and partner_values['address'][0:254].encode('utf-8'),
            'payzen_vads_cust_zip': partner_values['zip'] and partner_values['zip'][0:62].encode('utf-8') or '',
            'payzen_vads_cust_city': partner_values['city'] and partner_values['city'][0:62].encode('utf-8') or '',
            'payzen_vads_cust_state': partner_values['state'] and partner_values['state'].name[0:62].encode('utf-8') or '',
            'payzen_vads_cust_country': partner_values['country'].code and partner_values['country'].code.upper() or '',
            'payzen_vads_cust_email': partner_values['email'] and partner_values['email'][0:126].encode('utf-8') or '',
            'payzen_vads_cust_phone': partner_values['phone'] and partner_values['phone'][0:31].encode('utf-8') or '',
        })

        payzen_tx_values['payzen_signature'] = self._payzen_generate_digital_sign(acquirer, payzen_tx_values)
        return partner_values, payzen_tx_values

    def payzen_get_form_action_url(self, id, context=None):
        acquirer = self.browse(id, context=context)
        return self._get_payzen_urls(acquirer.environment, context=context)['payzen_form_url']


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
    def _payzen_form_get_tx_from_data(self, data, context=None):

        signature, result, reference = data.get('signature'), data.get('vads_result'), data.get('vads_order_id')
        if not reference or not signature or not result:
            error_msg = 'Payzen : received bad data %s' % (data)
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        tx_ids = self.search([('reference', '=', reference)], context=context)
        if not tx_ids or len(tx_ids) > 1:
            error_msg = 'Payzen: received data for reference %s' % (reference)
            if not tx_ids:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        tx = self.pool['payment.transaction'].browse(tx_ids[0], context=context)

        shasign_check = self.pool['payment.acquirer']._payzen_generate_digital_sign(tx.acquirer_id, data)
        """if shasign_check != signature.upper :
            error_msg = 'Payzen : invalid shasign, received %s, computed %s, for data %s' % (signature, shasign_check, data)
            _logger.error(error_msg)
            raise ValidationError(error_msg)"""

        return tx

    def _payzen_form_get_invalid_parameters(self, tx, data, context=None):
        invalid_parameters = []

        return invalid_parameters

    def _payzen_form_validate(self, tx, data, context=None):
        payzen_status = {'valide': ['00'],
                         'cancel': ['17', ''],
                         }
        status_code = data.get('vads_auth_result')
        if status_code in payzen_status['valide']:
            tx.write({
                'state': 'done',
                'state_message': '%s' % (data),
            })
            return True
        elif status_code in payzen_status['cancel']:
            tx.write({
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
            tx.write({
                'state': 'error',
                'state_message': '%s' % (data),
                'authresult_message': authresult_message,
            })
            return False
