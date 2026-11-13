with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """    {
        'file': 'frontend/edit-delete.html',
        'title': 'Edit / Delete by IMEI — BSTPL CustomerVault',
        'active_key': 'EDIT',
        'has_auth_wrap': False,
        'has_home_header': False,
        'container_html': containers['box-edit'],
        'dialog_keys': ['dlgBulkDeleteExcel', 'dlgBulkEditImei', 'dlgCartModal', 'devdlg', 'dlgEventPopup', 'dlgActionProgress'],
        'feature_js': feature_blocks['EDIT'],
        'init_js': 'initEditImeiContainer();'
    },"""

addition = """    {
        'file': 'frontend/edit-delete.html',
        'title': 'Edit / Delete by IMEI — BSTPL CustomerVault',
        'active_key': 'EDIT',
        'has_auth_wrap': False,
        'has_home_header': False,
        'container_html': containers['box-edit'],
        'dialog_keys': ['dlgBulkDeleteExcel', 'dlgBulkEditImei', 'dlgCartModal', 'devdlg', 'dlgEventPopup', 'dlgActionProgress'],
        'feature_js': feature_blocks['EDIT'],
        'init_js': 'initEditImeiContainer();'
    },
    {
        'file': 'frontend/alerts.html',
        'title': 'Expiry Alerts — BSTPL CustomerVault',
        'active_key': 'ALERTS',
        'has_auth_wrap': False,
        'has_home_header': False,
        'container_html': containers['box-exp'],
        'dialog_keys': ['dlgEventPopup', 'dlgActionProgress'],
        'feature_js': feature_blocks['ALERTS'],
        'init_js': 'await loadExpiryContainer().catch(e => console.warn(e));'
    },"""

if target in text:
    text = text.replace(target, addition, 1)
    with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("SUCCESS: Added alerts.html to pages config")
else:
    print("ERROR: edit-delete target not found")
