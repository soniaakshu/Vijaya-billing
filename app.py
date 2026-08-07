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
import shutil
import threading
import webbrowser

app = Flask(__name__)

# --------------------------------------------------
# Base Directory
# --------------------------------------------------

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# --------------------------------------------------
# PDF Configuration
# --------------------------------------------------

if sys.platform.startswith("win"):

    WKHTMLTOPDF_PATH = os.path.join(
        BASE_DIR,
        "wkhtmltopdf",
        "bin",
        "wkhtmltopdf.exe"
    )

else:

    WKHTMLTOPDF_PATH = shutil.which("wkhtmltopdf")

config = pdfkit.configuration(
    wkhtmltopdf=WKHTMLTOPDF_PATH
)

# --------------------------------------------------
# Database
# --------------------------------------------------

DB_PATH = os.path.join(BASE_DIR, "database.db")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{DB_PATH}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

print("=" * 60)
print("Current Working Directory:", os.getcwd())
print("Instance Path:", app.instance_path)
print("Database URI:", app.config["SQLALCHEMY_DATABASE_URI"])
print("=" * 60)

with app.app_context():
    db.create_all()
    print("Database Ready.")
# --------------------------------------------------
# Dashboard
# --------------------------------------------------

@app.route("/")
def dashboard():
    return render_template("dashboard.html")


# --------------------------------------------------
# K.S. Prakash Invoice
# --------------------------------------------------

@app.route("/new-invoice")
def new_invoice():

    print("Loading NEW_INVOICE.HTML")

    return render_template(
        "new_invoice.html"
    )


# --------------------------------------------------
# Padmavathi Invoice
# --------------------------------------------------

@app.route("/padmavathi")
def padmavathi_invoice():

    return render_template(
        "padmavathi_invoice.html"
    )


# --------------------------------------------------
# Invoice History
# --------------------------------------------------

@app.route("/history")
def history():

    invoices = Invoice.query.order_by(
        Invoice.id.desc()
    ).all()

    return render_template(
        "invoice_history.html",
        invoices=invoices
    )


# --------------------------------------------------
# Print - K.S. Prakash
# --------------------------------------------------

@app.route("/print/<int:invoice_id>")
def print_invoice(invoice_id):

    invoice = Invoice.query.get_or_404(
        invoice_id
    )

    return render_template(
        "print_invoice.html",
        invoice=invoice,
        print_mode=True,
        pdf_mode=False
    )


# --------------------------------------------------
# Print - Padmavathi
# --------------------------------------------------

@app.route("/print-padmavathi/<int:invoice_id>")
def print_padmavathi(invoice_id):

    invoice = Invoice.query.get_or_404(
        invoice_id
    )

    return render_template(
        "print_padmavathi.html",
        invoice=invoice,
        print_mode=True,
        pdf_mode=False
    )
# --------------------------------------------------
# Download PDF
# --------------------------------------------------

@app.route("/download/<int:invoice_id>")
def download_pdf(invoice_id):

    invoice = Invoice.query.get_or_404(invoice_id)

    # Select HTML template
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

    response.headers["Content-Disposition"] = (
        f'attachment; filename="Invoice_{invoice.bill_no}.pdf"'
    )

    return response
# --------------------------------------------------
# Delete Invoice
# --------------------------------------------------

@app.route("/delete/<int:invoice_id>")
def delete_invoice(invoice_id):

    invoice = Invoice.query.get_or_404(invoice_id)

    db.session.delete(invoice)
    db.session.commit()

    return redirect(
        url_for("history")
    )


# --------------------------------------------------
# Save Invoice
# --------------------------------------------------

@app.route("/save-invoice", methods=["POST"])
def save_invoice():

    action = request.form.get("action")
    company = request.form.get("company")

    print("=" * 50)
    print(request.form)
    print("Company =", repr(company))
    print("=" * 50)

    if company is None:
        return "Company field is missing!"

    bill_no = request.form.get("bill_no")
    customer = request.form.get("customer")
    from_date = request.form.get("from_date")
    to_date = request.form.get("to_date")

    invoice = Invoice(
        bill_no=bill_no,
        customer=customer,
        company=company,
        from_date=from_date,
        to_date=to_date,
        grand_total=0
    )

    db.session.add(invoice)
    db.session.commit()

    # ---------------- Products ----------------

    dates = request.form.getlist("item_date[]")
    products = request.form.getlist("product[]")
    prices = request.form.getlist("price[]")
    qtys = request.form.getlist("qty[]")

    actual_amounts = request.form.getlist("actual_amt[]")

    cgsts = request.form.getlist("cgst[]")
    cgst_amounts = request.form.getlist("cgst_amt[]")

    sgsts = request.form.getlist("sgst[]")
    sgst_amounts = request.form.getlist("sgst_amt[]")

    totals = request.form.getlist("total[]")

    grand_total = 0

    for i in range(len(products)):

        item = InvoiceItem(

            invoice_id=invoice.id,

            item_date=dates[i],

            product=products[i],

            price=float(prices[i] or 0),

            quantity=float(qtys[i] or 0),

            actual_amount=float(actual_amounts[i] or 0),

            cgst=float(cgsts[i] or 0),

            cgst_amount=float(cgst_amounts[i] or 0),

            sgst=float(sgsts[i] or 0),

            sgst_amount=float(sgst_amounts[i] or 0),

            total=float(totals[i] or 0)

        )

        grand_total += float(totals[i] or 0)

        db.session.add(item)

    invoice.grand_total = grand_total

    db.session.commit()

    # ---------------- Actions ----------------

    if action == "print":

        if company == "padmavathi":

            return redirect(
                url_for(
                    "print_padmavathi",
                    invoice_id=invoice.id
                )
            )

        return redirect(
            url_for(
                "print_invoice",
                invoice_id=invoice.id
            )
        )

    elif action == "pdf":

        return redirect(
            url_for(
                "download_pdf",
                invoice_id=invoice.id
            )
        )

    return redirect(
        url_for("history")
    )
# --------------------------------------------------
# Run Application
# --------------------------------------------------

def open_browser():

    webbrowser.open(
        "http://127.0.0.1:5000"
    )


if __name__ == "__main__":

    # Only open browser on Windows
    if sys.platform.startswith("win"):

        threading.Timer(
            1.5,
            open_browser
        ).start()

    print("=" * 60)
    print("Vijaya Billing Started")
    print("Current Directory:", BASE_DIR)
    print("=" * 60)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
