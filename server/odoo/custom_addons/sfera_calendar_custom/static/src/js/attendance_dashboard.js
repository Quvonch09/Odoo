/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AttendanceDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.notification = useService("notification");
        
        const today = new Date();
        this.state = useState({
            batch_id: this.props.action.context.batch_id,
            batch_name: this.props.action.context.batch_name || "Guruh",
            month: today.getMonth() + 1,
            year: today.getFullYear(),
            students: [],
            sessions: [],
            attendance: {},
            showModal: false,
            showReasonModal: false,
            activeStudent: null,
            activeSession: null,
            activeStatus: null,
            activeRemark: "",
            student_count: 0
        });

        onWillStart(async () => {
            await this.fetchData();
        });
    }

    async fetchData() {
        const data = await this.rpc({
            model: "op.batch",
            method: "get_attendance_data",
            args: [this.state.batch_id, this.state.month, this.state.year],
        });

        const today = new Date().toISOString().split('T')[0];
        
        // Process sessions to add some helper flags
        const sessions = data.sessions.map(s => ({
            ...s,
            is_today: s.date === today,
            is_future: s.date > today,
            weekday_short: new Date(s.date).toLocaleDateString('uz-UZ', { weekday: 'short' })
        }));

        this.state.students = data.students.map(s => ({
            ...s,
            initials: s.name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
        }));
        this.state.sessions = sessions;
        this.state.attendance = data.attendance;
        this.state.student_count = data.students.length;
        this.state.batch_name = data.batch_name;
    }

    get current_month_name() {
        const months = [
            "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", 
            "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"
        ];
        return months[this.state.month - 1];
    }

    prevMonth() {
        if (this.state.month === 1) {
            this.state.month = 12;
            this.state.year -= 1;
        } else {
            this.state.month -= 1;
        }
        this.fetchData();
    }

    nextMonth() {
        if (this.state.month === 12) {
            this.state.month = 1;
            this.state.year += 1;
        } else {
            this.state.month += 1;
        }
        this.fetchData();
    }

    openStatusModal(student, session) {
        if (session.is_future) {
            this.notification.add("Kelajakdagi darsga davomat qilib bo'lmaydi", { type: "warning" });
            return;
        }
        this.state.activeStudent = student;
        this.state.activeSession = session;
        this.state.showModal = true;
    }

    closeModal() {
        this.state.showModal = false;
    }

    async setStatus(status) {
        this.state.activeStatus = status;
        await this.saveAttendance('');
        this.closeModal();
    }

    onSelectAbsent(status) {
        this.state.activeStatus = status;
        this.state.activeRemark = "";
        
        // Check if there's already a remark
        const existing = this.state.attendance[this.state.activeStudent.id]?.[this.state.activeSession.id];
        if (existing && existing.remark) {
            this.state.activeRemark = existing.remark;
        }
        
        this.state.showModal = false;
        this.state.showReasonModal = true;
    }

    closeReasonModal() {
        this.state.showReasonModal = false;
    }

    async saveWithReason() {
        if (this.state.activeRemark.trim() === "") {
            this.notification.add("Iltimos, sababni kiriting", { type: "danger" });
            return;
        }
        await this.saveAttendance(this.state.activeRemark);
        this.closeReasonModal();
    }

    async saveAttendance(remark) {
        await this.rpc("/web/dataset/call_kw/op.batch/set_attendance_status", {
            model: "op.batch",
            method: "set_attendance_status",
            args: [
                this.state.batch_id, 
                this.state.activeStudent.id, 
                this.state.activeSession.id, 
                this.state.activeStatus,
                remark
            ],
            kwargs: {},
        });
        
        // Update local state for immediate feedback
        if (!this.state.attendance[this.state.activeStudent.id]) {
            this.state.attendance[this.state.activeStudent.id] = {};
        }
        this.state.attendance[this.state.activeStudent.id][this.state.activeSession.id] = {
            status: this.state.activeStatus,
            remark: remark
        };
        
        this.notification.add("Davomat saqlandi", { type: "success" });
    }

    onBack() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'op.batch',
            res_id: this.state.batch_id,
            view_mode: 'form',
            target: 'current'
        });
    }
}

AttendanceDashboard.template = "sfera_calendar_custom.AttendanceDashboard";

registry.category("actions").add("sfera_attendance_dashboard", AttendanceDashboard);
