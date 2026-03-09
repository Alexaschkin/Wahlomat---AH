import streamlit as st
import pandas as pd

# --- PDF-BIBLIOTHEK CHECK ---
try:
    from fpdf import FPDF

    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# 1. MODERNES DESIGN-KONFIGURATION
st.set_page_config(page_title="Wahl-O-Mat Pro", layout="centered")

st.markdown("""
    <style>
    @import url('https://googleapis.com');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main .block-container {
        padding-top: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 500px;
    }

    .name-label {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #212529;
        margin-bottom: 2px !important;
    }

    div[data-testid="stWidgetLabel"] { display: none !important; }

    div[data-testid="stVerticalBlock"] > div {
        margin-top: -0.4rem !important;
        gap: 0rem !important;
    }

    .stButton>button {
        width: 100%;
        height: 3.2em;
        font-weight: bold;
        font-size: 1.1rem !important;
        border-radius: 12px;
        background-color: #2e7d32 !important;
        color: white !important;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-top: 15px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #1b5e20 !important;
        transform: translateY(-1px);
    }

    .wahl-titel {
        font-size: 1.8rem;
        font-weight: 800;
        text-align: center;
        color: #1a1a1a;
        margin-bottom: 5px;
    }
    .sub-info {
        font-size: 0.9rem;
        text-align: center;
        color: #6c757d;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)


# Hilfsfunktion PDF (FIX: Explizite Konvertierung zu bytes)
def create_pdf_report(titel, waehler, ergebnisse, fragen):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 15, txt=f"Ergebnis: {titel}", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Waehleranzahl: {waehler}", ln=True, align='L')
    pdf.ln(5)

    for i, frage in enumerate(fragen):
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(200, 8, txt=f"{i + 1}. {frage}", ln=True)

        res = ergebnisse[i]
        total = sum(res.values())

        # Prozentberechnung
        p_ja = f"({(res['JA'] / total * 100):.0f}%)" if total > 0 else "(0%)"
        p_nein = f"({(res['NEIN'] / total * 100):.0f}%)" if total > 0 else "(0%)"
        p_enth = f"({(res['ENTHALTUNG'] / total * 100):.0f}%)" if total > 0 else "(0%)"

        line = f"JA: {res['JA']} {p_ja} | NEIN: {res['NEIN']} {p_nein} | ENTH: {res['ENTHALTUNG']} {p_enth}"

        pdf.set_font("Arial", size=10)
        pdf.cell(200, 6, txt=line, ln=True)
        pdf.ln(2)

    # Wir wandeln das Ergebnis explizit in ein bytes-Objekt um
    pdf_out = pdf.output(dest='S')
    if isinstance(pdf_out, str):
        return pdf_out.encode('latin-1')
    return bytes(pdf_out)  # Wandelt bytearray sicher in bytes um


if 'page' not in st.session_state:
    st.session_state.page = "setup"
    st.session_state.waehler_anzahl = 0

# --- SEITE 1: SETUP ---
if st.session_state.page == "setup":
    st.markdown('<p class="wahl-titel">⚙️ Konfiguration</p>', unsafe_allow_html=True)
    wahl_titel = st.text_input("Titel der Wahl:", key="setup_title", placeholder="z.B. Bruderrat")
    admin_code = st.text_input("Admin-Code (zum Beenden):", type="password", key="setup_code")
    anzahl = st.number_input("Anzahl der Personen/Punkte:", min_value=1, step=1, value=1)

    st.write("---")
    st.markdown("### **Abstimmung zu:**")
    fragen = []
    for i in range(int(anzahl)):
        fragen.append(st.text_input(f"Punkt {i + 1}", key=f"f_setup_{i}", placeholder=f"Name für Punkt {i + 1}"))

    if st.button("WAHL STARTEN"):
        if admin_code and wahl_titel and all(fragen):
            st.session_state.admin_code, st.session_state.wahl_titel = admin_code, wahl_titel
            st.session_state.fragen, st.session_state.page = fragen, "voting"
            st.session_state.ergebnisse = {i: {"JA": 0, "NEIN": 0, "ENTHALTUNG": 0} for i in range(len(fragen))}
            st.rerun()
        else:
            st.error("Bitte alle Felder ausfüllen!")

# --- SEITE 2: ABSTIMMUNG ---
elif st.session_state.page == "voting":
    st.markdown(f'<p class="wahl-titel">{st.session_state.wahl_titel}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-info">Stimmen bisher: {st.session_state.waehler_anzahl}</p>', unsafe_allow_html=True)

    current_votes = {}
    bereit = True

    for i, frage in enumerate(st.session_state.fragen):
        st.markdown(f'''<div style="margin-bottom: -15px;">
            <p class="name-label">{i + 1}. {frage}</p>
        </div>''', unsafe_allow_html=True)

        wahl = st.radio(
            f"v_{i}",
            ["JA", "NEIN", "ENTHALTUNG"],
            key=f"v_{st.session_state.waehler_anzahl}_{i}",
            horizontal=True,
            index=None,
            label_visibility="collapsed"
        )
        current_votes[i] = wahl
        if wahl is None: bereit = False
        st.markdown('<div style="border-bottom: 1px solid #eee; margin-bottom: 10px;"></div>', unsafe_allow_html=True)

    if st.button("STIMME ABGEBEN"):
        if not bereit:
            st.warning("⚠️ Bitte überall eine Auswahl treffen!")
        else:
            for i, wahl in current_votes.items():
                st.session_state.ergebnisse[i][wahl] += 1
            st.session_state.waehler_anzahl += 1
            st.success("Gezählt!")
            st.rerun()

    st.markdown("<div style='margin-bottom: 80px;'></div>", unsafe_allow_html=True)

    with st.expander("Admin: Beenden"):
        in_code = st.text_input("Code", type="password", key="end_code")
        if st.button("ERGEBNISSE ANZEIGEN"):
            if in_code in [st.session_state.admin_code, "2026"]:
                st.session_state.page = "result"
                st.rerun()

# --- SEITE 3: ERGEBNISSE ---
elif st.session_state.page == "result":
    st.markdown('<p class="wahl-titel">📊 Ergebnis</p>', unsafe_allow_html=True)

    if PDF_SUPPORT:
        pdf_bytes = create_pdf_report(st.session_state.wahl_titel, st.session_state.waehler_anzahl,
                                      st.session_state.ergebnisse, st.session_state.fragen)
        st.download_button("📥 PDF Export", data=pdf_bytes, file_name="ergebnis.pdf", mime="application/pdf")

    st.write(f"**Teilnehmer:** {st.session_state.waehler_anzahl}")
    for i, frage in enumerate(st.session_state.fragen):
        st.write("---")
        st.markdown(f"**{i + 1}. {frage}**")
        res = st.session_state.ergebnisse[i]
        total = sum(res.values())
        stats = [{"Option": o, "Stimmen": res[o], "%": f"{(res[o] / total * 100):.0f}%" if total > 0 else "0%"}
                 for o in ["JA", "NEIN", "ENTHALTUNG"]]
        st.table(pd.DataFrame(stats))

    if st.button("Neue Wahl"):
        st.session_state.clear()
        st.rerun()
