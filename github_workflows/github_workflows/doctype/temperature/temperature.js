// Copyright (c) 2025, Ambibuzz Technologies LLP and contributors
// For license information, please see license.txt

frappe.ui.form.on("Temperature", {
	refresh(frm) {
    	console.log(frm);
	},
});

class Calculator {
    add(a, b) {
        return a + b;
    }

    subtract(a, b) {
	console.log(a + b);
        return a - b;
    }

    multiply(a, b) {
        return a * b;
    }

    divide(a, b) {
        if (b === 0) {
			console.log("hehehehe");
            throw new Error("Cannot divide by zero!");
        }
        return a / b;
    }
}
