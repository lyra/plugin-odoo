# -*- coding: utf-'8' "-*-"

from hashlib import sha1
import logging
import urlparse
import math

from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_payzen.controllers.main import PayzenController
from odoo import models, api, release, fields, _
from odoo.tools import float_round, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_compare, float_repr
from datetime import datetime

_logger = logging.getLogger(__name__)

payzen_currencies = {
    'EUR': 978,
    'USD': 840,
    'CAD': 124,
    'XPF': 953,
}


class AcquirerPayzen(models.Model):
    _inherit = 'payment.acquirer'

    def _get_payzen_urls(self, environment):
        return {
           'payzen_form_url': 'https://secure.payzen.eu/vads-payment/', #'https://demo.payzen.eu/vads-payment/',
        }

    provider = fields.Selection(selection_add=[('payzen', 'PayZen')])
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

        """
        # such trans_id generation does not allow
        self.env.cr.execute("select MAX(id) FROM sale_order")
        x = self.env.cr.fetchall()
        trans_id = str(x[0][0]).rjust(6, '0')
        """
        
        # trans id is number of 1/10 seconds from midnight
        now = datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        delta = int((now - midnight).total_seconds() * 10)
        trans_id = str(delta).rjust(6, '0')

        if self.environment == 'test':
            mode = 'TEST'
        elif self.environment == 'prod':
            mode = 'PRODUCTION'

        payzen_tx_values = dict(values)
        payzen_tx_values.update({
            'vads_site_id': self.payzen_websitekey,
            'vads_amount': int(values['amount'] * math.pow(10, int(values['currency'].decimal_places))),
            'vads_currency': payzen_currencies.get(values['currency'].name, 0),
            'vads_trans_date': datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            'vads_trans_id': trans_id,
            'vads_ctx_mode': mode,
            'vads_page_action': 'PAYMENT',
            'vads_action_mode': 'INTERACTIVE',
            'vads_payment_config': 'SINGLE',
            'vads_version': 'V2',
            'vads_url_return': urlparse.urljoin(base_url, PayzenController._return_url),
            'vads_return_mode': 'GET',
            'vads_order_id': values.get('reference'),
            'vads_contrib': 'Odoo10_0.9.1/' + release.version,
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
    "00": u"Transaction approuvée ou traitée avec succès",
    "02": u"Contacter l’émetteur de carte",
    "03": u"Accepteur invalide",
    "04": u"Conserver la carte",
    "05": u"Ne pas honorer",
    "07": u"Conserver la carte, conditions spéciales",
    "08": u"Approuver après identification",
    "12": u"Transaction invalide",
    "13": u"Montant invalide",
    "14": u"Numéro de porteur invalide",
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
    "30": u"Erreur de format",
    "31": u"Identifiant de l’organisme acquéreur inconnu",
    "33": u"Date de validité de la carte dépassée",
    "34": u"Suspicion de fraude",
    "38": u"Date de validité de la carte dépassée",
    "41": u"Carte perdue",
    "43": u"Carte volée",
    "51": u"Provision insuffisante ou crédit dépassé",
    "54": u"Date de validité de la carte dépassée",
    "55": u"Code confidentiel erroné",
    "56": u"Carte absente du fichier",
    "57": u"Transaction non permise à ce porteur",
    "58": u"Transaction interdite au terminal",
    "59": u"Suspicion de fraude",
    "60": u"L’accepteur de carte doit contacter l’acquéreur",
    "61": u"Montant de retrait hors limite",
    "63": u"Règles de sécurité non respectées",
    "68": u"Réponse non parvenue ou reçue trop tard",
    "75": u"Nombre d’essais code confidentiel dépassé",
    "76": u"Porteur déjà en opposition, ancien enregistrement conservé",
    "90": u"Arrêt momentané du système",
    "91": u"Emetteur de cartes inaccessible",
    "94": u"Transaction dupliquée",
    "96": u"Mauvais fonctionnement du système",
    "97": u"Echéance de la temporisation de surveillance globale",
    "98": u"Serveur indisponible routage réseau demandé à nouveau",
    "99": u"Incident domaine initiateur",
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

        shasign, status, reference = data.get('signature'), data.get('vads_trans_status'), data.get('vads_order_id')
        if not reference or not shasign or not status:
            error_msg = 'PayZen : received bad data %s' % (data)
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = 'PayZen: received data for reference %s' % (reference)
            if not tx:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        # verify shasign
        shasign_check = tx.acquirer_id._payzen_generate_digital_sign('out', data)
        if shasign_check.upper() != shasign.upper():
            error_msg = _('PayZen: invalid shasign, received %s, computed %s, for data %s') % (shasign, shasign_check, data)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _payzen_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        # check what is bought
        amount = float(int(data.get('vads_amount', 0)) / math.pow(10, int(self.currency_id.decimal_places)))
        
        if float_compare(amount, self.amount, int(self.currency_id.decimal_places)) != 0:
            invalid_parameters.append(('amount', amount, '%.2f' % self.amount))

        currency_code = payzen_currencies.get(self.currency_id.name, 0)
        if int(data.get('vads_currency')) != currency_code:
            invalid_parameters.append(('currency', data.get('vads_currency'), currency_code))

        return invalid_parameters

    def _payzen_form_validate(self, data):
        payzen_statuses = {'success': ['AUTHORISED', 'AUTHORISED_TO_VALIDATE', 'CAPTURED', 'CAPTURE_FAILED'],
                         'pending': ['WAITING_AUTHORISATION', 'WAITING_AUTHORISATION_TO_VALIDATE', 'INITIAL', 'UNDER_VERIFICATION'],
                         'cancel': ['NOT_CREATED', 'ABANDONED']
                        }

        html_3ds = '3-DS authentication : '
        if data.get('vads_threeds_status') == 'Y':
            html_3ds += 'YES'
            html_3ds += '<br />3-DS certificate : ' + data.get('vads_threeds_cavv')
        else:
            html_3ds += 'NO'

        status = data.get('vads_trans_status')
        if status in payzen_statuses['success']:
            self.write({
                'acquirer_reference': data.get('vads_trans_id'),
                'state': 'done',
                'state_message': '%s' % (data),
                'html_3ds': html_3ds
            })
            return True
        elif status in payzen_statuses['pending']:
            self.write({
                'acquirer_reference': data.get('vads_trans_id'),
                'state': 'pending',
                'state_message': '%s' % (data),
                'html_3ds': html_3ds
            })
            return True
        elif status in payzen_statuses['cancel']:
            self.write({
                'state': 'cancel',
                'state_message': '%s' % (data)
            })
            return False
        else:
            auth_result = data.get('vads_auth_result')
            auth_message = ''
            if auth_result in _AUTH_RESULT:
                auth_message = _AUTH_RESULT[auth_result]

            error_msg = 'PayZen payment error, message %s, code %s' % (auth_message, auth_result)
            _logger.info(error_msg)

            self.write({
                'acquirer_reference': data.get('vads_trans_id'),
                'state': 'error',
                'state_message': '%s' % (data),
                'authresult_message': auth_message,
                'html_3ds': html_3ds
            })
            return False
