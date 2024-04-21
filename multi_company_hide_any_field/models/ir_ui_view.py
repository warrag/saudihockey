from odoo import models, SUPERUSER_ID


class IrUiView(models.Model):
	_inherit = 'ir.ui.view'

	def _apply_groups(self, node, name_manager, node_info):
		result = super(IrUiView, self)._apply_groups(node, name_manager, node_info)
		# Rules not work for superuser
		model = name_manager.model._name
		if self._uid == SUPERUSER_ID:
			return result
		try:
			self._cr.execute("SELECT id FROM ir_model WHERE model=%s", (model,))
			model_rec = self.env['ir.model'].sudo().browse(self._cr.fetchone()[0])
			field_ids = self.env.user.company_id.field_configuration_ids
			field_ids = field_ids.filtered(lambda field:self.env.user.id in field.user_ids.ids)
			for config_rec in field_ids:
				if (node.tag == 'field' and node.get('name') == config_rec.field_id.name) and model_rec.id==config_rec.model_id.id:
					node_info['modifiers']['invisible'] = True
						
		except Exception:
			return True
		return True
