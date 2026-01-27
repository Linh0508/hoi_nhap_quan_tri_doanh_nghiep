from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError

class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Bảng chứa thông tin nhân viên'
    _rec_name = 'ho_va_ten'
    _order = 'ten asc, tuoi desc'

    # --- Thông tin định danh ---
    ma_dinh_danh = fields.Char("Mã định danh", required=True)
    ho_ten_dem = fields.Char("Họ tên đệm", required=True)
    ten = fields.Char("Tên", required=True)
    ho_va_ten = fields.Char("Họ và tên", compute="_compute_ho_va_ten", store=True)
    
    phu_cap_an_trua_theo_ngay = fields.Float(string="Phụ cấp ăn trưa/ngày", default=30000)
    phu_cap_xang_xe_theo_ngay = fields.Float(string="Phụ cấp xăng xe/ngày", default=15000)
    don_gia_phat_muon = fields.Float(string="Đơn giá phạt muộn/phút", default=1000)
    luong_co_ban = fields.Float(string="Lương cơ bản")
    luong_bhxh = fields.Float(string="Lương đóng BHXH")

    # --- LIÊN KẾT TÀI KHOẢN (Quan trọng nhất để sửa lỗi lấy nhầm tên) ---
    user_id = fields.Many2one(
        'res.users', 
        string="Tài khoản hệ thống", 
        help="Liên kết với tài khoản đăng nhập để tự động nhận diện nhân viên khi chấm công/viết đơn."
    )

    # --- Thông tin cá nhân ---
    ngay_sinh = fields.Date("Ngày sinh", required=True)
    tuoi = fields.Integer("Tuổi", compute="_compute_tinh_tuoi", store=True)
    gioi_tinh = fields.Selection(
        [
            ("Nam", "Nam"),
            ("Nữ", "Nữ")
        ],
        string="Giới tính",
        required=True,
    )
    que_quan = fields.Char("Quê quán", required=True)
    email = fields.Char("Email", required=True)
    so_dien_thoai = fields.Char("Số điện thoại", required=True)
    anh = fields.Binary("Ảnh")

    # --- Thông tin công tác (Tự động lấy từ lịch sử) ---
    phong_ban_id = fields.Many2one("phong_ban", string="Phòng ban", compute="_compute_cong_tac", store=True)
    chuc_vu_id = fields.Many2one("chuc_vu", string="Chức vụ", compute="_compute_cong_tac", store=True)
    
    # --- Quan hệ One2many ---
    lich_su_cong_tac_ids = fields.One2many(
        "lich_su_cong_tac", 
        inverse_name="nhan_vien_id", 
        string="Danh sách lịch sử công tác"
    )
    danh_sach_chung_chi_bang_cap_ids = fields.One2many(
        "danh_sach_chung_chi_bang_cap",
        inverse_name="nhan_vien_id",
        string="Danh sách chứng chỉ bằng cấp"
    )
    
    # --- Logic tính toán (Compute Methods) ---

    @api.depends("ngay_sinh")
    def _compute_tinh_tuoi(self): 
        for record in self:
            if record.ngay_sinh:
                year_now = datetime.now().year  
                record.tuoi = year_now - record.ngay_sinh.year
            else:
                record.tuoi = 0
    
    @api.depends('ho_ten_dem', 'ten')
    def _compute_ho_va_ten(self):
        for record in self:
            ho = record.ho_ten_dem or ''
            ten = record.ten or ''
            record.ho_va_ten = f"{ho} {ten}".strip()
            
    @api.depends("lich_su_cong_tac_ids", "lich_su_cong_tac_ids.trang_thai", "lich_su_cong_tac_ids.loai_chuc_vu")
    def _compute_cong_tac(self):
        """
        Tự động cập nhật Phòng ban và Chức vụ hiện tại của nhân viên 
        dựa trên bản ghi Lịch sử công tác đang giữ chức vụ 'Chính'.
        """
        for record in self:
            # Tìm kiếm bản ghi công tác đang giữ và là chức vụ chính
            lich_su = self.env['lich_su_cong_tac'].search([
                ('nhan_vien_id', '=', record.id),
                ('loai_chuc_vu', '=', "Chính"),
                ('trang_thai', '=', "Đang giữ")
            ], limit=1)
            
            if lich_su:
                record.chuc_vu_id = lich_su.chuc_vu_id.id
                record.phong_ban_id = lich_su.phong_ban_id.id
            else:
                record.chuc_vu_id = False
                record.phong_ban_id = False

    # --- Ràng buộc (Constraints) ---
    @api.constrains("tuoi")
    def _check_tuoi(self):
        for record in self:
            if record.tuoi < 18:
                raise ValidationError("Nhân viên phải từ 18 tuổi trở lên!")