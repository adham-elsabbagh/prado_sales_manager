from odoo import models, fields, api, _
from odoo.exceptions import AccessError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    secondary_salesperson_id = fields.Many2one(
        'res.users',
        string='Secondary Salesperson',
        domain=[('share', '=', False)],  # Only internal users
        help='Secondary salesperson for this order',
        index=True,  # Add index for performance
        tracking=True  # Track changes
    )

    # Computed field to show all people with access to this order
    accessible_user_ids = fields.Many2many(
        'res.users',
        string='Users with Access',
        compute='_compute_accessible_users',
        help='All users who have access to view this sales order'
    )

    @api.depends('user_id', 'secondary_salesperson_id', 'team_id', 'team_id.member_ids')
    def _compute_accessible_users(self):
        """Compute all users who should have access to this order"""
        for order in self:
            accessible_users = self.env['res.users']

            # Primary salesperson
            if order.user_id:
                accessible_users |= order.user_id

            # Secondary salesperson
            if order.secondary_salesperson_id:
                accessible_users |= order.secondary_salesperson_id

            # Team members
            if order.team_id and order.team_id.member_ids:
                accessible_users |= order.team_id.member_ids

            # Team leader (if different from primary salesperson)
            if order.team_id and order.team_id.user_id:
                accessible_users |= order.team_id.user_id

            # Country managers of accessible salespeople
            country_manager_obj = self.env['sales.country.manager']
            for user in accessible_users:
                # Find country managers who manage this user
                managers = country_manager_obj.search([
                    ('salespeople_ids', 'in', user.id),
                    ('active', '=', True)
                ])
                accessible_users |= managers.mapped('manager_id')

            order.accessible_user_ids = accessible_users

    def _get_user_access_domain(self, user_id):
        """Get domain for orders accessible to a specific user"""
        user = self.env['res.users'].browse(user_id)

        # Check if user is a country manager
        country_manager_obj = self.env['sales.country.manager']
        managed_salespeople = country_manager_obj.get_managed_salespeople(user_id)

        if managed_salespeople:
            # User is a country manager - can see orders of managed salespeople
            domain = [
                '|', '|', '|', '|',
                ('user_id', '=', user_id),  # Own orders
                ('secondary_salesperson_id', '=', user_id),  # As secondary
                ('user_id', 'in', managed_salespeople),  # Managed salespeople orders
                ('secondary_salesperson_id', 'in', managed_salespeople),  # Managed as secondary
                ('team_id.member_ids', 'in', managed_salespeople + [user_id])  # Team orders
            ]
        else:
            # Regular salesperson
            domain = [
                '|', '|', '|',
                ('user_id', '=', user_id),  # Primary salesperson
                ('secondary_salesperson_id', '=', user_id),  # Secondary salesperson
                ('team_id.member_ids', 'in', [user_id]),  # Team member
                ('team_id.user_id', '=', user_id)  # Team leader
            ]

        return domain

    @api.model
    def search(self, domain, offset=0, limit=None, order=None):
        """Override search to apply access control"""
        # Only apply custom access control for non-admin users
        if not self.env.user.has_group('base.group_system'):
            access_domain = self._get_user_access_domain(self.env.user.id)
            domain = ['&'] + domain + access_domain

        return super().search(domain, offset=offset, limit=limit, order=order)

    def write(self, vals):
        """Override write to ensure proper access control"""
        # Check if user has access to modify these records
        for order in self:
            if not self.env.user.has_group('base.group_system'):
                access_domain = order._get_user_access_domain(self.env.user.id)
                accessible_orders = self.search(access_domain + [('id', '=', order.id)])
                if not accessible_orders:
                    raise AccessError(_("You don't have access to modify this sales order."))

        return super().write(vals)

    def action_view_accessible_users(self):
        """Action to view all users with access to this order"""
        self.ensure_one()
        return {
            'name': _('Users with Access - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.accessible_user_ids.ids)],
            'context': {'create': False, 'edit': False}
        }