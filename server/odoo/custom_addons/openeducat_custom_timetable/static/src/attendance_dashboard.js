/** @odoo-module name="@openeducat_custom_timetable/attendance_dashboard" **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class AttendanceDashboard extends Component {
    static template = "openeducat_custom_timetable.AttendanceDashboard";

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");
        
        this.state = useState({
            batch_id: this.props.action.context.batch_id || this.props.action.context.active_id,
            batch_name: this.props.action.context.batch_name || "Guruh",
            month: new Date().getMonth() + 1,
            year: new Date().getFullYear(),
            students: [],
            sessions: [],
            attendance: {},
            showModal: false,
            showReasonModal: false,
            activeStudentId: null,
            activeSessionId: null,
            activeStatus: null,
            activeRemark: "",
            isLoading: true,
        });

        onWillStart(async () => {
            await this.fetchData();
        });
    }

    async fetchData() {
        this.state.isLoading = true;
        try {
            const data = await this.orm.call(
                "op.batch",
                "get_attendance_data",
                [this.state.batch_id, this.state.month, this.state.year]
            );
            
            if (data) {
                this.state.students = (data.students || []).map(s => ({
                    ...s,
                    initials: s.name ? s.name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2) : '??'
                })).sort((a, b) => a.name.localeCompare(b.name));

                this.state.sessions = (data.sessions || []).map(s => {
                    const d = new Date(s.date);
                    const days = ["Ya", "Du", "Se", "Ch", "Pa", "Ju", "Sh"];
                    return { 
                        ...s, 
                        day: d.getDate(), 
                        weekday: days[d.getDay()] || '' 
                    };
                });

                this.state.attendance = data.attendance || {};
                this.state.batch_name = data.batch_name || this.state.batch_name;
            }
        } catch (e) {
            console.error("Attendance Fetch Error:", e);
        } finally {
            this.state.isLoading = false;
        }
    }

    openStatusModal(student, session) {
        this.state.activeStudentId = student.id;
        this.state.activeSessionId = session.id;
        this.state.showModal = true;
    }

    async setStatus(status) {
        this.state.activeStatus = status;
        if (status === 'present') {
            await this.saveAttendance('');
            this.state.showModal = false;
        } else {
            this.state.showModal = false;
            this.state.activeRemark = "";
            // Check if existing remark
            const existing = this.state.attendance[this.state.activeStudentId]?.[this.state.activeSessionId];
            if (existing && existing.remark) {
                this.state.activeRemark = existing.remark;
            }
            this.state.showReasonModal = true;
        }
    }

    async saveAttendance(remark) {
        try {
            await this.orm.call(
                "op.batch",
                "set_attendance_status",
                [this.state.batch_id, this.state.activeStudentId, this.state.activeSessionId, this.state.activeStatus, remark]
            );
            await this.fetchData(); 
            this.state.showReasonModal = false;
            this.notification.add("Saqlandi", { type: "success" });
        } catch (e) {
            this.notification.add("Xatolik bo'ldi", { type: "danger" });
        }
    }

    onBack() {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'op.batch',
            res_id: this.state.batch_id,
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'current'
        });
    }

    get currentMonthName() {
        const months = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"];
        return months[this.state.month - 1];
    }
}

registry.category("actions").add("sfera_attendance_dashboard", AttendanceDashboard);
