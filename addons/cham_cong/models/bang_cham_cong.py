from odoo import models, fields, api
from datetime import datetime, time
from pytz import timezone, UTC
from odoo.exceptions import UserError
from odoo import api, SUPERUSER_ID
from datetime import datetime

class BangChamCong(models.Model):
    _name = 'bang_cham_cong'
    _description = "Bảng chấm công"
    _rec_name = 'Id_BCC'

    def _get_default_nhan_vien(self):
        return self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)], limit=1
        )

    nhan_vien_id = fields.Many2one(
        'hr.employee',
        string="Nhân viên",
        required=True,
        default=_get_default_nhan_vien
    )

    ngay_cham_cong = fields.Date(
        "Ngày chấm công",
        required=True,
        default=fields.Date.context_today
    )

    Id_BCC = fields.Char(
        string="ID BCC",
        compute="_compute_Id_BCC",
        store=True
    )

    @api.depends('nhan_vien_id', 'ngay_cham_cong')
    def _compute_Id_BCC(self):
        for record in self:
            if record.nhan_vien_id and record.ngay_cham_cong:
                record.Id_BCC = f"{record.nhan_vien_id.name}_{record.ngay_cham_cong.strftime('%Y-%m-%d')}"
            else:
                record.Id_BCC = "Mới"

    dang_ky_ca_lam_id = fields.Many2one(
        'dang_ky_ca_lam_theo_ngay',
        string="Đăng ký ca làm"
    )

    ca_lam = fields.Selection(
        related='dang_ky_ca_lam_id.ca_lam',
        store=True,
        string="Ca làm"
    )

    don_tu_id = fields.Many2one(
        'don_tu',
        string="Đơn từ được duyệt"
    )

    loai_don = fields.Selection(
        related='don_tu_id.loai_don',
        store=True,
        string='Loại đơn'
    )

    thoi_gian_xin = fields.Float(
        related='don_tu_id.thoi_gian_xin',
        string='Số phút xin phép'
    )

    def _link_related_data(self):
        for record in self:

            dk_ca = self.env['dang_ky_ca_lam_theo_ngay'].search([
                ('nhan_vien_id', '=', record.nhan_vien_id.id),
                ('ngay_lam', '=', record.ngay_cham_cong)
            ], limit=1)

            record.dang_ky_ca_lam_id = dk_ca.id if dk_ca else False

            don = self.env['don_tu'].search([
                ('nhan_vien_id', '=', record.nhan_vien_id.id),
                ('ngay_ap_dung', '=', record.ngay_cham_cong),
                ('trang_thai_duyet', '=', 'da_duyet')
            ], limit=1)

            record.don_tu_id = don.id if don else False

    @api.onchange('nhan_vien_id', 'ngay_cham_cong')
    def _onchange_link_data(self):
        self._link_related_data()

    gio_vao_ca = fields.Datetime(
        compute='_compute_gio_ca',
        store=True
    )

    gio_ra_ca = fields.Datetime(
        compute='_compute_gio_ca',
        store=True
    )

    gio_vao = fields.Datetime("Giờ vào thực tế")
    gio_ra = fields.Datetime("Giờ ra thực tế")

    @api.depends('ca_lam', 'ngay_cham_cong')
    def _compute_gio_ca(self):

        tz = timezone(self.env.user.tz or 'Asia/Ho_Chi_Minh')

        for record in self:

            if not record.ngay_cham_cong or not record.ca_lam:
                record.gio_vao_ca = False
                record.gio_ra_ca = False
                continue

            times = {
                "Sáng": (time(7,30), time(11,30)),
                "Chiều": (time(13,30), time(17,30)),
                "Cả ngày": (time(7,30), time(17,30))
            }

            if record.ca_lam in times:

                v, r = times[record.ca_lam]

                local_in = tz.localize(datetime.combine(record.ngay_cham_cong, v))
                local_out = tz.localize(datetime.combine(record.ngay_cham_cong, r))

                utc_in = local_in.astimezone(UTC).replace(tzinfo=None)
                utc_out = local_out.astimezone(UTC).replace(tzinfo=None)

                record.gio_vao_ca = utc_in
                record.gio_ra_ca = utc_out

    phut_di_muon = fields.Float(
        compute="_compute_phut_phat",
        store=True
    )

    phut_ve_som = fields.Float(
        compute="_compute_phut_phat",
        store=True
    )

    is_late = fields.Boolean(
        compute="_compute_late_flag",
        store=True
    )

    late_minutes = fields.Integer(
        compute="_compute_late_flag",
        store=True
    )

    is_locked = fields.Boolean(default=False)

    @api.depends(
        'gio_vao', 'gio_ra',
        'gio_vao_ca', 'gio_ra_ca',
        'don_tu_id', 'thoi_gian_xin'
    )
    def _compute_phut_phat(self):
        for record in self:

            dm_goc = 0
            if record.gio_vao and record.gio_vao_ca and record.gio_vao > record.gio_vao_ca:
                dm_goc = (record.gio_vao - record.gio_vao_ca).total_seconds() / 60

            if record.don_tu_id and record.loai_don == 'di_muon':
                record.phut_di_muon = max(0, dm_goc - record.thoi_gian_xin)
            else:
                record.phut_di_muon = dm_goc

            vs_goc = 0
            if record.gio_ra and record.gio_ra_ca and record.gio_ra < record.gio_ra_ca:
                vs_goc = (record.gio_ra_ca - record.gio_ra).total_seconds() / 60

            if record.don_tu_id and record.loai_don == 've_som':
                record.phut_ve_som = max(0, vs_goc - record.thoi_gian_xin)
            else:
                record.phut_ve_som = vs_goc
                
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for record in records:
            record._link_related_data()
            record._generate_real_time()

        return records

    @api.depends('phut_di_muon')
    def _compute_late_flag(self):
        for record in self:
            record.late_minutes = int(record.phut_di_muon or 0)
            record.is_late = record.late_minutes > 0

    def write(self, vals):
        res = super().write(vals)

        if 'ca_lam' in vals or 'ngay_cham_cong' in vals:
            self._generate_real_time()

        return res

    def _generate_real_time(self):

        tz = timezone('Asia/Ho_Chi_Minh')

        for r in self:

            ca = r.ca_lam
            group = r.nhan_vien_id.id % 4
            date = r.ngay_cham_cong

            if not ca or not date:
                continue

            if ca == "Sáng":

                schedule = {
                    0: (time(7,30), time(11,30)),
                    1: (time(7,40), time(11,30)),
                    2: (time(7,30), time(11,10)),
                    3: (time(8,0), time(11,0))
                }

            elif ca == "Chiều":

                schedule = {
                    0: (time(13,30), time(17,30)),
                    1: (time(13,40), time(17,30)),
                    2: (time(13,30), time(17,10)),
                    3: (time(14,0), time(17,0))
                }

            else:

                schedule = {
                    0: (time(7,30), time(17,30)),
                    1: (time(7,40), time(17,30)),
                    2: (time(7,30), time(17,10)),
                    3: (time(8,0), time(17,0))
                }

            start_time, end_time = schedule[group]

            local_in = tz.localize(datetime.combine(date, start_time))
            local_out = tz.localize(datetime.combine(date, end_time))

            r.gio_vao = local_in.astimezone(UTC).replace(tzinfo=None)
            r.gio_ra = local_out.astimezone(UTC).replace(tzinfo=None)

    # def init(self):
    #     env = api.Environment(self._cr, SUPERUSER_ID, {})
    #     records = env['bang_cham_cong'].search([])

    #     tz = timezone('Asia/Ho_Chi_Minh')

    #     for r in records:

    #         ca = r.ca_lam
    #         group = r.nhan_vien_id.id % 4
    #         date = r.ngay_cham_cong

    #         if not ca or not date:
    #             continue

    #         # =========================
    #         # XÁC ĐỊNH GIỜ THEO CA + GROUP
    #         # =========================

    #         if ca == "Sáng":

    #             schedule = {
    #                 0: (time(7,30), time(11,30)),
    #                 1: (time(7,40), time(11,30)),
    #                 2: (time(7,30), time(11,10)),
    #                 3: (time(8,0), time(11,0))
    #             }

    #         elif ca == "Chiều":

    #             schedule = {
    #                 0: (time(13,30), time(17,30)),
    #                 1: (time(13,40), time(17,30)),
    #                 2: (time(13,30), time(17,10)),
    #                 3: (time(14,0), time(17,0))
    #             }

    #         else:  # Cả ngày

    #             schedule = {
    #                 0: (time(7,30), time(17,30)),
    #                 1: (time(7,40), time(17,30)),
    #                 2: (time(7,30), time(17,10)),
    #                 3: (time(8,0), time(17,0))
    #             }

    #         start_time, end_time = schedule[group]

    #         # =========================
    #         # CONVERT LOCAL → UTC
    #         # =========================

    #         local_in = tz.localize(datetime.combine(date, start_time))
    #         local_out = tz.localize(datetime.combine(date, end_time))

    #         gio_vao = local_in.astimezone(UTC).replace(tzinfo=None)
    #         gio_ra = local_out.astimezone(UTC).replace(tzinfo=None)

    #         # =========================
    #         # GHI DATABASE
    #         # =========================

    #         r.write({
    #             "gio_vao": gio_vao,
    #             "gio_ra": gio_ra
    #         })