# West Ada purchase request form (blank)

The blank West Ada Joint School District #2 "Request for Purchase/Reimbursement" form, with no filled data.

A Claude purchase-order skill fetches this file from its raw link, fills it inside the district's Jira portal page, and attaches the result to the CTE request. Filled POs are never stored here.

Raw link: https://raw.githubusercontent.com/DummyGuppy/westada-po-form/main/blank_po.pdf

`tools/fill_incremental.py` fills the form as a small add-on to `blank_po.pdf` (an incremental PDF update), so only that small piece has to be sent to the Jira page, which joins it to this blank and attaches the result.
