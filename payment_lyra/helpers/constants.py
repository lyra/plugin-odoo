# coding: utf-8
#
# Copyright © Lyra Network.
# This file is part of Lyra plugin for Odoo. See COPYING.md for license details.
#
# Author:    Lyra Network (https://www.lyra-network.com)
# Copyright: Copyright © Lyra Network
# License:   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)

from odoo import  _

pluginFeatures = {
    'qualif' : False,
    'shatwo' : True,
}

LYRA_PARAMS = {
    'GATEWAY_CODE': 'Lyra',
    'GATEWAY_NAME': 'Lyra',
    'BACKOFFICE_NAME': 'Lyra Expert',
    'GATEWAY_URL': 'https://secure.lyra.com/vads-payment/',
    'SITE_ID': '12345678',
    'KEY_TEST': '1111111111111111',
    'KEY_PROD': '2222222222222222',
    'SIGN_ALGO': 'SHA-256',
    'LANGUAGE': 'en',
    'GATEWAY_VERSION': 'V2',
    'PLUGIN_VERSION': '1.1.0',
    'CMS_IDENTIFIER': 'Odoo_10-12',
}

LYRA_LANGUAGES = {
    'cn': _('Chinese'),
    'de': _('German'),
    'es': _('Spanish'),
    'en': _('English'),
    'fr': _('French'),
    'it': _('Italian'),
    'jp': _('Japanese'),
    'nl': _('Dutch'),
    'pl': _('Polish'),
    'pt': _('Portuguese'),
    'ru': _('Russian'),
    'sv': _('Swedish'),
    'tr': _('Turkish'),
}

LYRA_CARDS = {
    'CB': u'CB',
    'E-CARTEBLEUE': u'E-CARTEBLEUE',
    'MAESTRO': u'Maestro',
    'MASTERCARD': u'Mastercard',
    'VISA': u'Visa',
    'VISA_ELECTRON': u'Visa Electron',
    'VPAY': u'V PAY',
    'AMEX': u'American Express',
    'CONECS': u'Titre-Restaurant Dématérialisé Conecs',
    'APETIZ': u'Titre-Restaurant Dématérialisé Apetiz',
    'CHQ_DEJ': u'Titre-Restaurant Dématérialisé Chèque Déjeuner',
    'SODEXO': u'Titre-Restaurant Dématérialisé Sodexo',
    'EDENRED': u'Ticket Restaurant',
    'PAYPAL': u'PayPal',
    'PAYPAL_SB': u'PayPal - Sandbox',
    'ALIPAY': u'Alipay',
    'BANCONTACT': u'Bancontact Mistercash',
    'GIROPAY': u'Giropay',
    'IDEAL': u'iDEAL',
    'MULTIBANCO': u'Multibanco',
    'MYBANK': u'MyBank',
    'PRZELEWY24': u'Przelewy24',
    'SOFORT_BANKING': u'Sofort',
    'UNION_PAY': u'UnionPay',
    'WECHAT': u'WeChat Pay',
}

LYRA_CURRENCIES = {
    'CAD': u'124',
    'DKK': u'208',
    'JPY': u'392',
    'NOK': u'578',
    'CHF': u'756',
    'GBP': u'826',
    'USD': u'840',
    'EUR': u'978',
    'PLN': u'985',
}

LYRA_AUTH_RESULT = {
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
