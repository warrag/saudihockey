# # -*- coding: utf-8 -*-
from datetime import date
# from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
from odoo import http
from odoo import api, fields, models, tools, _
import datetime
from werkzeug import urls
import functools
import dateutil.relativedelta as relativedelta
import urllib
import requests
import re
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
        trim_blocks=True,               # do not output newline after blocks
        autoescape=True,                # XML/HTML automatic escaping
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


class ContractTemplate(models.Model):
    _name = 'hr.contract.template'
    _description = 'Contract Templates'

    @api.model
    def _get_default_model(self):
        model = self.env['ir.model'].search([('model', '=', 'hr.contract')])
        return model

    name = fields.Char(string="Name", translate=True, required=True)
    body = fields.Html(string="Body", translate=True, required=True)
    model_id = fields.Many2one(
        'ir.model', string='Applies to', default=_get_default_model, help="The type of document this template can be used with")
    lang = fields.Char('Language', help="Use this field to either force a specific language (ISO code) or dynamically "
                                        "detect the language of your recipient by a placeholder expression "
                                        "(e.g. ${object.partner_id.lang})")

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
