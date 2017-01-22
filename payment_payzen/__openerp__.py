# -*- coding: utf-8 -*-

{
    'name': 'Payzen Payment Acquirer',
    'category': 'Hidden',
    'summary': 'Payment Acquirer: Payzen Implementation',
    'version': '0.9',
    'description': """
        Payzen Payment Acquirer
        
        """,
    'author': 'Sudokeys',
    'depends': ['payment'],
    'data': [
        'views/payzen.xml',
        'views/payment_acquirer.xml',
        'data/payzen.xml',
    ],
    'installable': True,
}
