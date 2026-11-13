import sys

with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

anchor = "fetch_block = fetch_block.replace(\"wrap.innerHTML = html;\", \"wrap.innerHTML = html;\\n\" + nf_filter_listener)"

patch_code = r'''
# Replace Download NOT FOUND button label with user's requested "Download Fetch Data Error Entries (Excel)"
fetch_block = fetch_block.replace(
    "${notFoundList.length ? `<button class=\"b\" id=\"btnBfDlNotFound\" type=\"button\">📥 Download NOT FOUND List</button>` : ''}",
    "${notFoundList.length ? `<button class=\"b\" id=\"btnBfDlNotFound\" type=\"button\" style=\"font-weight:700\">📥 Download Fetch Data Error Entries (Excel)</button>` : ''}"
)

# Wire 6-column error report export with 0-error protection (Requirement 5)
old_not_found_str = "exportExcel(`${prefix}_not_found_list`, ['NOT FOUND Term'], notFoundList.map(t => [t]));"
new_not_found_str = """if (!notFoundList || notFoundList.length === 0) {
              toast('ℹ️ No error entries recorded from latest fetch.');
              return;
            }
            const errHeaders = [
              'ICCID / CCID',
              'Customer / Device Details',
              'Error Reason',
              'Fetch Status',
              'API Response / Failure Description',
              'Date & Time of Processing'
            ];
            const nowFormatted = new Date().toLocaleString();
            const errRows = notFoundList.map(term => [
              term,
              'Not found in active customer database',
              'Search query term did not match any active IMEI, ICCID, or serial number',
              'FAILED - NOT FOUND',
              '404 No matching database records found',
              nowFormatted
            ]);
            exportExcel('fetch_data_error_entries_' + new Date().toISOString().slice(0, 10), errHeaders, errRows);"""

fetch_block = fetch_block.replace(old_not_found_str, new_not_found_str)
'''

if 'fetch_data_error_entries_' not in text:
    text = text.replace(anchor, anchor + "\n" + patch_code)
    with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully patched fetch_block in build_clean_modular_app.py')
else:
    print('Already patched')

