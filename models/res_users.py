from odoo import models, fields, api, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    # Related fields for easier access
    is_country_manager = fields.Boolean(
        string='Is Country Manager',
        compute='_compute_is_country_manager',
        search='_search_is_country_manager',
        help='Whether this user is configured as a country manager'
    )

    managed_salespeople_ids = fields.Many2many(
        'res.users',
        string='Managed Salespeople',
        compute='_compute_managed_salespeople',
        help='Salespeople managed by this user (if they are a country manager)'
    )

    managing_country_manager_ids = fields.Many2many(
        'res.users',
        string='Country Managers',
        compute='_compute_managing_country_managers',
        help='Country managers who manage this user'
    )

    sales_team_member_ids = fields.Many2many(
        'crm.team',
        string='Member of Sales Teams',
        compute='_compute_sales_team_memberships',
        help='Sales teams this user is a member of'
    )

    primary_sales_orders_count = fields.Integer(
        string='Primary Sales Orders',
        compute='_compute_sales_orders_count'
    )

    secondary_sales_orders_count = fields.Integer(
        string='Secondary Sales Orders',
        compute='_compute_sales_orders_count'
    )

    accessible_sales_orders_count = fields.Integer(
        string='Accessible Sales Orders',
        compute='_compute_sales_orders_count'
    )

    @api.depends('sales_country_manager_ids')
    def _compute_is_country_manager(self):
        for user in self:
            user.is_country_manager = bool(
                self.env['sales.country.manager'].search_count([
                    ('manager_id', '=', user.id),
                    ('active', '=', True)
                ])
            )

    def _search_is_country_manager(self, operator, value):
        """Search method for is_country_manager field"""
        manager_records = self.env['sales.country.manager'].search([('active', '=', True)])
        manager_ids = manager_records.mapped('manager_id').ids

        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('id', 'in', manager_ids)]
        else:
            return [('id', 'not in', manager_ids)]

    @api.depends('sales_country_manager_ids.salespeople_ids')
    def _compute_managed_salespeople(self):
        for user in self:
            manager_record = self.env['sales.country.manager'].search([
                ('manager_id', '=', user.id),
                ('active', '=', True)
            ], limit=1)

            if manager_record:
                user.managed_salespeople_ids = manager_record.salespeople_ids
            else:
                user.managed_salespeople_ids = self.env['res.users']

    def _compute_managing_country_managers(self):
        for user in self:
            manager_records = self.env['sales.country.manager'].search([
                ('salespeople_ids', 'in', user.id),
                ('active', '=', True)
            ])
            user.managing_country_manager_ids = manager_records.mapped('manager_id')

    def _compute_sales_team_memberships(self):
        for user in self:
            teams = self.env['crm.team'].search([
                ('member_ids', 'in', user.id)
            ])
            user.sales_team_member_ids = teams

    def _compute_sales_orders_count(self):
        for user in self:
            # Primary sales orders
            user.primary_sales_orders_count = self.env['sale.order'].search_count([
                ('user_id', '=', user.id)
            ])

            # Secondary sales orders
            user.secondary_sales_orders_count = self.env['sale.order'].search_count([
                ('secondary_salesperson_id', '=', user.id)
            ])

            # All accessible orders (using the domain logic)
            sale_order = self.env['sale.order']
            access_domain = sale_order._get_user_access_domain(user.id)
            user.accessible_sales_orders_count = sale_order.search_count(access_domain)

    def action_view_accessible_sales_orders(self):
        """Action to view all sales orders accessible to this user"""
        self.ensure_one()

        sale_order = self.env['sale.order']
        access_domain = sale_order._get_user_access_domain(self.id)

        return {
            'name': _('Accessible Sales Orders - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form,pivot,graph',
            'domain': access_domain,
            'context': {
                'search_default_my_quotation': 0,  # Don't filter by current user
            }
        }

    def action_view_managed_salespeople(self):
        """Action to view salespeople managed by this user"""
        self.ensure_one()

        return {
            'name': _('Managed Salespeople - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.managed_salespeople_ids.ids)],
            'context': {'create': False}
        }