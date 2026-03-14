from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
import calendar
from odoo import api, SUPERUSER_ID


class BangLuong(models.Model):
    _name = 'tinh.luong.bang.luong'
    _description = 'Bảng tính lương'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ma_dinh_danh'
    _sql_constraints = [
        (
            'unique_salary',
            'unique(ma_dinh_danh, thang, nam)',
            'Nhân viên đã có bảng lương tháng này!'
        )
    ]

    ma_dinh_danh = fields.Many2one(
        'hr.employee',
        string="Nhân viên",
        required=True,
        states={'draft': [('readonly', False)]},
        readonly=True
    )

    thang = fields.Selection([
        ('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'),
        ('4', 'Tháng 4'), ('5', 'Tháng 5'), ('6', 'Tháng 6'),
        ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'),
        ('10', 'Tháng 10'), ('11', 'Tháng 11'), ('12', 'Tháng 12'),
    ], string="Tháng",
        default=lambda self: str(date.today().month),
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    nam = fields.Integer(
        "Năm",
        default=lambda self: date.today().year,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('paid', 'Đã thanh toán'),
        ('cancel', 'Hủy bỏ'),
    ], string="Trạng thái", default='draft', tracking=True)

    line_ids = fields.One2many(
        'tinh.luong.line',
        'bang_luong_id',
        string="Chi tiết lương"
    )

    # tong_nhan = fields.Float(
    #     string="Thực lĩnh",
    #     compute="_compute_total",
    #     store=True
    # )

    so_lan_muon = fields.Integer(
        compute="_compute_attendance",
        store=True
    )

    ngay_cong_chuan = fields.Integer(string="Công chuẩn", compute="_compute_attendance")
    so_cong_thuc_te = fields.Integer(string="Công thực tế", compute="_compute_attendance")
    so_ngay_huong_phu_cap = fields.Integer(string="Ngày đi làm", compute="_compute_attendance")
    so_gio_tang_ca = fields.Float(string="Giờ tăng ca", compute="_compute_attendance")

    tong_thu_nhap = fields.Float(
        string="Tổng thu nhập",
        compute="_compute_totals",
        store=True
    )

    tong_khau_tru = fields.Float(
        string="Tổng khấu trừ",
        compute="_compute_totals",
        store=True
    )

    luong_net = fields.Float(
        string="Lương thực lĩnh",
        compute="_compute_totals",
        store=True
    )

    tien_tang_ca = fields.Float(string="Tiền tăng ca", compute="_compute_breakdown")
    tien_an_trua = fields.Float(string="Tiền ăn trưa", compute="_compute_breakdown")
    tien_xang_xe = fields.Float(string="Tiền xăng xe", compute="_compute_breakdown")
    tien_thuong_kpi = fields.Float(string="Thưởng KPI", compute="_compute_breakdown")
    tien_phat_muon = fields.Float(string="Phạt đi muộn", compute="_compute_breakdown")
    bhxh_nv = fields.Float(string="BHXH nhân viên", compute="_compute_breakdown")
    thue_tncn = fields.Float(string="Thuế TNCN", compute="_compute_breakdown")

    @api.depends('line_ids.amount', 'line_ids.line_type')
    def _compute_totals(self):
        self = self.with_context(allow_write=True)
        for rec in self:
            thu = sum(l.amount for l in rec.line_ids if l.line_type == 'income')
            tru = sum(l.amount for l in rec.line_ids if l.line_type == 'deduction')

            rec.tong_thu_nhap = thu
            rec.tong_khau_tru = tru
            rec.luong_net = thu - tru

    @api.depends('line_ids.amount', 'line_ids.name')
    def _compute_breakdown(self):
        self = self.with_context(allow_write=True)
        for rec in self:
            rec.tien_tang_ca = 0
            rec.tien_an_trua = 0
            rec.tien_xang_xe = 0
            rec.tien_thuong_kpi = 0
            rec.tien_phat_muon = 0
            rec.bhxh_nv = 0
            rec.thue_tncn = 0

            for line in rec.line_ids:
                if line.name == "Tiền tăng ca":
                    rec.tien_tang_ca += line.amount
                elif line.name == "Tiền ăn trưa":
                    rec.tien_an_trua += line.amount
                elif line.name == "Tiền xăng xe":
                    rec.tien_xang_xe += line.amount
                elif line.name == "Thưởng KPI":
                    rec.tien_thuong_kpi += line.amount
                elif line.name == "Phạt đi muộn":
                    rec.tien_phat_muon += line.amount
                elif line.name == "BHXH nhân viên":
                    rec.bhxh_nv += line.amount
                elif line.name == "Thuế TNCN":
                    rec.thue_tncn += line.amount

    @api.depends('ma_dinh_danh', 'thang', 'nam')
    def _compute_attendance(self):
        self = self.with_context(allow_write=True)
        for rec in self:
            rec.ngay_cong_chuan = 0
            rec.so_cong_thuc_te = 0
            rec.so_ngay_huong_phu_cap = 0
            rec.so_gio_tang_ca = 0  

            if not rec.ma_dinh_danh:
                continue

            _, days_in_month = calendar.monthrange(rec.nam, int(rec.thang))

            rec.ngay_cong_chuan = 26

            first_day = date(rec.nam, int(rec.thang), 1)
            last_day = date(rec.nam, int(rec.thang), days_in_month)

            records_cc = self.env['bang_cham_cong'].search([
                ('nhan_vien_id', '=', rec.ma_dinh_danh.id),
                ('ngay_cham_cong', '>=', first_day),
                ('ngay_cham_cong', '<=', last_day)
            ])

            rec.so_lan_muon = sum(1 for r in records_cc if r.phut_di_muon > 0)

            ngay_di_lam = len(records_cc.filtered(
                lambda r: r.gio_vao
            ))

            ngay_nghi_phep = len(records_cc.filtered(
                lambda r: r.loai_don == 'nghi'
            ))

            rec.so_cong_thuc_te = ngay_di_lam + ngay_nghi_phep
            rec.so_ngay_huong_phu_cap = ngay_di_lam
            ot_hours = 0
            for r in records_cc:

                if not r.gio_ra or not r.gio_ra_ca:
                    continue

                overtime = (r.gio_ra - r.gio_ra_ca).total_seconds() / 3600

                if overtime > 0:
                    ot_hours += overtime

            rec.so_gio_tang_ca = ot_hours

    def action_compute_salary(self):
        self = self.with_context(allow_write=True)
        for rec in self:
            rec._compute_attendance()
            if rec.state != 'draft':
                raise UserError("Chỉ tính lương khi ở trạng thái Nháp!")

            if not rec.ma_dinh_danh:
                raise UserError("Chưa chọn nhân viên!")

            rec.line_ids.unlink()

            config = self.env['cau.hinh.luong'].search([
                ('employee_id','=',rec.ma_dinh_danh.id)
            ], limit=1)
            if not config:
                raise UserError("Nhân viên chưa có cấu hình lương!")
            config = config[0]

            setting = self.env['payroll.setting'].search([], limit=1)
            if not setting:
                raise UserError("Chưa cấu hình Payroll Setting!")

            if rec.ngay_cong_chuan > 0:
                luong_thoi_gian = (
                    config.luong_co_ban / rec.ngay_cong_chuan
                ) * rec.so_cong_thuc_te
            else:
                luong_thoi_gian = 0

            tien_an_trua = config.tro_cap_an_trua * rec.so_ngay_huong_phu_cap
            tien_xang_xe = config.tro_cap_xang_xe * rec.so_ngay_huong_phu_cap
            phu_cap_chuc_vu = config.phu_cap_chuc_vu
            phu_cap_co_dinh = config.phu_cap_co_dinh

            luong_gio = config.luong_co_ban / (26 * 8)

            tien_tang_ca = rec.so_gio_tang_ca * luong_gio * 1.5

            kpi_record = self.env['kpi.danh.gia'].search([
                ('ma_dinh_danh', '=', rec.ma_dinh_danh.id),
                ('thang', '=', rec.thang),
                ('nam', '=', rec.nam)
            ], limit=1)

            tien_kpi = kpi_record.tien_thuong if kpi_record else 0
            tien_phat = rec.so_lan_muon * config.muc_phat_muon

            def add_line(name, amount, ltype):
                if amount:
                    self.env['tinh.luong.line'].create({
                        'bang_luong_id': rec.id,
                        'name': name,
                        'amount': amount,
                        'line_type': ltype
                    })

            add_line("Lương thời gian", luong_thoi_gian, 'income')
            add_line("Phụ cấp chức vụ", phu_cap_chuc_vu, 'income')
            add_line("Phụ cấp cố định", phu_cap_co_dinh, 'income')
            add_line("Tiền tăng ca", tien_tang_ca, 'income')
            add_line("Tiền ăn trưa", tien_an_trua, 'income')
            add_line("Tiền xăng xe", tien_xang_xe, 'income')
            add_line("Thưởng KPI", tien_kpi, 'income')

            tong_thu = sum(l.amount for l in rec.line_ids if l.line_type == 'income')

            bhxh = config.luong_bhxh * setting.ty_le_bhxh_nv

            thu_nhap_chiu_thue = tong_thu - bhxh
            thue = max(
                0,
                (thu_nhap_chiu_thue - setting.muc_giam_tru_ban_than)
                * setting.ty_le_thue
            )

            add_line("Phạt đi muộn", tien_phat, 'deduction')
            add_line("BHXH nhân viên", bhxh, 'deduction')
            add_line("Thuế TNCN", thue, 'deduction')

    def action_confirm(self):
        self = self.with_context(allow_write=True)
        for rec in self:
            if not rec.line_ids:
                rec.action_compute_salary()

            _, days = calendar.monthrange(rec.nam, int(rec.thang))
            first_day = date(rec.nam, int(rec.thang), 1)
            last_day = date(rec.nam, int(rec.thang), days)

            records_cc = self.env['bang_cham_cong'].search([
                ('nhan_vien_id', '=', rec.ma_dinh_danh.id),
                ('ngay_cham_cong', '>=', first_day),
                ('ngay_cham_cong', '<=', last_day)
            ])

            records_cc.write({'is_locked': True})

            rec.state = 'confirmed'

    def action_pay(self):
        self = self.with_context(allow_write=True)
        self.write({'state': 'paid'})

    def action_cancel(self):
        self = self.with_context(allow_write=True)
        self.write({'state': 'cancel'})

    def action_set_draft(self):
        self = self.with_context(allow_write=True)
        self.write({'state': 'draft'})

    def unlink(self):
        self = self.with_context(allow_write=True)
        for rec in self:

            if rec.state != 'draft':
                raise UserError("Chỉ có thể xóa khi ở trạng thái Nháp!")

            _, days = calendar.monthrange(rec.nam, int(rec.thang))

            first_day = date(rec.nam, int(rec.thang), 1)
            last_day = date(rec.nam, int(rec.thang), days)

            records_cc = self.env['bang_cham_cong'].search([
                ('nhan_vien_id','=',rec.ma_dinh_danh.id),
                ('ngay_cham_cong','>=',first_day),
                ('ngay_cham_cong','<=',last_day)
            ])

            records_cc.write({'is_locked': False})

        return super().unlink()

    # ================== THÊM: KHÓA SỬA SAU CONFIRM ==================
    def write(self, vals):
        for rec in self:
            if rec.state in ['confirmed', 'paid'] \
            and not self.env.user.has_group('base.group_system') \
            and not self.env.context.get('allow_write'):
                raise UserError("Chỉ Admin mới được chỉnh sửa khi đã xác nhận!")
        return super().write(vals)

    # ================== THÊM: GỬI EMAIL ==================
    def action_send_email(self):
        template = self.env.ref('tinh_luong.email_template_payroll')
        template.send_mail(self.id, force_send=True)

    # ================== THÊM: AUTO TẠO LƯƠNG THÁNG TRƯỚC ==================
    @api.model
    def cron_auto_create_payroll(self):
        today = date.today()
        thang = today.month - 1 or 12
        nam = today.year if today.month != 1 else today.year - 1

        employees = self.env['hr.employee'].search([])

        for emp in employees:
            exists = self.search([
                ('ma_dinh_danh', '=', emp.id),
                ('thang', '=', str(thang)),
                ('nam', '=', nam)
            ], limit=1)

            if not exists:
                self.create({
                    'ma_dinh_danh': emp.id,
                    'thang': str(thang),
                    'nam': nam
                })

    def init(self):
        env = api.Environment(self._cr, SUPERUSER_ID, {})

        employees = env['hr.employee'].search([])

        for emp in employees:

            exists = env['tinh.luong.bang.luong'].search([
                ('ma_dinh_danh','=',emp.id),
                ('thang','=','2'),
                ('nam','=',2026)
            ])

            if not exists:

                env['tinh.luong.bang.luong'].create({
                    "ma_dinh_danh": emp.id,
                    "thang": "2",
                    "nam": 2026
                })
