from odoo import models, fields, api
from datetime import datetime
from odoo import api, SUPERUSER_ID


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'
    # ===== Thông tin bổ sung =====
    ma_dinh_danh = fields.Char("Mã định danh")
    que_quan = fields.Char("Quê quán")
    cccd = fields.Char("CCCD")

    # ===== Liên kết tổ chức =====
    don_vi_id = fields.Many2one("don_vi", string="Đơn vị")
    chuc_vu_id = fields.Many2one("chuc_vu", string="Chức vụ")

    tuoi = fields.Integer(compute="_compute_tuoi", store=True)
    lich_su_cong_tac_ids = fields.One2many(
        "lich_su_cong_tac",
        "nhan_vien_id",
        string="Lịch sử công tác"
    )

    danh_sach_chung_chi_bang_cap_ids = fields.One2many(
        "danh_sach_chung_chi_bang_cap",
        "nhan_vien_id",
        string="Chứng chỉ"
    )
    
    cau_hinh_luong_id = fields.One2many(
        'cau.hinh.luong',
        'employee_id',
        string="Cấu hình lương"
    )

    @api.depends('birthday')
    def _compute_tuoi(self):
        for rec in self:
            if rec.birthday:
                rec.tuoi = datetime.now().year - rec.birthday.year
            else:
                rec.tuoi = 0
                
    def init(self):

        env = api.Environment(self._cr, SUPERUSER_ID, {})

        # Lấy dữ liệu tổ chức
        dv_cong_nghe = env["don_vi"].search([("ma_don_vi", "=", "DV01")], limit=1)
        dv_kinh_doanh = env["don_vi"].search([("ma_don_vi", "=", "DV02")], limit=1)
        dv_hanh_chinh = env["don_vi"].search([("ma_don_vi", "=", "DV03")], limit=1)

        dev = env["chuc_vu"].search([("ma_chuc_vu", "=", "CV01")], limit=1)
        tester = env["chuc_vu"].search([("ma_chuc_vu", "=", "CV02")], limit=1)
        leader = env["chuc_vu"].search([("ma_chuc_vu", "=", "CV03")], limit=1)
        manager = env["chuc_vu"].search([("ma_chuc_vu", "=", "CV04")], limit=1)

        employees = [
            {
                "name": "Nguyễn Văn An",
                "ma_dinh_danh": "NV001",
                "cccd": "079203000111",
                "que_quan": "Cần Thơ",
                "don_vi_id": dv_cong_nghe.id,
                "chuc_vu_id": dev.id,
            },
            {
                "name": "Trần Thị Bình",
                "ma_dinh_danh": "NV002",
                "cccd": "079203000222",
                "que_quan": "Hậu Giang",
                "don_vi_id": dv_cong_nghe.id,
                "chuc_vu_id": tester.id,
            },
            {
                "name": "Lê Minh Châu",
                "ma_dinh_danh": "NV003",
                "cccd": "079203000333",
                "que_quan": "An Giang",
                "don_vi_id": dv_cong_nghe.id,
                "chuc_vu_id": leader.id,
            },
            {
                "name": "Phạm Quốc Dũng",
                "ma_dinh_danh": "NV004",
                "cccd": "079203000444",
                "que_quan": "Kiên Giang",
                "don_vi_id": dv_cong_nghe.id,
                "chuc_vu_id": manager.id,
            },
            {
                "name": "Hoàng Thị Mai",
                "ma_dinh_danh": "NV005",
                "cccd": "079203000555",
                "que_quan": "Sóc Trăng",
                "don_vi_id": dv_kinh_doanh.id,
                "chuc_vu_id": leader.id,
            },
            {
                "name": "Đặng Văn Nam",
                "ma_dinh_danh": "NV006",
                "cccd": "079203000666",
                "que_quan": "Bạc Liêu",
                "don_vi_id": dv_kinh_doanh.id,
                "chuc_vu_id": dev.id,
            },
            {
                "name": "Ngô Thị Phương",
                "ma_dinh_danh": "NV007",
                "cccd": "079203000777",
                "que_quan": "Vĩnh Long",
                "don_vi_id": dv_hanh_chinh.id,
                "chuc_vu_id": manager.id,
            },
            {
                "name": "Võ Thành Trung",
                "ma_dinh_danh": "NV008",
                "cccd": "079203000888",
                "que_quan": "Đồng Tháp",
                "don_vi_id": dv_cong_nghe.id,
                "chuc_vu_id": dev.id,
            },
            {
                "name": "Bùi Thanh Hòa",
                "ma_dinh_danh": "NV009",
                "cccd": "079203000999",
                "que_quan": "Cà Mau",
                "don_vi_id": dv_cong_nghe.id,
                "chuc_vu_id": tester.id,
            },
            {
                "name": "Phan Thu Trang",
                "ma_dinh_danh": "NV010",
                "cccd": "079203001010",
                "que_quan": "TP.HCM",
                "don_vi_id": dv_hanh_chinh.id,
                "chuc_vu_id": leader.id,
            },
        ]

        for emp in employees:

            exist = env["hr.employee"].search([
                ("ma_dinh_danh", "=", emp["ma_dinh_danh"])
            ])

            if not exist:
                env["hr.employee"].create(emp)