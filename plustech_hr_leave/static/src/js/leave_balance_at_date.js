odoo.define("plustech_hr_leave.import.mixin", function (require) {
	"use strict";
	/**
	 * This is the MIXIN that will show the balance at date which will be used by list  controllers.
	 */
	var core = require("web.core");
	var _t = core._t;
	var LeaveBalanceMixin = {
		_onGenerate: function (event) {
		this.do_action({
			name: _("Balance"),
			type: "ir.actions.act_window",
			view_mode: "form",
			view_type: "form",
			views: [[false, "form"]],
			res_model: "leave.balance.history",
			target: "new",
		});
		},
	};
	return LeaveBalanceMixin;
});

odoo.define("plustech_hr_leave.balance.tree", function (require) {
	"use strict";
	var core = require("web.core");
	var ListController = require("web.ListController");
	var ListView = require("web.ListView");
	var LeaveBalanceMixin = require("plustech_hr_leave.import.mixin");
	var viewRegistry = require("web.view_registry");
	 var session = require('web.session');

	var LeaveBalanceListController = ListController.extend(
		LeaveBalanceMixin,
		{
		buttons_template: "LeaveBalanceReport.Buttons",
		events: _.extend({}, ListController.prototype.events, {
			"click .o_button_balance_at_date": "_onGenerate",
		}),
		}
	);

	var LeaveBalanceListView = ListView.extend({
		config: _.extend({}, ListView.prototype.config, {
		Controller: LeaveBalanceListController,
		}),
	});
	if(session.user_has_group('base.group_system')){
	   	viewRegistry.add("leave_balance_tree", LeaveBalanceListView);

	}
	});