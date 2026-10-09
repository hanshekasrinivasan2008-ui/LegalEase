from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, StreamingResponse
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from docx import Document as DocxDocument
from docx.shared import Pt

app = FastAPI()

# Memory to store last data
LAST_DATA = {}

HTML_TEMPLATE = """
<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LegalEase</title>
<style>
body{margin:0;font-family:Arial;background:#f8f9ff}
.header{background:#111C44;color:white;padding:18px 30px}
.notice{background:#fef9c3;padding:12px;margin:15px;border-radius:6px;font-size:13px}
.grid{display:flex;gap:20px;padding:20px}
.card{background:white;padding:20px;border-radius:12px;width:50%;border:1px solid #ddd}
input,select,textarea{width:100%;padding:8px;margin:5px 0 12px 0;border:1px solid #ccc;border-radius:6px}
.btn{background:#111C44;color:white;padding:10px 15px;border:none;border-radius:6px;cursor:pointer;width:100%}
.small{padding:6px 10px;width:auto;margin-left:5px}
table{width:100%;border-collapse:collapse;margin-top:10px}
th,td{border:1px solid #ddd;padding:8px;text-align:left;font-size:13px}
th{background:#f1f5f9}
</style>
</head><body>
<div class="header"><h2 style="margin:0">⚖️ LegalEase</h2><p style="margin:0;color:#94a3b8">AI-Powered Legal Document Generator</p></div>
<div class="notice"><b>Important:</b> LegalEase creates AI-assisted drafts. It is not a law firm.</div>
<div class="grid">
<div class="card">
<h3>1. Document Details</h3>
<form method="post" action="/generate">
<label>Document Type</label><select name="doc_type"><option>Employment Contract</option><option>NDA</option><option>Rental Agreement</option></select>
<div style="display:flex;gap:10px"><div style="width:50%"><label>Party A</label><input name="party_a" value="ABC Technologies Pvt Ltd"></div><div style="width:50%"><label>Party B</label><input name="party_b" value="Tarunprakash J"></div></div>
<label>Effective Date</label><input type="date" name="eff_date" value="2026-09-01">
<label>Role</label><input name="role" value="Software Developer">
<label>Compensation</label><input name="comp" value="₹40,000 per month">
<label>Key Terms</label><textarea name="key_terms">Notice period: 30 days. Working hours: Monday to Friday, 9:30 AM to 6:00 PM. Employee must maintain confidentiality.</textarea>
<label>Company / Brand Name</label><input name="company" value="ABC Technologies Pvt Ltd">
<label>Custom Instructions</label><textarea name="custom">Include clauses for job responsibilities, confidentiality, leave, notice period and termination</textarea>
<button class="btn" type="submit">✨ Generate Document</button>
</form>
</div>
<div class="card">
<div style="display:flex;justify-content:space-between;align-items:center"><h3>2. Editable Preview</h3><div><a href="/download/pdf"><button class="btn small">PDF</button></a><a href="/download/docx"><button class="btn small">DOCX</button></a><a href="/download/txt"><button class="btn small">TXT</button></a></div></div>
<textarea style="height:350px">__DOC__</textarea>
<h4>Automatic Term Table</h4><table><tr><th>Term</th><th>Value</th></tr>__TABLE__</table>
</div></div></body></html>
"""

def build_doc_text(data):
    return f"""{data['company']} - {data['doc_type'].upper()}

This {data['doc_type']} is made between {data['party_a']} (Party A) and {data['party_b']} (Party B) effective from {data['eff_date']}.

1. POSITION & RESPONSIBILITIES
Employee will serve as {data['role']}.

2. COMPENSATION
{data['comp']}

3. KEY TERMS
{data['key_terms']}

4. CUSTOM INSTRUCTIONS
{data['custom']}

5. CONFIDENTIALITY, TERM & GOVERNING LAW
Employee agrees to maintain confidentiality. This agreement is governed by Indian law.

For {data['company']}
Employer Signature: ___________________

{data['party_b']}
Employee Signature: ___________________

AI-assisted draft — professional legal review recommended before signing.
"""

def get_table_data(data):
    return [
        ["Document Type", data['doc_type']],
        ["Party A", data['party_a']],
        ["Party B", data['party_b']],
        ["Effective Date", data['eff_date']],
        ["Role", data['role']],
        ["Compensation", data['comp']],
        ["Key Terms", data['key_terms']],
    ]

@app.get("/", response_class=HTMLResponse)
def home():
    data = LAST_DATA if LAST_DATA else {'doc_type':'-','party_a':'-','party_b':'-','eff_date':'-','role':'-','comp':'-','key_terms':'-','company':'LegalEase','custom':''}
    doc_text = build_doc_text(data) if LAST_DATA else "Your generated document will appear here... Click Generate"
    table_rows = "".join([f"<tr><td>{k}</td><td>{v}</td></tr>" for k,v in get_table_data(data)]) if LAST_DATA else "<tr><td colspan=2>Generate a document to enable exports.</td></tr>"
    return HTML_TEMPLATE.replace("__DOC__", doc_text).replace("__TABLE__", table_rows)

@app.post("/generate", response_class=HTMLResponse)
def generate(doc_type: str = Form(...), party_a: str = Form(...), party_b: str = Form(...), eff_date: str = Form(...), role: str = Form(...), comp: str = Form(...), key_terms: str = Form(...), company: str = Form(...), custom: str = Form(...)):
    global LAST_DATA
    LAST_DATA = {'doc_type':doc_type,'party_a':party_a,'party_b':party_b,'eff_date':eff_date,'role':role,'comp':comp,'key_terms':key_terms,'company':company,'custom':custom}
    return home()

@app.get("/download/pdf")
def download_pdf():
    if not LAST_DATA: return home()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []
    # Title
    for line in build_doc_text(LAST_DATA).split('\n'):
        story.append(Paragraph(line if line.strip() else "<br/>", styles['Normal']))
        story.append(Spacer(1, 6))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Key Terms</b>", styles['Heading2']))
    story.append(Spacer(1, 8))
    # Table like in video
    table_data = [["Term","Value"]] + get_table_data(LAST_DATA)
    t = Table(table_data, colWidths=[120, 380])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))
    story.append(Paragraph("AI-assisted draft — professional legal review recommended before signing.", styles['Italic']))
    doc.build(story)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition":"attachment; filename=LegalEase_Document.pdf"})

@app.get("/download/docx")
def download_docx():
    if not LAST_DATA: return home()
    buf = io.BytesIO()
    d = DocxDocument()
    for line in build_doc_text(LAST_DATA).split('\n'):
        d.add_paragraph(line)
    d.add_paragraph("")
    d.add_heading("Key Terms", level=2)
    table = d.add_table(rows=1, cols=2)
    table.style = 'Light Shading'
    hdr = table.rows[0].cells
    hdr[0].text = 'Term'
    hdr[1].text = 'Value'
    for k,v in get_table_data(LAST_DATA):
        row = table.add_row().cells
        row[0].text = k
        row[1].text = v
    d.add_paragraph("")
    d.add_paragraph("AI-assisted draft — professional legal review recommended before signing.").italic = True
    d.save(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition":"attachment; filename=LegalEase_Document.docx"})

@app.get("/download/txt")
def download_txt():
    if not LAST_DATA: return home()
    text = build_doc_text(LAST_DATA) + "\n\n--- KEY TERMS TABLE ---\n" + "\n".join([f"{k}: {v}" for k,v in get_table_data(LAST_DATA)])
    buf = io.BytesIO(text.encode())
    return StreamingResponse(buf, media_type="text/plain", headers={"Content-Disposition":"attachment; filename=LegalEase_Document.txt"})