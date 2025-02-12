// Copyright (c) 2025, Ambibuzz Technologies LLP and contributors
// For license information, please see license.txt

frappe.ui.form.on("Track Record", {
	units: function (frm) {
		let units = parseInt(frm.doc.units);
		if (!isNaN(units)) {
			frm.set_value("duration", units * 2);
		}
	}
});
