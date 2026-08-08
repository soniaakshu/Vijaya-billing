from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)

    bill_no = db.Column(db.String(30), nullable=False)

    customer = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(30), nullable=False)

    invoice_date = db.Column(db.String(20))

    from_date = db.Column(db.String(20))
    
    to_date = db.Column(db.String(20))

    grand_total = db.Column(db.Float, default=0)

    items = db.relationship(
        "InvoiceItem",
        backref="invoice",
        lazy=True,
        cascade="all, delete-orphan"
    )


class InvoiceItem(db.Model):
    __tablename__ = "invoice_items"

    id = db.Column(db.Integer, primary_key=True)

    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey("invoices.id"),
        nullable=False
    )

    # Product Date
    item_date = db.Column(db.String(20))

    # Product Name
    product = db.Column(db.String(100))

    # Unit Price
    price = db.Column(db.Float)

    # Quantity
    quantity = db.Column(db.Float)

    # Price × Quantity
    actual_amount = db.Column(db.Float)

    # CGST %
    cgst = db.Column(db.Float)

    # CGST Amount
    cgst_amount = db.Column(db.Float)

    # SGST %
    sgst = db.Column(db.Float)

    # SGST Amount
    sgst_amount = db.Column(db.Float)

    # Final Total
    total = db.Column(db.Float)
