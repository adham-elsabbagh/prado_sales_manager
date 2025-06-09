from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SalesCountryManager(models.Model):
    _name = 'sales.country.manager'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sales Country Manager'
    _rec_name = 'manager_id'
    _order = 'manager_id'

    manager_id = fields.Many2one(
        'res.users',
        string='Country Manager',
        required=True,
        domain=[('share', '=', False)],  # Only internal users
        help='User who acts as a country manager'
    )

    salespeople_ids = fields.Many2many(
        'res.users',
        'sales_country_manager_salesperson_rel',
        'manager_id',
        'salesperson_id',
        string='Managed Salespeople',
        domain=[('share', '=', False)],  # Only internal users
        help='Salespeople managed by this country manager'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Inactive records are hidden from most views'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    # Computed fields for better UX
    salespeople_count = fields.Integer(
        string='Number of Salespeople',
        compute='_compute_salespeople_count',
        store=True
    )

    @api.depends('salespeople_ids')
    def _compute_salespeople_count(self):
        for record in self:
            record.salespeople_count = len(record.salespeople_ids)

    @api.constrains('manager_id', 'salespeople_ids')
    def _check_manager_not_in_salespeople(self):
        """Ensure manager is not in their own salespeople list"""
        for record in self:
            if record.manager_id.id in record.salespeople_ids.ids:
                raise ValidationError(_(
                    "A country manager cannot manage themselves. "
                    "Please remove %s from the salespeople list."
                ) % record.manager_id.name)

    @api.constrains('manager_id')
    def _check_unique_manager(self):
        """Ensure each user is only a manager in one record"""
        for record in self:
            domain = [
                ('manager_id', '=', record.manager_id.id),
                ('id', '!=', record.id),
                ('company_id', '=', record.company_id.id)
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_(
                    "User %s is already defined as a country manager. "
                    "Each user can only be a country manager once per company."
                ) % record.manager_id.name)

    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"{record.manager_id.name} ({len(record.salespeople_ids)} salespeople)"
            result.append((record.id, name))
        return result

    @api.model
    def get_managed_salespeople(self, manager_user_id):
        """Get all salespeople managed by a specific manager"""
        manager_record = self.search([
            ('manager_id', '=', manager_user_id),
            ('active', '=', True)
        ], limit=1)

        if manager_record:
            return manager_record.salespeople_ids.ids
        return []

    @api.model
    def is_country_manager(self, user_id):
        """Check if a user is a country manager"""
        return bool(self.search_count([
            ('manager_id', '=', user_id),
            ('active', '=', True)
        ]))

    def action_view_sales_orders(self):
        """Action to view all sales orders accessible to this country manager"""
        # Get all salespeople managed by this manager
        salesperson_ids = self.salespeople_ids.ids

        # Build domain for sales orders accessible to managed salespeople
        domain = [
            '|', '|', '|',
            ('user_id', 'in', salesperson_ids),
            ('secondary_salesperson_id', 'in', salesperson_ids),
            ('team_id.member_ids', 'in', salesperson_ids),
            ('team_id.user_id', 'in', salesperson_ids)  # Team leader
        ]

        return {
            'name': _('Sales Orders - %s') % self.manager_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {
                'default_user_id': False,  # Don't auto-assign
                'search_default_my_quotation': 0,  # Don't filter by current user
            }
        }