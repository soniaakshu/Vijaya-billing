from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    make_response,
    session
)

from models import db, Invoice, InvoiceItem, Admin
from werkzeug.security import generate_password_hash, check_password_hash

import pdfkit
import os
import hmac
import sys
import shutil
import threading
import webbrowser

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "temporary-development-key"
)

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

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
# Database Configuration
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
        # Create first admin account if none exists
    if Admin.query.count() == 0:

        username = os.environ.get("ADMIN_USERNAME")
        password = os.environ.get("ADMIN_PASSWORD")

        if username and password:

            admin = Admin(
                username=username,
                password_hash=generate_password_hash(password)
            )

            db.session.add(admin)
            db.session.commit()

            print("First admin account created.")
    

    # Add invoice_date to existing databases if it does not exist
    from sqlalchemy import text

    try:
        db.session.execute(
            text(
                "ALTER TABLE invoices "
                "ADD COLUMN invoice_date VARCHAR(20)"
            )
        )
        db.session.commit()
        print("Added invoice_date column.")
    except Exception as e:
        db.session.rollback()

        # Column already exists - nothing to do
        if "duplicate column name" in str(e).lower():
            print("invoice_date column already exists.")
        else:
            print("Database migration message:", e)

    print("Database Ready.")
# --------------------------------------------------
# LOGIN
# --------------------------------------------------

# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = Admin.query.filter_by(
            username=username
        ).first()

        if admin and check_password_hash(
            admin.password_hash,
            password
        ):
            session["admin_id"] = admin.id
            session["logged_in"] = True

            return redirect(
                url_for("dashboard")
            )

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )

# --------------------------------------------------
# CHANGE PASSWORD
# --------------------------------------------------

@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if not session.get("logged_in"):
        return redirect(
            url_for("login")
        )

    admin_id = session.get("admin_id")

    admin = Admin.query.get(admin_id)

    if admin is None:
        session.clear()

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        current_password = request.form.get(
            "current_password",
            ""
        )

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # Check current password
        if not check_password_hash(
            admin.password_hash,
            current_password
        ):
            return render_template(
                "change_password.html",
                error="Current password is incorrect."
            )

        # Check minimum password length
        if len(new_password) < 8:
            return render_template(
                "change_password.html",
                error="New password must be at least 8 characters."
            )

        # Check confirmation
        if new_password != confirm_password:
            return render_template(
                "change_password.html",
                error="New passwords do not match."
            )

        # Save new password securely
        admin.password_hash = generate_password_hash(
            new_password
        )

        db.session.commit()

        return render_template(
            "change_password.html",
            success="Password changed successfully."
        )

    return render_template(
        "change_password.html"
    )
# --------------------------------------------------
# PROTECT WEBSITE
# --------------------------------------------------

@app.before_request
def require_login():

    allowed_routes = {
        "login",
        "static"
    }

    if request.endpoint in allowed_routes:
        return

    if not session.get("logged_in"):
        return redirect(
            url_for("login")
        )
# --------------------------------------------------
# PROTECT WEBSITE
# --------------------------------------------------

@app.before_request
def require_login():

    allowed_routes = {
        "login",
        "static"
    }

    if request.endpoint in allowed_routes:
        return

    if not session.get("logged_in"):
        return redirect(url_for("login"))
# --------------------------------------------------
# Dashboard
# --------------------------------------------------

@app.route("/")
def dashboard():

    return render_template(
        "dashboard.html"
    )

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

    # Select template
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
    ] = (
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
# Save Invoice (Updated to handle "Others" fields)
# --------------------------------------------------

@app.route("/save-invoice", methods=["POST"])
def save_invoice():

    action = request.form.get("action")
    company = request.form.get("company")

    print("=" * 50)
    print("Form Data:", request.form)
    print("Company =", repr(company))
    print("=" * 50)

    if company is None:
        return "Company field is missing!", 400

    bill_no = request.form.get("bill_no")
    
    # ---------------- Customer Field Handling ----------------
    customer = request.form.get("customer")
    custom_customer = request.form.get("custom_customer", "").strip()
    
    # If "Others" is selected, fallback to the custom customer input box
    if customer == "Others" and custom_customer:
        customer = custom_customer

    invoice_date = request.form.get("invoice_date")
    from_date = request.form.get("from_date")
    to_date = request.form.get("to_date")

    # ---------------- Create Invoice ----------------
    invoice = Invoice(
        bill_no=bill_no,
        customer=customer,
        company=company,
        invoice_date=invoice_date,
        from_date=from_date,
        to_date=to_date,
        grand_total=0
    )
    db.session.add(invoice)
    db.session.commit()

    # ---------------- Product Details Handling ----------------
    dates = request.form.getlist("item_date[]")
    products = request.form.getlist("product[]")
    custom_products = request.form.getlist("custom_product[]")  # Reads custom typed products
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

        # Handle "Others" for Product
        prod_name = products[i]
        if prod_name == "Others" and i < len(custom_products) and custom_products[i].strip():
            prod_name = custom_products[i].strip()

        item = InvoiceItem(
            invoice_id=invoice.id,
            item_date=dates[i] if i < len(dates) else "",
            product=prod_name,
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
            return redirect(url_for("print_padmavathi", invoice_id=invoice.id))
        return redirect(url_for("print_invoice", invoice_id=invoice.id))

    elif action == "pdf":
        return redirect(url_for("download_pdf", invoice_id=invoice.id))

    return redirect(url_for("history"))
# --------------------------------------------------
# Run Application
# --------------------------------------------------

def open_browser():

    webbrowser.open(
        "http://127.0.0.1:5000"
    )


if __name__ == "__main__":

    # Open browser automatically only on Windows
    if sys.platform.startswith("win"):

        threading.Timer(
            1.5,
            open_browser
        ).start()

    print("=" * 60)
    print("Vijaya Billing Started")
    print("Current Working Directory:", os.getcwd())
    print("Database:", DB_PATH)
    print("=" * 60)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
