from odoo import models, fields, api, _


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    member_ids = fields.Many2many(
        'res.users',
        'crm_team_member_rel',
        'team_id',
        'user_id',
        string='Team Members',
        domain=[('share', '=', False)],  # Only internal users
        help='Salespeople who are members of this team and can access all team orders'
    )

    # Enhanced computed fields
    member_count = fields.Integer(
        string='Number of Members',
        compute='_compute_member_count',
        store=True
    )

    sales_order_count = fields.Integer(
        string='Sales Orders Count',
        compute='_compute_sales_order_count'
    )

    @api.depends('member_ids')
    def _compute_member_count(self):
        for team in self:
            team.member_count = len(team.member_ids)

    def _compute_sales_order_count(self):
        """Compute the number of sales orders for this team"""
        for team in self:
            team.sales_order_count = self.env['sale.order'].search_count([
                ('team_id', '=', team.id)
            ])

    @api.onchange('user_id')
    def _onchange_user_id(self):
        """Auto-add team leader to members when changed"""
        if self.user_id and self.user_id not in self.member_ids:
            self.member_ids = [(4, self.user_id.id)]

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-add team leader to members on creation"""
        teams = super().create(vals_list)
        for team in teams:
            if team.user_id and team.user_id not in team.member_ids:
                team.member_ids = [(4, team.user_id.id)]
        return teams

    def write(self, vals):
        """Auto-add team leader to members when updated"""
        result = super().write(vals)
        if 'user_id' in vals:
            for team in self:
                if team.user_id and team.user_id not in team.member_ids:
                    team.member_ids = [(4, team.user_id.id)]
        return result

    def action_view_sales_orders(self):
        """Action to view all sales orders for this team"""
        return {
            'name': _('Sales Orders - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form,pivot,graph',
            'domain': [('team_id', '=', self.id)],
            'context': {
                'default_team_id': self.id,
                'search_default_team_id': self.id,
            }
        }

    def action_view_team_members(self):
        """Action to view team members"""
        return {
            'name': _('Team Members - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.member_ids.ids)],
            'context': {'create': False}
        }

    def get_team_accessible_orders_domain(self):
        """Get domain for orders accessible to any member of this team"""
        member_ids = self.member_ids.ids
        if not member_ids:
            return [('id', '=', 0)]  # No members, no access

        return [
            '|', '|', '|',
            ('team_id', '=', self.id),  # Team orders
            ('user_id', 'in', member_ids),  # Primary salesperson in team
            ('secondary_salesperson_id', 'in', member_ids),  # Secondary in team
            ('team_id.member_ids', 'in', member_ids)  # Any team with these members
        ]