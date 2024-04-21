odoo.define('plustech_hr_leave.LeaveStatsWidget', function (require) {
    'use strict';

    var time = require('web.time');
    var Widget = require('web.Widget');
    var widget_registry = require('web.widget_registry');
    var LeaveStatsWidget = require('hr_holidays.LeaveStatsWidget');
    var fieldUtils = require('web.field_utils');
    var session = require('web.session');
    var LeaveStatsWidgetExtend = LeaveStatsWidget.extend({
        init: function(parent, action) {
            this._super(parent, action);
            var options = action.params || {};
            this.params = options;
            this.leaveType = action.context.default_plus_type;
        },

         _fetchDepartmentLeaves: function () {
            if (!this.date || !this.department) {
                this.departmentLeaves = null;
                return Promise.resolve();
            }
            var self = this;
            var month_date_from = this.date.clone().startOf('month');
            var month_date_to = this.date.clone().endOf('month');
            return this._rpc({
                model: 'hr.leave',
                method: 'search_read',
                args: [
                    [['department_id', '=', this.department.res_id],
                    ['plus_type', '=', this.leaveType],
                    ['state', '=', 'validate'],
                    ['holiday_type', '=', 'employee'],
                    ['date_from', '<=', month_date_to],
                    ['date_to', '>=', month_date_from]],
                    ['employee_id', 'date_from', 'date_to', 'number_of_days'],
                ],
            }).then(function (data) {
                var dateFormat = time.getLangDateFormat();
                self.departmentLeaves = data.map(function (leave) {
                    // Format datetimes to date (in the user's format)
                    return _.extend(leave, {
                        date_from: fieldUtils.parse.datetime(
                            leave.date_from,
                            false,
                            { isUTC: true }).local().format(dateFormat),
                        date_to: fieldUtils.parse.datetime(
                            leave.date_to,
                            false,
                            { isUTC: true }).local().format(dateFormat),
                        number_of_days: leave.number_of_days,
                    });
                });
            });
        },
        _fetchLeaveTypesData: function (options) {
            if (!this.date || !this.employee) {
                this.leavesPerType = null;
                return Promise.resolve();
            }
            var self = this;
            var year_date_from = this.date.clone().startOf('year');
            var year_date_to = this.date.clone().endOf('year');
            return this._rpc({
                model: 'hr.leave',
                method: 'read_group',
                kwargs: {
                    domain: [['plus_type', '=', this.leaveType],['employee_id', '=', this.employee.res_id], ['state', '=', 'validate'], ['date_from', '<=', year_date_to], ['date_to', '>=', year_date_from]],
                    fields: ['holiday_status_id', 'number_of_days:sum'],
                    groupby: ['holiday_status_id'],
                },
                'context': {'LeaveStats': true}
            }).then(function (data) {
                self.leavesPerType = data;
            });
        }

 });

        widget_registry.add('hr_leave_stats', LeaveStatsWidgetExtend);

    });
