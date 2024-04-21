# # -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
import logging
from odoo import api, fields, models, tools, _
import datetime
from werkzeug import urls
import functools
import dateutil.relativedelta as relativedelta

_logger = logging.getLogger(__name__)
try:
    from jinja2.sandbox import SandboxedEnvironment

    mako_template_env = SandboxedEnvironment(
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="${",
        variable_end_string="}",
        comment_start_string="<%doc>",
        comment_end_string="</%doc>",
        line_statement_prefix="%",
        line_comment_prefix="##",
        trim_blocks=True,  # do not output newline after blocks
        autoescape=True,  # XML/HTML automatic escaping
    )
    mako_template_env.globals.update({
        'str': str,
        'quote': urls.url_quote,
        'urlencode': urls.url_encode,
        'datetime': datetime,
        'len': len,
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'filter': filter,
        'reduce': functools.reduce,
        'map': map,
        'round': round,

        'relativedelta': lambda *a, **kw: relativedelta.relativedelta(*a, **kw),
    })
except ImportError:
    _logger.warning("jinja2 not available, templating features will not work!")


class LetterLetter(models.Model):
    _name = 'letter.letter'
    _description = 'Letters'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_model(self):
        model = self.env['ir.model'].search([('model', '=', 'letter.request')])
        return model

    name = fields.Char()
    body = fields.Html(string="Body", translate=True, required=False)
    model_id = fields.Many2one('ir.model', string='Applies to', default=_get_default_model, help="The type of document this template can be used with")
    lang = fields.Char('Language', help="Use this field to either force a specific language (ISO code) or dynamically "
                                        "detect the language of your recipient by a placeholder expression "
                                        "(e.g. ${object.partner_id.lang})")
    need_approval = fields.Boolean(string='Need Approval')
    stage_ids = fields.One2many(comodel_name='letter.temp.stage', inverse_name='letter_id')
    categ_id = fields.Many2one(comodel_name='letter.letter.categ', string="Category", required=False)
    report_xml_id = fields.Char('Report XML ID', required=0)
    field_ids = fields.One2many('hr.letter.fields', 'template_id')
    active = fields.Boolean('Active', default=True)
    version = fields.Char('Version', )

    def render_template(self, template, model, res_id):
        template = mako_template_env.from_string(tools.ustr(template))
        user = self.env.user
        record = self.env[model].browse(res_id)
        variables = {'user': user, 'object': record}
        try:
            render_result = template.render(variables)
        except Exception:
            _logger.error("Failed to render template %r using values %r" % (
                template, variables))
            render_result = u""
        if render_result == u"False":
            render_result = u""

        return render_result


class LetterTempStages(models.Model):
    _name = 'letter.temp.stage'
    _description = 'Letters Template Stages'
    _rec_name = 'stage_id'
    _order = 'sequence, id'

    letter_id = fields.Many2one('letter.letter')
    appear_on_report = fields.Boolean('Appear On Report')
    sequence = fields.Integer(default=1)
    stage_id = fields.Many2one('letter.stages', required=True)
    approval = fields.Selection(string='', selection=[
        ('employee', 'Employee'),
        ('direct_mg', 'Direct Manager'),
        ('depart_mg', 'Department Manager'),
        ('hr_officer', 'HR Officer'),
        ('hr_Manager', 'HR Manager'),
        ('financial', 'Financial'),
        ('ceo', 'CEO'),
    ], required=True, )
    user_ids = fields.Many2many('res.users', string='Approvers')
    print = fields.Boolean('Print', related="stage_id.print", readonly=False)
    default_stage = fields.Boolean(string='Is Default Stage', related="stage_id.default_stage")
    readonly = fields.Boolean('Readonly', related="stage_id.readonly", readonly=False)
    cancel_stage = fields.Boolean(string='Is cancel stage', related="stage_id.cancel_stage", readonly=False)
    cancel_stage = fields.Boolean(string='Is Refuse', related="stage_id.cancel_stage", readonly=False)
    sent_notification = fields.Boolean(string='Sent Notification', readonly=False, related="stage_id.sent_notification")
    activity_type_id = fields.Many2one('mail.activity.type', related="stage_id.activity_type_id", string='Activity Type', readonly=False)

    @api.onchange('stage_id')
    def change_stage_id(self):
        domain = self.letter_id.stage_ids.mapped('stage_id').ids
        return {'domain': {'stage_id': [('id', 'not in', domain)]}}

    @api.constrains('default_stage')
    def _check_unique_code(self):
        for line in self:
            lines = self.env['letter.stages'].search([('id', '!=', line.id), ('default_stage', '=', True)])
            if len(lines) > 0 and self.default_stage:
                raise ValidationError(_('There is default stage already defined!'))


class LetterLetterCategory(models.Model):
    _name = 'letter.letter.categ'
    _description = 'Letters Categories'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', tracking=True)
