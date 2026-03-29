       import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Quản lý Workflow CDHA", page_icon="📋", layout="wide")

st.title("📋 PHẦN MỀM QUẢN LÝ WORKFLOW & THỜI GIAN TRẢ KẾT QUẢ CHẨN ĐOÁN HÌNH ẢNH")

DB_NAME = "quanly_workflow_cdha.db"

def get_connection():
    for attempt in range(5):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=20)
            conn.execute("PRAGMA journal_mode=WAL;")
            return conn
        except:
            time.sleep(0.5)
    return None

def init_db():
    conn = get_connection()
    if conn is None: return
    conn.execute('''CREATE TABLE IF NOT EXISTS studies (
        id INTEGER PRIMARY KEY,
        ma_yeu_cau TEXT UNIQUE,
        ma_benh_nhan TEXT,
        ten_benh_nhan TEXT,
        loai_hinh_anh TEXT,
        bac_si_chi_dinh TEXT,
        ky_thuat_vien TEXT,
        thoi_gian_bat_dau_chup TEXT,
        thoi_gian_ket_thuc_chup TEXT,
        thoi_gian_hen_tra TEXT,
        thoi_gian_tra_thuc_te TEXT,
        bac_si_doc TEXT,
        trang_thai TEXT DEFAULT 'Chờ chụp',
        ghi_chu TEXT
    )''')
    conn.commit()
    conn.close()

init_db()
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

menu = st.sidebar.selectbox("Chọn chức năng", 
    ["📋 Danh sách yêu cầu", "➕ Thêm yêu cầu mới", "🔄 Cập nhật trạng thái", "📊 Thống kê & Trễ hạn"])

# === THÊM YÊU CẦU MỚI ===
if menu == "➕ Thêm yêu cầu mới":
    st.subheader("Thêm yêu cầu chẩn đoán hình ảnh mới")
    
    col1, col2 = st.columns(2)
    with col1:
        ma_yeu_cau = st.text_input("Mã yêu cầu *", placeholder="CDHA20260329001")
        ma_bn = st.text_input("Mã bệnh nhân")
        ten_bn = st.text_input("Tên bệnh nhân *")
    with col2:
        loai_hinh = st.selectbox("Loại hình ảnh", ["X-quang", "CT Scanner", "MRI", "Siêu âm", "Mammography", "Khác"])
        bs_chi_dinh = st.text_input("Bác sĩ chỉ định")
        ky_thuat_vien = st.text_input("Kỹ thuật viên")

    if st.button("✅ Lưu yêu cầu mới", type="primary"):
        if not ma_yeu_cau or not ten_bn:
            st.error("Vui lòng nhập Mã yêu cầu và Tên bệnh nhân")
        else:
            # Tính thời gian hẹn trả
            hours = 2 if loai_hinh == "X-quang" else 6 if loai_hinh == "CT Scanner" else 24 if loai_hinh == "MRI" else 12
            hen_tra = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
            
            conn = get_connection()
            if conn:
                try:
                    conn.execute("""INSERT INTO studies 
                        (ma_yeu_cau, ma_benh_nhan, ten_benh_nhan, loai_hinh_anh, bac_si_chi_dinh, ky_thuat_vien, thoi_gian_hen_tra)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                        (ma_yeu_cau.strip(), ma_bn, ten_bn, loai_hinh, bs_chi_dinh, ky_thuat_vien, hen_tra))
                    conn.commit()
                    conn.close()
                    st.success(f"Đã thêm yêu cầu {ma_yeu_cau} thành công!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Mã yêu cầu này đã tồn tại!")
                except Exception as e:
                    st.error(f"Lỗi: {e}")
            else:
                st.error("Database đang bận, vui lòng thử lại sau 5 giây.")

# Phần Danh sách, Cập nhật, Thống kê sẽ được bổ sung sau nếu cần. 
# Hiện tại ưu tiên fix lỗi thêm yêu cầu trước.

st.caption("Phiên bản sửa lỗi database locked - Streamlit Cloud")
