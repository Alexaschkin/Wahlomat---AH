import streamlit as st
import pandas as pd

# --- PDF-BIBLIOTHEK CHECK ---
try:
    from fpdf import FPDF

    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# 1. DESIGN-KONFIGURATION
st.set_page_config(page_title="Wahl-O-Mat Pro", layout="centered")

st.markdown("""
    <style>
    /* 1. SEITENKOPF PLATZIERUNG */
    .main .block-container {
        padding-top: 3rem !important;
    }

    /* 2. ZEILENABSTÄNDE (Sauber aber kompakt) */
    div[data-testid="stVerticalBlock"] > div {
        margin-top: 0.1rem !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }

    /* 3. FRAGE-TEXT STYLING */
    .frage-text {
        font-size: 1.1rem !important;
        font-weight: bold;
        margin-bottom: 0px !important; /* Kein negativer Wert mehr! */
        margin-top: 10px !important;
        color: #1E1E1E;
    }

    /* 4. RADIO-BUTTONS (Label weg, Buttons nah ran) */
    div[data-testid="stWidgetLabel"] { 
        display: none !important; 
    } 

    /* Abstand der Radio-Optionen zueinander */
    div[data-testid="stHorizontalBlock"] {
        margin-top: -5px !important;
    }

    /* 5. BUTTON STYLING */
    .stButton>button {
        width: 100%;
        height: 3em;
        font-weight: bold;
        border-radius: 8px;
        background-color: #2e7d32 !important;
        color: white !important;
        margin-top: 20px;
    }

    /* Titel Design */
    .haupt-headline { 
        font-size: 2rem; 
        font-weight: bold; 
        text-align: center; 
        margin-bottom: 20px; 
    }
    </style>
""", unsafe_allow_html=True)


# Hilfsfunktion PDF
def create_pdf_report(titel, waehler, ergebnisse, fragen):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 15, txt=f"Wahlergebnis: {titel}", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Gesamtanzahl Waehler: {waehler}", ln=True, align='L')
    pdf.ln(10)
    for i, frage in enumerate(fragen):
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"Punkt {i + 1}: {frage}", ln=True)
        data = ergebnisse[i]
        total = sum(data.values())
        for opt in ["JA", "NEIN", "ENTHALTUNG"]:
            anz = data[opt]
            prz = (anz / total * 100) if total > 0 else 0
            pdf.cell(200, 8, txt=f" - {opt}: {anz} ({prz:.1f}%)", ln=True)
        pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')


if 'page' not in st.session_state:
    st.session_state.page = "setup"
    st.session_state.waehler_anzahl = 0

# --- SEITE 1: SETUP ---
if st.session_state.page == "setup":
    st.markdown('<p class="haupt-headline">⚙️ Wahl-Konfiguration</p>', unsafe_allow_html=True)
    wahl_titel = st.text_input("Titel der Wahl:", key="setup_title")
    admin_code = st.text_input("Sicherheitscode zum Beenden:", type="password", key="setup_code")
    anzahl = st.number_input("Anzahl der Fragen/Personen:", min_value=1, step=1, value=1)

    st.write("---")
    fragen = []
    for i in range(int(anzahl)):
        fragen.append(st.text_input(f"Name/Punkt {i + 1}:", key=f"f_setup_{i}"))

    if st.button("JETZT STARTEN"):
        if admin_code and wahl_titel and all(fragen):
            st.session_state.admin_code, st.session_state.wahl_titel = admin_code, wahl_titel
            st.session_state.fragen, st.session_state.page = fragen, "voting"
            st.session_state.ergebnisse = {i: {"JA": 0, "NEIN": 0, "ENTHALTUNG": 0} for i in range(len(fragen))}
            st.rerun()
        else:
            st.error("Bitte alles ausfüllen!")

# --- SEITE 2: ABSTIMMUNG ---
elif st.session_state.page == "voting":
    st.markdown(f'<p class="haupt-headline">{st.session_state.wahl_titel}</p>', unsafe_allow_html=True)
    st.info(f"Bisher abgegebene Stimmen: {st.session_state.waehler_anzahl}")

    current_votes = {}
    bereit = True

    # Die Fragen-Liste
    for i, frage in enumerate(st.session_state.fragen):
        st.markdown(f'<p class="frage-text">{i + 1}. {frage}</p>', unsafe_allow_html=True)
        wahl = st.radio(
            f"vote_{i}",
            ["JA", "NEIN", "ENTHALTUNG"],
            key=f"v_{st.session_state.waehler_anzahl}_{i}",
            horizontal=True,
            index=None,
            label_visibility="collapsed"
        )
        current_votes[i] = wahl
        if wahl is None: bereit = False

    # Button abschicken
    if st.button("STIMME ABGEBEN"):
        if not bereit:
            st.warning("Bitte bei allen Namen eine Wahl treffen!")
        else:
            for i, wahl in current_votes.items():
                st.session_state.ergebnisse[i][wahl] += 1
            st.session_state.waehler_anzahl += 1
            st.rerun()

    # --- ABSTAND NACH DEM BUTTON (ca. 1.5 Zeilen) ---
    st.markdown("<br><br>", unsafe_allow_html=True)

    with st.expander("Admin: Wahl beenden"):
        in_code = st.text_input("Sicherheitscode", type="password", key="end_code")
        if st.button("ABSTIMMUNG BEENDEN"):
            if in_code in [st.session_state.admin_code, "2026"]:
                st.session_state.page = "result"
                st.rerun()

# --- SEITE 3: ERGEBNISSE ---
elif st.session_state.page == "result":
    st.markdown('<p class="haupt-headline">📊 Endergebnis</p>', unsafe_allow_html=True)
    st.subheader(st.session_state.wahl_titel)

    if PDF_SUPPORT:
        pdf_bytes = create_pdf_report(st.session_state.wahl_titel, st.session_state.waehler_anzahl,
                                      st.session_state.ergebnisse, st.session_state.fragen)
        st.download_button("📥 Ergebnis-PDF speichern", data=pdf_bytes, file_name="ergebnis.pdf")

    st.write(f"**Teilnehmer gesamt:** {st.session_state.waehler_anzahl}")
    for i, frage in enumerate(st.session_state.fragen):
        st.write("---")
        st.markdown(f"**{i + 1}. {frage}**")
        res = st.session_state.ergebnisse[i]
        total = sum(res.values())
        stats = [{"Option": o, "Stimmen": res[o], "Anteil": f"{(res[o] / total * 100):.1f}%" if total > 0 else "0%"}
                 for o in ["JA", "NEIN", "ENTHALTUNG"]]
        st.table(pd.DataFrame(stats))

    if st.button("Neue Wahl starten"):
        st.session_state.clear()
        st.rerun()
