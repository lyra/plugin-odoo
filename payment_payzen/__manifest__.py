# -*- coding: utf-8 -*-

{
    'name': 'PayZen Payment Acquirer',
    'category': 'Hidden',
    'summary': 'Payment Acquirer: PayZen Implementation',
    'version': '0.9.1',
    'description': """PayZen Payment Acquirer""",
    'author': 'Sudokeys, Lyra Network',
    'depends': ['payment'],
    'data': [
        'views/payzen.xml',
        'views/payment_views.xml',
        'data/payzen.xml',
    ],
    'installable': True,
}
