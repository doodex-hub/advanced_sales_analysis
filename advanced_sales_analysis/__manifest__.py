# -*- coding: utf-8 -*-
{
    'name': "Advanced Sales Analysis",

    'summary': """
        This custom Odoo module enhances the Sales Analysis report by providing additional financial insights. It introduces three key metrics to give a more detailed view of the sales pipeline and cash flow status.
    """,

    'description': """
        This custom Odoo module enhances the Sales Analysis report by providing additional financial insights. It introduces three key metrics to give a more detailed view of the sales pipeline and cash flow status.
    """,

    'author': "Doodex",
    'company': "Doodex",
    'website': "https://www.doodex.net/",

    'category': 'Sales',
    'version': '17.0.1.0.0',

    'depends': ['base','sale','account','sale_management'],

    'data': [
        # 'security/ir.model.access.csv',
    ],

    'images': [
       'static/description/banner.gif',
       'static/description/icon.png',
    ],
    'license': 'LGPL-3',
    'price': 20,
    'currency': "USD",
}
