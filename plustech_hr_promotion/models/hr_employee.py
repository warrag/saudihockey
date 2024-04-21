from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    promotion_count = fields.Integer(string='Promotions', compute='compute_promotion_count')
    last_promotion_id = fields.Many2one('employee.promotion', string='Employee Last Promotion')

    def compute_promotion_count(self):
        for record in self:
            promotions = self.env['employee.promotion'].search([('employee_id', '=', record.id)])
            record.promotion_count = len(promotions)

    def action_promotion_view(self):
        self.ensure_one()
        result = self.env.ref('plustech_hr_promotion.employee_promotion_history_action').read()[0]
        result['domain'] = [('employee_id', '=', self.id)]
        return result


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    promotion_count = fields.Integer(string='Promotions', compute='promotion_count')
    last_promotion_id = fields.Many2one('employee.promotion', string='Employee Last Promotion')
