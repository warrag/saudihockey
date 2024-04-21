from odoo import fields, models, api


class HrResignation(models.Model):
    _inherit = 'hr.employee.resignation'

    count_eos = fields.Integer(string='End Of Service Count', compute='count_end_of_service')

    def count_end_of_service(self):
        for record in self:
            eos_ids = self.env['end.of.service.reward'].search([('resignation_id', '=', record.id)])
            record.count_eos = len(eos_ids)

    def action_generate_eos(self):
        result = self.env.ref('plustech_hr_end_of_service.end_of_service_award_action').read()[0]
        view_id = self.env.ref('plustech_hr_end_of_service.view_end_of_service_award_form').id
        result.update({'views': [(view_id, 'form')], })
        result['context'] = {
            'default_employee_id': self.employee_id.id,
            'default_resignation_id': self.id,
            'default_last_work_date': self.expected_leaving_date
        }
        return result

    def action_open_eos(self):
        self.ensure_one()
        action, = self.env.ref('plustech_hr_end_of_service.end_of_service_award_action').read()
        action['domain'] = [('resignation_id', '=', self.id)]
        return action
