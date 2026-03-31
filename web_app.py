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

    /* Versteckt nur die Gruppen-Überschriften, NICHT die Radio-Optionen selbst */
    div[data-testid="stRadio"] > label { display: none !important; }
    div[data-testid="stTextInput"] > label { display: none !important; }
    div[data-testid="stNumberInput"] > label { display: none !important; }

    /* Entfernt die Plus-Minus Buttons bei Number-Inputs */
    button.step-up, button.step-down { display: none !important; }
    div[data-testid="stNumberInput"] div[data-baseweb="input"] {
        padding-right: 0px !important;
    }

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


# Hilfsfunktion PDF
def create_pdf_report(titel, waehler, ergebnisse, fragen, mit_mea, gesamt_mea):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 15, txt=f"Ergebnis: {titel}", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Teilnehmer: {waehler}", ln=True, align='L')
    if mit_mea:
        pdf.cell(200, 10, txt=f"Gesamt-MEA: {gesamt_mea:.3f}", ln=True, align='L')
    pdf.ln(5)

    for i, frage in enumerate(fragen):
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(200, 8, txt=f"{i + 1}. {frage}", ln=True)

        res = ergebnisse[i]
        total_stimmen = len(res["JA"]) + len(res["NEIN"]) + len(res["ENTHALTUNG"])

        # Kopfstimmen Zeile
        count_ja, count_nein, count_enth = len(res["JA"]), len(res["NEIN"]), len(res["ENTHALTUNG"])
        p_ja = f"({(count_ja / total_stimmen * 100):.0f}%)" if total_stimmen > 0 else "(0%)"
        p_nein = f"({(count_nein / total_stimmen * 100):.0f}%)" if total_stimmen > 0 else "(0%)"
        p_enth = f"({(count_enth / total_stimmen * 100):.0f}%)" if total_stimmen > 0 else "(0%)"

        line = f"Stimmen - JA: {count_ja} {p_ja} | NEIN: {count_nein} {p_nein} | ENTH: {count_enth} {p_enth}"
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 6, txt=line, ln=True)

        # MEA Zeile
        if mit_mea:
            sum_ja, sum_nein, sum_enth = sum(res["JA"]), sum(res["NEIN"]), sum(res["ENTHALTUNG"])
            total_mea_abstimmung = sum_ja + sum_nein + sum_enth
            p_mea_ja = f"({(sum_ja / total_mea_abstimmung * 100):.1f}%)" if total_mea_abstimmung > 0 else "(0%)"
            p_mea_nein = f"({(sum_nein / total_mea_abstimmung * 100):.1f}%)" if total_mea_abstimmung > 0 else "(0%)"
            p_mea_enth = f"({(sum_enth / total_mea_abstimmung * 100):.1f}%)" if total_mea_abstimmung > 0 else "(0%)"

            mea_line = f"MEA - JA: {sum_ja:.3f} {p_mea_ja} | NEIN: {sum_nein:.3f} {p_mea_nein} | ENTH: {sum_enth:.3f} {p_mea_enth}"
            pdf.cell(200, 6, txt=mea_line, ln=True)

        pdf.ln(4)

    pdf_out = pdf.output(dest='S')
    if isinstance(pdf_out, str):
        return pdf_out.encode('latin-1')
    return bytes(pdf_out)


if 'page' not in st.session_state:
    st.session_state.page = "setup"
    st.session_state.waehler_anzahl = 0
    st.session_state.gesamt_mea_summe = 0.0

# --- SEITE 1: SETUP ---
if st.session_state.page == "setup":
    st.markdown('<p class="wahl-titel">⚙️ Konfiguration</p>', unsafe_allow_html=True)

    st.markdown('<p class="name-label">Titel der Wahl:</p>', unsafe_allow_html=True)
    wahl_titel = st.text_input("Titel", key="setup_title", placeholder="z.B. Eigentümerversammlung")

    st.markdown('<p class="name-label">Admin-Code:</p>', unsafe_allow_html=True)
    admin_code = st.text_input("Admin", type="password", key="setup_code")

    st.markdown('<p class="name-label">Anzahl der Punkte:</p>', unsafe_allow_html=True)
    anzahl = st.number_input("Anzahl", min_value=1, step=1, value=1)

    mit_mea = st.checkbox("Miteigentumsanteile (MEA) berücksichtigen?", value=False)

    st.write("---")
    st.markdown("### **Abstimmung zu:**")
    fragen = []
    for i in range(int(anzahl)):
        fragen.append(st.text_input(f"Punkt {i + 1}", key=f"f_setup_{i}", placeholder=f"Thema für Punkt {i + 1}"))

    if st.button("WAHL STARTEN"):
        if admin_code and wahl_titel and all(fragen):
            st.session_state.admin_code, st.session_state.wahl_titel = admin_code, wahl_titel
            st.session_state.fragen, st.session_state.mit_mea = fragen, mit_mea
            st.session_state.page = "voting"
            st.session_state.ergebnisse = {i: {"JA": [], "NEIN": [], "ENTHALTUNG": []} for i in range(len(fragen))}
            st.rerun()
        else:
            st.error("Bitte alle Felder ausfüllen!")

# --- SEITE 2: ABSTIMMUNG ---
elif st.session_state.page == "voting":
    st.markdown(f'<p class="wahl-titel">{st.session_state.wahl_titel}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-info">Wähler bisher: {st.session_state.waehler_anzahl}</p>', unsafe_allow_html=True)

    current_mea = 1.0
    if st.session_state.mit_mea:
        st.markdown('<p class="name-label">Eigentumsanteil für diese Stimme:</p>', unsafe_allow_html=True)
        # MEA Feld ohne +/- Buttons
        current_mea = st.number_input("MEA", min_value=0.0, value=1.0, step=0.001, format="%.3f",
                                      key=f"mea_{st.session_state.waehler_anzahl}")
        st.write("---")

    current_votes = {}
    bereit = True

    for i, frage in enumerate(st.session_state.fragen):
        st.markdown(f'<p class="name-label">{i + 1}. {frage}</p>', unsafe_allow_html=True)
        # Die Radio-Buttons sind jetzt wieder beschriftet sichtbar
        wahl = st.radio(f"v_{i}", ["JA", "NEIN", "ENTHALTUNG"],
                        key=f"v_{st.session_state.waehler_anzahl}_{i}",
                        horizontal=True, index=None)
        current_votes[i] = wahl
        if wahl is None: bereit = False
        st.markdown('<div style="border-bottom: 1px solid #eee; margin-bottom: 10px;"></div>', unsafe_allow_html=True)

    if st.button("STIMME ABGEBEN"):
        if not bereit:
            st.warning("⚠️ Bitte überall eine Auswahl treffen!")
        else:
            for i, wahl in current_votes.items():
                st.session_state.ergebnisse[i][wahl].append(current_mea)
            st.session_state.waehler_anzahl += 1
            st.session_state.gesamt_mea_summe += current_mea
            st.success("Gezählt!")
            st.rerun()

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
                                      st.session_state.ergebnisse, st.session_state.fragen,
                                      st.session_state.mit_mea, st.session_state.gesamt_mea_summe)
        st.download_button("📥 PDF Export", data=pdf_bytes, file_name="ergebnis.pdf", mime="application/pdf")

    st.write(f"**Teilnehmer (Köpfe):** {st.session_state.waehler_anzahl}")
    if st.session_state.mit_mea:
        st.write(f"**Gesamtsumme aller Anteile (MEA):** {st.session_state.gesamt_mea_summe:.3f}")

    for i, frage in enumerate(st.session_state.fragen):
        st.write("---")
        st.markdown(f"**{i + 1}. {frage}**")
        res = st.session_state.ergebnisse[i]

        data = []
        for opt in ["JA", "NEIN", "ENTHALTUNG"]:
            row = {"Option": opt, "Stimmen": len(res[opt])}
            if st.session_state.mit_mea:
                row["MEA Summe"] = round(sum(res[opt]), 3)
            data.append(row)

        st.table(pd.DataFrame(data))

    if st.button("Neue Wahl"):
        st.session_state.clear()
        st.rerun()
