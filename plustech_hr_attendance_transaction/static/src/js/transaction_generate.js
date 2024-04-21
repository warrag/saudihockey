odoo.define("plustech_hr_attendance_transaction.import.mixin", function (require) {
	"use strict";
	/**
	 * This is the MIXIN that will show the generate wizard which will be used by list  controllers.
	 */
	var core = require("web.core");
	var _t = core._t;
	var GenerateTransactionMixin = {
		_onGenerate: function (event) {
		this.do_action({
			name: _("Transaction Generate"),
			type: "ir.actions.act_window",
			view_mode: "form",
			view_type: "form",
			views: [[false, "form"]],
			res_model: "transaction.generate.wizard",
			target: "new",
		});
		},
	};
	return GenerateTransactionMixin;
});

odoo.define("plustech_hr_attendance_transaction.generate.tree", function (require) {
	"use strict";
	var core = require("web.core");
	var ListController = require("web.ListController");
	var ListView = require("web.ListView");
	var GenerateTransactionMixin = require("plustech_hr_attendance_transaction.import.mixin");
	var viewRegistry = require("web.view_registry");
	 var session = require('web.session');

	var AttendanceTransactionListController = ListController.extend(
		GenerateTransactionMixin,
		{
		buttons_template: "AttendanceTransactionListView.buttons",
		events: _.extend({}, ListController.prototype.events, {
			"click .o_button_generate_transaction": "_onGenerate",
		}),
		}
	);

	var AttendanceTransactionListView = ListView.extend({
		config: _.extend({}, ListView.prototype.config, {
		Controller: AttendanceTransactionListController,
		}),
	});
	if(session.user_has_group('base.group_system')){
	   	viewRegistry.add("attendance_transaction_tree", AttendanceTransactionListView);

	}
	});