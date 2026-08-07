from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    make_response
)

from models import db, Invoice, InvoiceItem

import pdfkit
import os
import sys
import threading
import webbrowser

app = Flask(__name__)

# --------------------------------------------------
# PDF Configuration
# --------------------------------------------------

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

WKHTMLTOPDF_PATH = os.path.join(
    BASE_DIR,
    "wkhtmltopdf",
    "bin",
    "wkhtmltopdf.exe"
)

config = pdfkit.configuration(
    wkhtmltopdf=WKHTMLTOPDF_PATH
)

# --------------------------------------------------
# Database Configuration
# --------------------------------------------------

DB_PATH = os.path.join(BASE_DIR, "database.db")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{DB_PATH}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)# --------------------------------------------------
# Download PDF
# --------------------------------------------------

@app.route("/download/<int:invoice_id>")
def download_pdf(invoice_id):

    invoice = Invoice.query.get_or_404(invoice_id)

    if invoice.company == "padmavathi":

        html = render_template(
            "pdf_padmavathi.html",
            invoice=invoice
        )

    else:

        html = render_template(
            "pdf_invoice.html",
            invoice=invoice
        )

    options = {

        "enable-local-file-access": "",

        "page-size": "A4",

        "encoding": "UTF-8",

        "margin-top": "6mm",

        "margin-right": "6mm",

        "margin-bottom": "6mm",

        "margin-left": "6mm",

        "print-media-type": "",

        "disable-smart-shrinking": "",

        "quiet": ""

    }

    css_file = os.path.join(
        app.root_path,
        "static",
        "css",
        "pdf_invoice.css"
    )

    pdf = pdfkit.from_string(
        html,
        False,
        configuration=config,
        options=options,
        css=css_file
    )

    response = make_response(pdf)

    response.headers["Content-Type"] = "application/pdf"

    response.headers[
        "Content-Disposition"
    ] = f'attachment; filename="Invoice_{invoice.bill_no}.pdf"'

    return response
print("=" * 60)
print("Current Working Directory:", os.getcwd())
print("Instance Path:", app.instance_path)
print("Database URI:", app.config["SQLALCHEMY_DATABASE_URI"])
print("=" * 60)

with app.app_context():
    db.create_all()
    print("Database Ready.")
    # --------------------------------------------------
# Run Application
# --------------------------------------------------

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()

    print("=" * 60)
    print("Vijaya Billing Started")
    print("Open: http://127.0.0.1:5000")
    print("=" * 60)

    app.run(host="127.0.0.1", port=5000)