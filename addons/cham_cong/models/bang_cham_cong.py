from odoo import models, fields, api
from datetime import datetime, time
from odoo.exceptions import ValidationError
from pytz import timezone, UTC

class BangChamCong(models.Model):
    _name = 'bang_cham_cong'
    _description = "Bảng chấm công"
    _rec_name = 'Id_BCC'

    # --- LIÊN KẾT NHÂN SỰ ---
    # Hàm này giúp tự động chọn đúng nhân viên dựa trên tài khoản đang đăng nhập
    def _get_default_nhan_vien(self):
        return self.env['nhan_vien'].search([('user_id', '=', self.env.user.id)], limit=1)

    nhan_vien_id = fields.Many2one(
        'nhan_vien', 
        string="Nhân viên", 
        required=True, 
        default=_get_default_nhan_vien
    )
    ngay_cham_cong = fields.Date("Ngày chấm công", required=True, default=fields.Date.context_today)
    Id_BCC = fields.Char(string="ID BCC", compute="_compute_Id_BCC", store=True)

    @api.depends('nhan_vien_id', 'ngay_cham_cong')
    def _compute_Id_BCC(self):
        for record in self:
            if record.nhan_vien_id and record.ngay_cham_cong:
                record.Id_BCC = f"{record.nhan_vien_id.ho_va_ten}_{record.ngay_cham_cong.strftime('%Y-%m-%d')}"
            else:
                record.Id_BCC = "Mới"

    # --- ĐĂNG KÝ CA LÀM ---
    dang_ky_ca_lam_id = fields.Many2one('dang_ky_ca_lam_theo_ngay', string="Đăng ký ca làm")
    ca_lam = fields.Selection(related='dang_ky_ca_lam_id.ca_lam', store=True, string="Ca làm")

    # --- ĐƠN TỪ LIÊN QUAN ---
    don_tu_id = fields.Many2one('don_tu', string="Đơn từ được duyệt")
    loai_don = fields.Selection(related='don_tu_id.loai_don', string='Loại đơn')
    thoi_gian_xin = fields.Float(related='don_tu_id.thoi_gian_xin', string='Số phút xin phép')

    # --- LOGIC TÌM KIẾM DỮ LIỆU TỰ ĐỘNG (Search Link) ---
    @api.onchange('nhan_vien_id', 'ngay_cham_cong')
    def _onchange_link_data(self):
        """Tự động tìm Ca làm và Đơn từ khi chọn Nhân viên/Ngày"""
        for record in self:
            if record.nhan_vien_id and record.ngay_cham_cong:
                # Tìm ca làm
                dk_ca = self.env['dang_ky_ca_lam_theo_ngay'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('ngay_lam', '=', record.ngay_cham_cong)
                ], limit=1)
                record.dang_ky_ca_lam_id = dk_ca.id if dk_ca else False

                # Tìm đơn từ (Đã duyệt)
                don = self.env['don_tu'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('ngay_ap_dung', '=', record.ngay_cham_cong),
                    ('trang_thai_duyet', '=', 'da_duyet')
                ], limit=1)
                record.don_tu_id = don.id if don else False

    # --- GIỜ GIẤC & TÍNH TOÁN ---
    gio_vao_ca = fields.Datetime("Giờ vào ca (Hệ thống)", compute='_compute_gio_ca', store=True)
    gio_ra_ca = fields.Datetime("Giờ ra ca (Hệ thống)", compute='_compute_gio_ca', store=True)
    
    gio_vao = fields.Datetime("Giờ vào thực tế")
    gio_ra = fields.Datetime("Giờ ra thực tế")

    @api.depends('ca_lam', 'ngay_cham_cong')
    def _compute_gio_ca(self):
        user_tz = self.env.user.tz or 'Asia/Ho_Chi_Minh'
        tz = timezone(user_tz)
        for record in self:
            if not record.ngay_cham_cong or not record.ca_lam:
                record.gio_vao_ca = record.gio_ra_ca = False
                continue

            # Quy định giờ theo ca
            times = {
                "Sáng": (time(7, 30), time(11, 30)),
                "Chiều": (time(13, 30), time(17, 30)),
                "Cả ngày": (time(7, 30), time(17, 30))
            }
            
            if record.ca_lam in times:
                v, r = times[record.ca_lam]
                # Localize về múi giờ VN sau đó chuyển sang UTC để lưu DB
                dt_v = tz.localize(datetime.combine(record.ngay_cham_cong, v)).astimezone(UTC).replace(tzinfo=None)
                dt_r = tz.localize(datetime.combine(record.ngay_cham_cong, r)).astimezone(UTC).replace(tzinfo=None)
                record.gio_vao_ca = dt_v
                record.gio_ra_ca = dt_r

    # --- ĐI MUỘN / VỀ SỚM ---
    phut_di_muon = fields.Float("Số phút đi muộn", compute="_compute_phut_phat", store=True)
    phut_ve_som = fields.Float("Số phút về sớm", compute="_compute_phut_phat", store=True)
    
    @api.depends('gio_vao', 'gio_ra', 'gio_vao_ca', 'gio_ra_ca', 'don_tu_id', 'thoi_gian_xin')
    def _compute_phut_phat(self):
        for record in self:
            # 1. Tính đi muộn
            dm_goc = 0
            if record.gio_vao and record.gio_vao_ca and record.gio_vao > record.gio_vao_ca:
                dm_goc = (record.gio_vao - record.gio_vao_ca).total_seconds() / 60
            
            # Trừ phép đi muộn
            if record.don_tu_id and record.loai_don == 'di_muon':
                record.phut_di_muon = max(0, dm_goc - record.thoi_gian_xin)
            else:
                record.phut_di_muon = dm_goc

            # 2. Tính về sớm
            vs_goc = 0
            if record.gio_ra and record.gio_ra_ca and record.gio_ra < record.gio_ra_ca:
                vs_goc = (record.gio_ra_ca - record.gio_ra).total_seconds() / 60
            
            # Trừ phép về sớm
            if record.don_tu_id and record.loai_don == 've_som':
                record.phut_ve_som = max(0, vs_goc - record.thoi_gian_xin)
            else:
                record.phut_ve_som = vs_goc

    # --- TRẠNG THÁI ---
    trang_thai = fields.Selection([
        ('di_lam', 'Đúng giờ'),
        ('di_muon', 'Đi muộn'),
        ('ve_som', 'Về sớm'),
        ('di_muon_ve_som', 'Muộn & Sớm'),
        ('chua_vao_ca', 'Chưa đến ca làm'),
    ], string="Trạng thái", compute="_compute_trang_thai", store=True)
    
    @api.depends('phut_di_muon', 'phut_ve_som', 'gio_vao', 'gio_ra')
    def _compute_trang_thai(self):
        for record in self:
            if not record.gio_vao and not record.gio_ra:
                record.trang_thai = 'chua_vao_ca'
            elif record.phut_di_muon > 0 and record.phut_ve_som > 0:
                record.trang_thai = 'di_muon_ve_som'
            elif record.phut_di_muon > 0:
                record.trang_thai = 'di_muon'
            elif record.phut_ve_som > 0:
                record.trang_thai = 've_som'
            else:
                record.trang_thai = 'di_lam'

    loai_ngay_cong = fields.Selection([
        ('di_lam', 'Đi làm thực tế'),
        ('nghi_phep', 'Nghỉ phép hưởng lương'),
        ('nghi_khong_luong', 'Nghỉ không lương'),
        ('le_tet', 'Nghỉ lễ/tết'),
        ('vang_mat', 'Vắng mặt/Chưa xác định')
    ], string="Loại ngày công", compute="_compute_loai_ngay_cong", store=True)

    so_gio_tang_ca = fields.Float("Số giờ tăng ca", compute="_compute_tang_ca", store=True)

    @api.depends('gio_vao', 'gio_ra', 'don_tu_id', 'trang_thai')
    def _compute_loai_ngay_cong(self):
        for record in self:
            # Ưu tiên 1: Có đi làm thực tế
            if record.gio_vao or record.gio_ra:
                record.loai_ngay_cong = 'di_lam'
            # Ưu tiên 2: Xét đơn từ nếu không đi làm
            elif record.don_tu_id and record.don_tu_id.trang_thai_duyet == 'da_duyet':
                if record.loai_don == 'nghi_phep':
                    record.loai_ngay_cong = 'nghi_phep'
                elif record.loai_don == 'nghi_khong_luong':
                    record.loai_ngay_cong = 'nghi_khong_luong'
                else:
                    record.loai_ngay_cong = 'vang_mat'
            else:
                record.loai_ngay_cong = 'vang_mat'

    @api.depends('don_tu_id', 'don_tu_id.trang_thai_duyet')
    def _compute_tang_ca(self):
        for record in self:
            # Giả sử có loại đơn 'tang_ca' và thoi_gian_xin tính bằng giờ
            if record.don_tu_id and record.loai_don == 'tang_ca' and record.don_tu_id.trang_thai_duyet == 'da_duyet':
                record.so_gio_tang_ca = record.thoi_gian_xin
            else:
                record.so_gio_tang_ca = 0.0