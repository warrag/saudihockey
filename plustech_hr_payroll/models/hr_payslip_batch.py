from odoo import models, api, fields, _
from odoo.tools.misc import format_date


class HrPayslipRun(models.Model):
    _name = 'hr.payslip.run'
    _inherit = ['hr.payslip.run', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(selection_add=[('post', _('Posted')), ('paid', _('Paid')), ('cancel', _('Cancelled'))])
    number = fields.Char(string='Reference', readonly=True, copy=False)

    @api.model
    def create(self, vals):
        res = super(HrPayslipRun, self).create(vals)
        res.number = self.env['ir.sequence'].next_by_code('payslip.batch')
        return res

    @api.onchange('date_start')
    def _onchange_dates(self):
        if self.date_start:
            self.name = 'Payslip Batch For - %s' % (format_date(
                self.env, self.date_start, date_format="MMMM y"))

    def button_open_journal_entry(self):
        ''' Redirect the user to this payment journal.
         :return:    An action on account.move.
         '''
        self.ensure_one()
        slip_ids = self.mapped('slip_ids').filtered(lambda line: line.state not in ['draft', 'cancel'])
        move_id = slip_ids.mapped('move_id')[:1]

        return {
            'name': _("Journal Entry"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': move_id.id,
        }

    def payslip_entries_post(self):
        slip_ids = self.mapped('slip_ids').filtered(lambda line: line.state not in ['draft', 'cancel'])
        move_ids = slip_ids.move_id.filtered(lambda move: move.state == 'draft')
        move_ids.action_post()
        posted_move_ids = slip_ids.move_id.filtered(lambda move: move.state == 'draft')
        if not posted_move_ids:
            self.state = 'post'

    def action_batch_cancel(self):
        self.mapped('slip_ids').filtered(lambda line: line.state != 'cancel').action_payslip_cancel()
        self.write({'state': 'cancel'})

    def action_batch_draft(self):
        self.write({'state': 'draft'})

    def get_header(self):
        category_list_ids = self.env['hr.salary.rule.category'].search([('appears_on_payslip_batch', '=', True)])
        # find all the rule by category
        col_by_category = {}
        for payslip in self.slip_ids:
            for line in payslip.line_ids:
                col_by_category.setdefault(line.category_id, [])
                col_by_category[line.category_id] += line.salary_rule_id.filtered(lambda r: r.appears_on_payslip_batch==True).ids
        for categ_id, rule_ids in col_by_category.items():
            col_by_category[categ_id] = self.env['hr.salary.rule'].browse(set(rule_ids))
        # make the category wise rule
        result = []
        for categ_id in category_list_ids:
            rule_ids = col_by_category.get(categ_id)
            if not rule_ids:
                continue
            result.append({categ_id: rule_ids.sorted(lambda l: l.sequence)})
        return result

    def get_rule_list(self):
        get_rule_list = []
        for header_dict in self.get_header():
            for rule_ids in header_dict.values():
                for rule_id in rule_ids:
                    get_rule_list.append(rule_id)
        return get_rule_list
