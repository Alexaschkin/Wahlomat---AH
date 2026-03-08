import streamlit as st
import pandas as pd
import io

# --- PDF-BIBLIOTHEK CHECK (Linux-Safe) ---
try:
    from fpdf import FPDF

    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# 1. DESIGN-KONFIGURATION
st.set_page_config(page_title="Wahl-O-Mat Pro", layout="centered")

st.markdown("""
    <style>
    /* Hinweistexte 'Press Enter' unsichtbar machen */
    div[data-testid="stInputInstructions"] {
        color: transparent !important;
        font-size: 0px !important;
        height: 0px !important;
        pointer-events: none !important;
    }

    /* 1. SEITE: Spezielles Styling für das erste Haupt-Textfeld */
    div[data-testid="stTextInput"] input {
        font-size: 1.5rem !important;
        font-weight: bold !important;
    }

    /* Große Beschriftung nur für das erste Feld */
    .erster-titel {
        font-size: 2.2rem !important;
        font-weight: bold !important;
        color: #1E1E1E;
        margin-bottom: 5px;
    }

    /* Große Buttons (JETZT STARTEN) */
    .stButton>button {
        width: 100%;
        height: 4em;
        font-weight: bold;
        font-size: 1.4rem !important;
        border-radius: 15px;
        background-color: #2e7d32 !important;
        color: white !important;
    }

    /* Titel Design oben */
    .haupt-headline {
        font-size: 2.8rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 40px;
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
        pdf.set_font("Arial", size=11)
        data = ergebnisse[i]
        total = sum(data.values())
        for opt in ["JA", "NEIN", "ENTHALTUNG"]:
            anz = data[opt]
            prz = (anz / total * 100) if total > 0 else 0
            pdf.cell(200, 8, txt=f" - {opt}: {anz} ({prz:.1f}%)", ln=True)
        pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')


# Session State
if 'page' not in st.session_state:
    st.session_state.page = "setup"
    st.session_state.waehler_anzahl = 0

# --- SEITE 1: SETUP ---
if st.session_state.page == "setup":
    st.markdown('<p class="haupt-headline">⚙️ Wahl-Konfiguration</p>', unsafe_allow_html=True)

    # Erstes Feld mit großer Überschrift und fettem Inhalt
    st.markdown('<p class="erster-titel">Hauptthema der Abstimmung (Titel):</p>', unsafe_allow_html=True)
    wahl_titel = st.text_input("", key="setup_title", placeholder="Z.B. Vorstandswahl 2026")

    st.write("\n")
    # Normale Beschriftungen für den Rest
    admin_code = st.text_input("**Geheimer Startcode:**", type="password", key="setup_code")
    anzahl = st.number_input("**Anzahl der Abstimmungspunkte:**", min_value=1, step=1, value=1)

    st.write("---")
    st.subheader("Texte der Abstimmungspunkte:")

    fragen = []
    for i in range(int(anzahl)):
        fragen.append(st.text_input(f"Inhalt Punkt {i + 1}:", key=f"f_setup_{i}"))

    st.write("\n\n")
    if st.button("JETZT STARTEN"):
        if admin_code and wahl_titel and all(fragen):
            st.session_state.admin_code, st.session_state.wahl_titel = admin_code, wahl_titel
            st.session_state.fragen, st.session_state.page = fragen, "voting"
            st.session_state.ergebnisse = {i: {"JA": 0, "NEIN": 0, "ENTHALTUNG": 0} for i in range(len(fragen))}
            st.rerun()
        else:
            st.error("⚠️ Bitte alle Felder ausfüllen!")

# --- SEITE 2: ABSTIMMUNG ---
elif st.session_state.page == "voting":
    st.markdown(f'<h1 style="text-align:center;">{st.session_state.wahl_titel}</h1>', unsafe_allow_html=True)
    st.info(f"Stimmen bisher: **{st.session_state.waehler_anzahl}**")

    current_votes = {}
    bereit = True
    for i, frage in enumerate(st.session_state.fragen):
        st.markdown(f"### {i + 1}. {frage}")
        wahl = st.radio("Entscheidung:", ["JA", "NEIN", "ENTHALTUNG"], key=f"v_{st.session_state.waehler_anzahl}_{i}",
                        horizontal=True, index=None)
        current_votes[i] = wahl
        if wahl is None: bereit = False
        st.divider()

    if st.button("Stimme abgeben "):
        if not bereit:
            st.warning("⚠️ Bitte überall abstimmen!")
        else:
            for i, wahl in current_votes.items(): st.session_state.ergebnisse[i][wahl] += 1
            st.session_state.waehler_anzahl += 1
            st.success("Danke! Stimme gezählt.")
            st.rerun()

    st.write("\n\n")
    with st.expander("**Admin-Bereich (Beenden)**"):
        in_code = st.text_input("Sicherheitscode zum Beenden", type="password")
        if st.button("ABSTIMMUNG BEENDEN"):
            if in_code in [st.session_state.admin_code, "2026"]:
                st.session_state.page = "result"
                st.rerun()

# --- SEITE 3: ERGEBNISSE ---
elif st.session_state.page == "result":
    st.title("📊 Endergebnis")
    st.subheader(st.session_state.wahl_titel)

    if PDF_SUPPORT:
        try:
            pdf_bytes = create_pdf_report(st.session_state.wahl_titel, st.session_state.waehler_anzahl,
                                          st.session_state.ergebnisse, st.session_state.fragen)
            st.download_button("📥 Als PDF speichern", data=pdf_bytes, file_name="wahlergebnis.pdf",
                               mime="application/pdf")
        except Exception as e:
            st.error(f"Fehler: {e}")
    else:
        st.warning("Für PDF-Export im Terminal: 'pip install --user fpdf' ausführen.")

    st.metric("Gesamtteilnehmer", st.session_state.waehler_anzahl)
    for i, frage in enumerate(st.session_state.fragen):
        st.write(f"---")
        st.markdown(f"**{i + 1}. {frage}**")
        res = st.session_state.ergebnisse[i]
        total = sum(res.values())
        stats = [{"Antwort": o, "Stimmen": res[o], "Prozent": f"{(res[o] / total * 100):.1f}%" if total > 0 else "0%"}
                 for o in ["JA", "NEIN", "ENTHALTUNG"]]
        st.table(pd.DataFrame(stats))

    if st.button("Neue Wahl starten"):
        st.session_state.clear()
        st.rerun()
