document.addEventListener("DOMContentLoaded", function () {

    const tableBody = document.querySelector("#productTable tbody");
    const addBtn = document.getElementById("addRow");
    const grandTotal = document.getElementById("grandTotal");
    const customerSelect = document.getElementById("customerSelect");

    // ------------------------------
    // Customer "Others" Toggle
    // ------------------------------
    function toggleCustomCustomer() {
        const customCustomerBox = document.getElementById("customCustomerContainer");
        if (customerSelect && customCustomerBox) {
            if (customerSelect.value === "Others") {
                customCustomerBox.style.display = "block";
            } else {
                customCustomerBox.style.display = "none";
            }
        }
    }

    if (customerSelect) {
        customerSelect.addEventListener("change", toggleCustomCustomer);
        toggleCustomCustomer(); // Run on page load
    }

    // ------------------------------
    // Calculate Row
    // ------------------------------
    function calculateRow(row) {

        const price = parseFloat(row.querySelector(".price").value) || 0;
        const qty = parseFloat(row.querySelector(".qty").value) || 0;
        const cgst = parseFloat(row.querySelector(".cgst").value) || 0;
        const sgst = parseFloat(row.querySelector(".sgst").value) || 0;

        // Actual Amount
        const actualAmount = price * qty;

        // GST Amounts
        const cgstAmount = (actualAmount * cgst) / 100;
        const sgstAmount = (actualAmount * sgst) / 100;

        // Final Total
        const rowTotal = actualAmount + cgstAmount + sgstAmount;

        // Fill values
        row.querySelector(".actualAmt").value = actualAmount.toFixed(2);
        row.querySelector(".cgstAmt").value = cgstAmount.toFixed(2);
        row.querySelector(".sgstAmt").value = sgstAmount.toFixed(2);
        row.querySelector(".total").value = rowTotal.toFixed(2);

        calculateGrandTotal();
    }

    // ------------------------------
    // Grand Total
    // ------------------------------
    function calculateGrandTotal() {

        let total = 0;

        document.querySelectorAll(".total").forEach(function(input){
            total += parseFloat(input.value) || 0;
        });

        grandTotal.textContent = total.toFixed(2);
    }

    // ------------------------------
    // Attach Events (Row Calculations + Custom Product Input)
    // ------------------------------
    function attachEvents(row) {

        // Recalculate on input changes
        row.querySelectorAll(".price, .qty, .cgst, .sgst").forEach(function(input){
            input.addEventListener("input", function(){
                calculateRow(row);
            });
        });

        // Toggle Custom Product input when "Others" is selected
        const productSelect = row.querySelector(".product");
        if (productSelect) {
            productSelect.addEventListener("change", function () {
                let customProductInput = row.querySelector(".custom-product-input");

                if (this.value === "Others") {
                    if (!customProductInput) {
                        customProductInput = document.createElement("input");
                        customProductInput.type = "text";
                        customProductInput.name = "custom_product[]";
                        customProductInput.className = "form-control form-control-sm mt-1 custom-product-input";
                        customProductInput.placeholder = "Enter Product Name";
                        this.parentNode.appendChild(customProductInput);
                    } else {
                        customProductInput.style.display = "block";
                    }
                } else {
                    if (customProductInput) {
                        customProductInput.style.display = "none";
                        customProductInput.value = ""; // Clear custom input if switched back
                    }
                }
            });
        }

        // Delete row handler
        row.querySelector(".deleteRow").addEventListener("click", function(){

            row.remove();

            document.querySelectorAll("#productTable tbody tr").forEach(function(r, index){
                r.cells[0].textContent = index + 1;
            });

            calculateGrandTotal();
        });
    }

    // ------------------------------
    // Existing Rows
    // ------------------------------
    document.querySelectorAll("#productTable tbody tr").forEach(function(row){
        attachEvents(row);
        calculateRow(row);
    });

    // ------------------------------
    // Add Product Row
    // ------------------------------
    addBtn.addEventListener("click", function(){

        let rowCount = tableBody.rows.length + 1;

        const row = `
<tr>
    <td>${rowCount}</td>

    <td>
        <input type="date" class="form-control" name="item_date[]">
    </td>

    <td>
        <select class="form-select product" name="product[]">
            <option>Milk</option>
            <option>Curd</option>
            <option>Paneer</option>
            <option>Ghee</option>
            <option>Ice Cream</option>
            <option>Doodhpeda</option>
            <option value="Others">Others</option>
        </select>
    </td>

    <td>
        <input type="number" class="form-control price" name="price[]" min="0" step="0.01">
    </td>

    <td>
        <input type="number" class="form-control qty" name="qty[]" min="0" step="1">
    </td>

    <!-- Actual Amount -->
    <td>
        <input type="text" class="form-control actualAmt" name="actual_amt[]" value="0.00" readonly>
    </td>

    <!-- CGST % -->
    <td>
        <input type="number" class="form-control cgst" name="cgst[]" value="2.5" min="0" step="any">
    </td>

    <!-- CGST Amount -->
    <td>
        <input type="text" class="form-control cgstAmt" name="cgst_amt[]" value="0.00" readonly>
    </td>

    <!-- SGST % -->
    <td>
        <input type="number" class="form-control sgst" name="sgst[]" value="2.5" min="0" step="any">
    </td>

    <!-- SGST Amount -->
    <td>
        <input type="text" class="form-control sgstAmt" name="sgst_amt[]" value="0.00" readonly>
    </td>

    <!-- Total -->
    <td>
        <input type="text" class="form-control total" name="total[]" value="0.00" readonly>
    </td>

    <td>
        <button type="button" class="btn btn-danger deleteRow">Delete</button>
    </td>
</tr>
`;

        tableBody.insertAdjacentHTML("beforeend", row);

        const newRow = tableBody.lastElementChild;

        attachEvents(newRow);
        calculateRow(newRow);

    });

});
