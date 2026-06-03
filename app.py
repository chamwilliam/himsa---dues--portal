import streamlit as st
import sqlite3
import pandas as pd
import datetime
import io
import os
import urllib.parse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import base64

# Function to load the image and turn it into a web-readable format
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Try loading your uploaded logo file
try:
    img_base64 = get_base64_image("IMG-20260514-WA0105.jpg")
    
    # Injecting custom styling to place the logo behind everything safely
    watermark_css = f"""
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.90), rgba(255, 255, 255, 0.90)), 
                          url("data:image/jpg;base64,{img_base64}");
        background-size: 650px;
        background-repeat: no-repeat;
        background-position: center 55%;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(watermark_css, unsafe_allow_html=True)
except FileNotFoundError:
    pass  # Keeps the app running normally if the image is missing
# Create local system folder to physically back up PDF receipt records
RECEIPTS_DIR = "HIMSA_Receipts"
if not os.path.exists(RECEIPTS_DIR):
    os.makedirs(RECEIPTS_DIR)

# --- SYSTEM ENGINE DATABASE INITIALIZATION ---
def init_clean_database():
    conn = sqlite3.connect('himsa_dues.db')
    cursor = conn.cursor()
    
    # 1. Accounts & Core Membership Registry Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        index_number TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        role TEXT DEFAULT 'student',
        password TEXT NOT NULL
    )''')
    
    # 2. Dynamic Tariff Settings Structure Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dues_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        academic_year TEXT NOT NULL,
        level INTEGER NOT NULL,
        amount REAL NOT NULL,
        UNIQUE(academic_year, level)
    )''')
    
    # 3. Secure Financial Audit Ledger Payments Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        index_number TEXT,
        amount_paid REAL NOT NULL,
        payment_method TEXT NOT NULL,
        transaction_id TEXT UNIQUE NOT NULL,
        academic_year TEXT NOT NULL,
        payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(index_number) REFERENCES users(index_number)
    )''')
    
    # Secure Core Financial Secretary Master Executive Profile
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO users (index_number, name, role, password) 
            VALUES ('ADMIN001', 'Financial Secretary', 'admin', 'admin123')
        """)
        
    # Auto-seed dynamic matrix tables across all academic years
    cursor.execute("SELECT COUNT(*) FROM dues_config")
    if cursor.fetchone()[0] == 0:
        start_year = 2023
        for i in range(20): 
            year_str = f"{start_year + i}/{start_year + i + 1}"
            # Seed distinctive baseline prices across all valid level milestones
            cursor.execute("INSERT OR IGNORE INTO dues_config (academic_year, level, amount) VALUES (?, 100, 300.00)", (year_str,))
            cursor.execute("INSERT OR IGNORE INTO dues_config (academic_year, level, amount) VALUES (?, 200, 90.00)", (year_str,))
            cursor.execute("INSERT OR IGNORE INTO dues_config (academic_year, level, amount) VALUES (?, 300, 90.00)", (year_str,))
            cursor.execute("INSERT OR IGNORE INTO dues_config (academic_year, level, amount) VALUES (?, 400, 120.00)", (year_str,))
            
    # --- AUTO-SEED DISABLE DISPATCH ---
    # Demo students removed to ensure a permanent empty database for your launch next semester.
    pass
            
    conn.commit()
    conn.close()

init_clean_database()

# --- FIXED EXPLICIT COHORT LEVEL TIMELINE MAPPING ---
def calculate_student_level(index_number, selected_year_string):
    # Enforces your precise custom milestone timeline rules directly
    if selected_year_string == "2023/2024":
        return 400
    elif selected_year_string == "2024/2025":
        return 300
    elif selected_year_string == "2025/2026":
        return 200
    elif selected_year_string == "2026/2027":
        return 100
    
    # Dynamic fallback calculation logic for future entries past 2027
    try:
        start_year_selected = int(selected_year_string.split('/')[0])
        parts = index_number.split('/')
        if len(parts) >= 4:
            cohort_year = int(parts[2])
            elapsed = start_year_selected - (2000 + cohort_year)
            calculated_level = 400 - (elapsed * 100)
            if calculated_level in [100, 200, 300, 400]:
                return calculated_level
    except:
        pass
    return 100

# --- INTELLECTUAL PDF RECEIPT BUILDER (ReportLab Engine) ---
def generate_receipt_pdf(student_name, index_number, level, amount, tx_id, year, method, save_to_disk=False):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=colors.HexColor('#0f766e'), alignment=1)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#475569'), alignment=1)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, leading=16, textColor=colors.HexColor('#334155'))
    
    story.append(Paragraph("HEALTH INFORMATION MANAGEMENT STUDENTS ASSOCIATION (HIMSA)", title_style))
    story.append(Paragraph("University of Cape Coast (UCC), Ghana", sub_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<font color='#0f766e'><b>OFFICIAL FINANCIAL RECEIPT</b></font>", ParagraphStyle('ReceiptTitle', parent=title_style, fontSize=14, alignment=1)))
    story.append(Spacer(1, 20))
    
    data = [
        [Paragraph("<b>Transaction Reference:</b>", body_style), Paragraph(str(tx_id), body_style)],
        [Paragraph("<b>Academic Session:</b>", body_style), Paragraph(str(year), body_style)],
        [Paragraph("<b>Date of Payment:</b>", body_style), Paragraph(datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), body_style)],
        [Paragraph("<b>Student Full Name:</b>", body_style), Paragraph(str(student_name), body_style)],
        [Paragraph("<b>Index Number:</b>", body_style), Paragraph(str(index_number), body_style)],
        [Paragraph("<b>Calculated Status:</b>", body_style), Paragraph(f"Level {level}", body_style)],
        [Paragraph("<b>Payment Method:</b>", body_style), Paragraph(str(method), body_style)],
        [Paragraph("<b>Total Amount Paid:</b>", body_style), Paragraph(f"<b>GH₵ {amount:,.2f}</b>", body_style)]
    ]
    
    t = Table(data, colWidths=[200, 300])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#ccfbf1')),
    ]))
    story.append(t)
    story.append(Spacer(1, 40))
    
    story.append(Paragraph("...........................................................", ParagraphStyle('Line', parent=body_style, alignment=2)))
    story.append(Paragraph("<b>William Cham</b><br/>HIMSA Financial Secretary", ParagraphStyle('Sign', parent=body_style, alignment=2)))
    
    doc.build(story)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    
    if save_to_disk:
        file_path = os.path.join(RECEIPTS_DIR, f"HIMSA_Receipt_{tx_id}.pdf")
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
            
    return io.BytesIO(pdf_bytes)

# --- USER INTERFACE PRESET CUSTOMIZATION ---
st.set_page_config(page_title="HIMSA Portal", page_icon="🛡️", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    h1, h2, h3 { color: #0f766e !important; }
    .stButton>button { background-color: #0f766e; color: white; border-radius: 6px; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #115e59; }
    </style>
""", unsafe_allow_html=True)

def get_db_connection():
    return sqlite3.connect('himsa_dues.db')

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

st.title("🛡️ HIMSA Financial Strategy & Dues Portal")
st.caption("Health Information Management Students Association")
st.markdown("---")

start_year = 2023
academic_years_list = [f"{start_year + i}/{start_year + i + 1}" for i in range(20)]
active_session_year = st.sidebar.selectbox("📆 Current Academic Year Session", academic_years_list)

# --- GATEKEEPER SIGN-IN PORTAL ---
if not st.session_state.logged_in:
    st.subheader("🔒 Gatekeepers Security Sign-In")
    username = st.text_input("Index Number / Administration Code").strip()
    password = st.text_input("Security Access Password", type="password")
    
    if st.button("Authenticate Identity Session"):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT index_number, name, role FROM users WHERE index_number=? AND password=?", (username, password))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            st.session_state.logged_in = True
            st.session_state.user = {"index": user_data[0], "name": user_data[1], "role": user_data[2]}
            st.rerun()
        else:
            st.error("Invalid credentials. Verify your index number structure or password credentials.")
else:
    user = st.session_state.user
    
    # Dynamic level calculation parsing
    computed_level = calculate_student_level(user['index'], active_session_year) if user['role'] == 'student' else 400
    
    conn = get_db_connection()
    dues_rules = pd.read_sql_query("SELECT level, amount FROM dues_config WHERE academic_year=?", conn, params=(active_session_year,)).set_index('level')['amount'].to_dict()
    conn.close()
    
    st.sidebar.markdown(f"### Active: **{user['name']}**")
    st.sidebar.markdown(f"**Role:** `{user['role'].upper()}`")
    
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    # --- EXECUTIVE ADMINISTRATIVE SYSTEM PANELS ---
    if user['role'] == 'admin':
        st.subheader(f"📈 Executive Management Controls ({active_session_year})")
        
        conn = get_db_connection()
        total_collected = pd.read_sql_query("SELECT SUM(amount_paid) as total FROM payments WHERE academic_year=?", conn, params=(active_session_year,))['total'].iloc[0] or 0.0
        raw_students = pd.read_sql_query("SELECT index_number FROM users WHERE role='student'", conn)
        conn.close()
        
        m1, m2 = st.columns(2)
        m1.metric("Total Vault Balance", f"GH₵ {total_collected:,.2f}")
        m2.metric("Enrolled Student Base", f"{len(raw_students)} Members")
        
        tab_remit, tab_register, tab_settings, tab_directory = st.tabs(["📝 Record Cash Remittance", "➕ Enroll New Student", "⚙️ Dynamic Tariff Adjuster", "📋 Directory Ledger"])
        
        with tab_remit:
            student_idx = st.text_input("Student Index Number (e.g. AH/HIM/24/0032)").strip()
            if student_idx:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM users WHERE index_number=?", (student_idx,))
                match = cursor.fetchone()
                conn.close()
                
                if match:
                    dyn_lvl = calculate_student_level(student_idx, active_session_year)
                    assigned_rate = dues_rules.get(dyn_lvl, 0.00)
                    st.info(f"Verified Student: **{match[0]}** (Level {dyn_lvl}) — Live Tariff: **GH₵ {assigned_rate:.2f}**")
                    
                    c1, c2 = st.columns(2)
                    dest_phone = c1.text_input("Student WhatsApp Number (with country code, e.g., 233244000000)", value="233")
                    dest_email = c2.text_input("Student Email Address", value="student@ucc.edu.gh")
                    
                    cash_amount = st.number_input("Counted Cash (GH₵)", min_value=0.0, value=float(assigned_rate))
                    
                    if st.button("Commit Cash to Ledger"):
                        tx_id = f"CSH-{int(datetime.datetime.now().timestamp())}"
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO payments (index_number, amount_paid, payment_method, transaction_id, academic_year) 
                            VALUES (?, ?, 'Cash Handover', ?, ?)
                        """, (student_idx, cash_amount, tx_id, active_session_year))
                        conn.commit()
                        conn.close()
                        
                        generate_receipt_pdf(match[0], student_idx, dyn_lvl, cash_amount, tx_id, active_session_year, "Cash Handover", save_to_disk=True)
                        
                        st.success(f"Successfully logged GH₵ {cash_amount:.2f} for {match[0]}!")
                        st.session_state['last_tx'] = {
                            "name": match[0], "idx": student_idx, "lvl": dyn_lvl, 
                            "amt": cash_amount, "txid": tx_id, "yr": active_session_year, 
                            "method": "Cash Handover", "phone": dest_phone, "email": dest_email
                        }
                        st.rerun()
                        
                    if 'last_tx' in st.session_state and st.session_state['last_tx']['idx'] == student_idx:
                        tx = st.session_state['last_tx']
                        
                        st.markdown("---")
                        st.markdown("### 📤 Dispatch Official PDF Receipt File")
                        st.caption(f"The PDF receipt document has been physically archived on your machine at: **`{RECEIPTS_DIR}/HIMSA_Receipt_{tx['txid']}.pdf`**")
                        
                        msg_body = (
                            f"🛡️ *HIMSA OFFICIAL FINANCIAL RECEIPTS*\n\n"
                            f"Hello *{tx['name']}*,\n"
                            f"Your payment of *GH₵ {tx['amt']:.2f}* has been processed successfully.\n"
                            f"Please find attached your official PDF receipt document.\n\n"
                            f"🧾 *Receipt ID Reference:* {tx['txid']}\n"
                            f"📆 *Session Year:* {tx['yr']}\n\n"
                            f"Issued by William Cham\n_Financial Secretary, HIMSA UCC_"
                        )
                        
                        encoded_msg = urllib.parse.quote(msg_body)
                        whatsapp_url = f"https://wa.me/{tx['phone']}?text={encoded_msg}"
                        
                        encoded_subject = urllib.parse.quote(f"HIMSA PDF Dues Receipt: {tx['txid']}")
                        encoded_email_body = urllib.parse.quote(msg_body.replace('*', ''))
                        email_url = f"mailto:{tx['email']}?subject={encoded_subject}&body={encoded_email_body}"
                        
                        sh1, sh2, sh3 = st.columns(3)
                        
                        pdf_data = generate_receipt_pdf(tx['name'], tx['idx'], tx['lvl'], tx['amt'], tx['txid'], tx['yr'], tx['method'])
                        sh1.download_button(
                            label="📥 Download Copy to Laptop",
                            data=pdf_data,
                            file_name=f"HIMSA_Receipt_{tx['txid']}.pdf",
                            mime="application/pdf"
                        )
                        
                        sh2.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color:#25D366;color:white;border:none;padding:10px;border-radius:6px;font-weight:bold;width:100%;cursor:pointer;">📱 Attach PDF via WhatsApp</button></a>', unsafe_allow_html=True)
                        sh3.markdown(f'<a href="{email_url}"><button style="background-color:#EA4335;color:white;border:none;padding:10px;border-radius:6px;font-weight:bold;width:100%;cursor:pointer;">📧 Attach PDF via Email</button></a>', unsafe_allow_html=True)
                else:
                    st.warning("No registered profile matches this index number.")
                        
        with tab_register:
            new_idx = st.text_input("New Student Index Number (e.g. AH/HIM/24/XXXX)").strip()
            new_name = st.text_input("Full Legal Name")
            if st.button("Register Student Account"):
                if new_idx and new_name:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO users (index_number, name, role, password) VALUES (?, ?, 'student', 'password123')", (new_idx, new_name))
                        conn.commit()
                        conn.close()
                        st.success(f"Successfully Enrolled {new_name} inside registry database!")
                        st.rerun()
                    except:
                        st.error("This student index number sequence is already registered.")

        with tab_settings:
            st.markdown("### ⚙️ Update Dues Pricing Decisions On-The-Fly")
            col_lvl = st.selectbox("Select Target Class Level", [100, 200, 300, 400])
            current_configured_price = dues_rules.get(col_lvl, 0.00)
            st.warning(f"Current fee set for Level {col_lvl} in {active_session_year}: **GH₵ {current_configured_price:.2f}**")
            new_approved_price = st.number_input("Enter New Approved Amount (GH₵)", min_value=0.0, value=float(current_configured_price))
            
            if st.button("Save New Rate Decision"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO dues_config (academic_year, level, amount) 
                    VALUES (?, ?, ?)
                    ON CONFLICT(academic_year, level) 
                    DO UPDATE SET amount = excluded.amount
                """, (active_session_year, col_lvl, new_approved_price))
                conn.commit()
                conn.close()
                st.success(f"🎉 Approved! Level {col_lvl} baseline shifted to GH₵ {new_approved_price:.2f}!")
                st.rerun()

            # --- SYSTEM WIPE UTILITY ---
            st.markdown("---")
            st.markdown("### 🚨 Master Reset System Utilities")
            st.caption("Removes all transaction logs and completely purges member indexes back to zero.")
            confirm_code = st.text_input("Type 'RESET' to authorize clearing database history", placeholder="RESET")
            if st.button("💥 Execute Complete Ledger Wipe"):
                if confirm_code == "RESET":
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM payments") 
                    cursor.execute("DELETE FROM users WHERE role='student'") 
                    conn.commit()
                    conn.close()
                    if 'last_tx' in st.session_state:
                        del st.session_state['last_tx']
                    st.success("💥 System reset complete! Enrolled Student Base has been set back to 0.")
                    st.rerun()
    with tab_directory: 
        # 1. Keep your original payment transaction ledger layout at the top
        try:
            conn = get_db_connection()
            p_df = pd.read_sql_query("SELECT * FROM payments", conn)
            conn.close()
            st.subheader("💸 Global Payment Logs")
            st.dataframe(p_df, use_container_width=True)
        except Exception as e:
            st.error(f"Could not load payment logs: {e}")

        # 2. Add a visual separation divider
        st.write("---")
        st.subheader("📋 Filter Registered Members by Level")

        # The clean selector box on a single line completely avoids the multi-line typo trap
        selected_level = st.selectbox("Select Level to Display", ["Level 100", "Level 200", "Level 300", "Level 400"], key="directory_level_filter")

        # Convert selectbox text into your standard year format suffix patterns
        level_to_year = {
            "Level 100": "%/26/%",
            "Level 200": "%/25/%",
            "Level 300": "%/24/%",
            "Level 400": "%/23/%"
        }
        year_pattern = level_to_year.get(selected_level, "%/24/%")

        # Smart bypass: Select users based on their Index Number string structure instead of a missing column
        query = "SELECT name AS 'Full Legal Name', index_number AS 'Index Number' FROM users WHERE index_number LIKE ?"
        
        try:
            conn = get_db_connection()
            filtered_data = pd.read_sql_query(query, conn, params=(year_pattern,))
            conn.close()
            
            if not filtered_data.empty:
                st.dataframe(filtered_data, use_container_width=True)
                st.info(f"Total Count: {len(filtered_data)} students registered for this class tier.")
            else:
                st.warning(f"No student records found matching the {selected_level} criteria in the system.")
        except Exception as e:
            st.error(f"Could not filter records: {e}")
    # --- STUDENT DASHBOARD TERMINAL VIEW ---
    else:
        st.subheader(f"📋 Student Dashboard — Session: {active_session_year}")
        base_rate = dues_rules.get(computed_level, 0.00)
        
        conn = get_db_connection()
        user_sums_df = pd.read_sql_query("SELECT SUM(amount_paid) as paid FROM payments WHERE index_number=? AND academic_year=?", conn, params=(user['index'], active_session_year))
        total_user_paid = user_sums_df['paid'].iloc[0] or 0.0
        past_payments = pd.read_sql_query("SELECT transaction_id, amount_paid, payment_method, payment_date FROM payments WHERE index_number=? AND academic_year=?", conn, params=(user['index'], active_session_year)).to_dict('records')
        conn.close()
        
        remaining_balance = max(0.0, base_rate - total_user_paid)
        
        s1, s2 = st.columns(2)
        s1.metric(f"Assessment Rate (Level {computed_level})", f"GH₵ {base_rate:.2f}")
        s2.metric("Outstanding Balance Due", f"GH₵ {remaining_balance:.2f}")
        
        # --- MOBILE MONEY SECURE PAYMENT PORTAL ---
        st.markdown("---")
        if remaining_balance > 0:
            st.markdown("### 📱 Mobile Money Secure Payment Gateway")
            st.caption("Complete your association financial obligations securely through our simulated portal gateway.")
            
            p_col1, p_col2 = st.columns(2)
            momo_network = p_col1.selectbox("Select Network Wallet Provider", ["MTN Mobile Money", "Telecel Cash", "AT Money"])
            momo_phone = p_col2.text_input("Mobile Money Wallet Phone Number", placeholder="e.g., 0244123456")
            
            if st.button(f"⚡ Confirm and Authorize Payment of GH₵ {remaining_balance:.2f}"):
                if len(momo_phone.strip()) >= 10:
                    tx_ref = f"MOM-{int(datetime.datetime.now().timestamp())}"
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO payments (index_number, amount_paid, payment_method, transaction_id, academic_year) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (user['index'], remaining_balance, f"MoMo ({momo_network})", tx_ref, active_session_year))
                    conn.commit()
                    conn.close()
                    
                    generate_receipt_pdf(user['name'], user['index'], computed_level, remaining_balance, tx_ref, active_session_year, f"MoMo ({momo_network})", save_to_disk=True)
                    
                    st.success(f"🎉 Success! Payment processed via {momo_network}. Instantly generated official receipt file reference: {tx_ref}")
                    st.rerun()
                else:
                    st.error("Please enter a valid active mobile money telephone number structure to process transaction.")
        else:
            st.success(f"🎉 Financial Clearance Granted for the {active_session_year} academic year! No outstanding balances remain.")
            
        if past_payments:
            st.markdown("### 📥 Your Printable Digital Receipts")
            for pay in past_payments:
                col_info, col_btn = st.columns([3, 1])
                col_info.write(f"🧾 **Ref:** `{pay['transaction_id']}` | **Paid:** GH₵ {pay['amount_paid']:.2f} via {pay['payment_method']}")
                
                pdf_data = generate_receipt_pdf(user['name'], user['index'], computed_level, pay['amount_paid'], pay['transaction_id'], active_session_year, pay['payment_method'])
                col_btn.download_button(
                    label="Download PDF",
                    data=pdf_data,
                    file_name=f"HIMSA_Receipt_{pay['transaction_id']}.pdf",
                    mime="application/pdf",
                    key=pay['transaction_id']
                )
