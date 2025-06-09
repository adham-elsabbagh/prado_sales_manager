{
    'name': 'Sales Access Control',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Enhanced access control for sales orders based on teams and management hierarchy',
    'description': """
Sales Access Control Module
============================

This module extends the access control for sales orders to support:

* Salespeople can access orders where they are primary or secondary salesperson
* Salespeople can access all orders from their assigned sales teams
* Country Managers can access all orders visible to salespeople they manage

Features:
---------
* Secondary Salesperson field on Sales Orders
* Team membership management for salespeople
* Country Manager to Salesperson mapping
* Enhanced security rules for proper access control
* Admin interfaces for managing relationships

Technical Details:
------------------
* Compatible with Odoo 17.0
* Uses record rules for security
* Optimized for performance with proper indexing
* Includes migration and demo data
    """,
    'author': 'Adham',
    'license': 'MIT',
    'depends': [
        'base',
        'sale',
        'sales_team',
    ],
    'data': [
        'security/sales_access_security.xml',
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/crm_team_views.xml',
        'views/sales_country_manager_views.xml',
        'views/res_users_views.xml',
        'views/sales_access_menus.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}