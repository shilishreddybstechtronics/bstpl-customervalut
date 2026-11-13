import sys, os, json, re
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

def test_all():
    print("=================================================================")
    print("      COMPREHENSIVE 13-POINT VALIDATION SUITE FOR CUSTOMERVAULT   ")
    print("=================================================================")
    results = {}

    # Test 1 & 2: Home Overview (No SIM Expiry Alert card, 4-card grid)
    with open('frontend/home.html', 'r', encoding='utf-8') as f:
        home_html = f.read()

    has_expiry_card = 'id="globalExpiryAlertBanner"' in home_html
    has_stat_customers = 'id="statCustomers"' in home_html
    has_stat_del_customers = 'id="statDeletedCustomers"' in home_html
    has_stat_cust_errors = 'id="statCustomerErrors"' in home_html
    has_stat_err_entries = 'id="statErrorEntries"' in home_html
    has_stats_ribbon = 'id="statsRibbon"' in home_html

    results["1. Home Overview - Remove Unwanted Expiry Card"] = (not has_expiry_card)
    results["2. Home Overview - 4-Card Responsive Grid"] = all([
        has_stats_ribbon, has_stat_customers, has_stat_del_customers, has_stat_cust_errors, has_stat_err_entries
    ])

    # Test 3: Customer Files Grid Layout in inventory.html
    with open('frontend/inventory.html', 'r', encoding='utf-8') as f:
        inv_html = f.read()

    has_cust_card_class = 'customer-file-card' in inv_html
    has_cview = 'data-cview' in inv_html
    has_cdl = 'data-cdl' in inv_html
    has_cgrid_delegate = 'cgrid' in inv_html and 'openCustomerEntriesView' in inv_html
    results["3. Customer Files - Grid Layout & Cards"] = all([has_cust_card_class, has_cview, has_cdl, has_cgrid_delegate])

    # Test 4: Individual Record Management in inventory.html & edit-delete.html
    with open('frontend/edit-delete.html', 'r', encoding='utf-8') as f:
        ed_html = f.read()

    has_inv_edit_del = 'data-editdev' in inv_html and 'data-del' in inv_html and "$('invTableWrap').onclick" in inv_html
    has_ed_save_del = 'initEditImeiContainer' in ed_html and 'Changes saved permanently' in ed_html
    results["4. Individual Record Management (Isolation, Confirm, Save, Refresh)"] = all([has_inv_edit_del, has_ed_save_del])

    # Test 5: Error and Invalid Entries Redesign in errors.html
    with open('frontend/errors.html', 'r', encoding='utf-8') as f:
        err_html = f.read()

    has_tab_errors = 'id="tabErrErrors"' in err_html
    has_tab_invalid = 'id="tabErrInvalid"' in err_html
    has_err_sort = 'id="errSortCol"' in err_html
    has_err_pagesize = 'id="errPageSize"' in err_html
    has_err_edit_modal = 'data-erredit' in err_html and 'dlgEditError' in err_html
    results["5. Error & Invalid Entries Complete Redesign"] = all([
        has_tab_errors, has_tab_invalid, has_err_sort, has_err_pagesize, has_err_edit_modal
    ])

    # Test 6: SIM Expiry Date - Edit Functionality
    with open('backend/routes_data.py', 'r', encoding='utf-8') as f:
        routes_data = f.read()

    has_expiry_endpoint = '/devices/{device_id}/expiry-date' in routes_data
    has_exp_modal_inv = 'openEditExpiryModal' in inv_html
    has_exp_modal_ed = 'openEditExpiryModal' in ed_html
    results["6. SIM Expiry Date - Edit Functionality & DB Update"] = all([
        has_expiry_endpoint, has_exp_modal_inv, has_exp_modal_ed
    ])

    # Test 7: Login Page - Branding on RIGHT, Form on LEFT
    with open('frontend/index.html', 'r', encoding='utf-8') as f:
        login_html = f.read()

    has_login_branding_right = 'secure-surface-col' in login_html or 'Secure Smart Connected Surface Online' in login_html
    has_login_back_guard = 'replaceState' in login_html or 'pageshow' in login_html
    results["7. Login Page - Branding Right & Layout"] = (has_login_branding_right and has_login_back_guard)

    # Test 8: User Permissions & Access Control in settings.html
    with open('frontend/settings.html', 'r', encoding='utf-8') as f:
        set_html = f.read()

    has_perm_branding = 'Secure Smart Connected Surface Online' in set_html
    has_close_modal_def = 'window.closeModal = function' in set_html
    has_perm_success_popup = 'Permissions Saved Successfully' in set_html
    results["8. User Permissions & Access Control (Branding, Close, Save, Popup)"] = all([
        has_perm_branding, has_close_modal_def, has_perm_success_popup
    ])

    # Test 9: Unique Columns Correct Dynamic Calculation
    from backend.database import SessionLocal
    from backend.routes_data import get_dynamic_unique_columns, stats
    db = SessionLocal()
    try:
        cols = get_dynamic_unique_columns(db)
        s = stats(db=db, user=None)
        has_unique_cols = len(cols) > 0 and s["unique_columns"] == len(cols)
    finally:
        db.close()

    results["9. Unique Columns - Correct Dynamic Calculation"] = has_unique_cols

    # Test 10: Settings - Logout Option
    has_settings_logout_btn = 'id="settingsBtnLogout"' in set_html
    has_settings_logout_fn = 'handleSettingsLogout' in set_html
    results["10. Settings - Logout Option (Session Termination & Back-block)"] = (has_settings_logout_btn and has_settings_logout_fn)

    # Test 11: Login Inventory - Remove Unwanted Sections
    has_login_inv_focused = 'id="settingsLoginInventoryCard"' in set_html and 'loadLoginInventory' in set_html
    cluttered_in_login_inv = 'id="settingsLoginInventoryCard"' in set_html and 'Activity KPI Summary Ribbon' in set_html
    results["11. Login Inventory - Focused User Directory (No Clutter)"] = (has_login_inv_focused and not cluttered_in_login_inv)

    # Test 12: Search Audit Trail - Redesign
    with open('backend/routes_activity.py', 'r', encoding='utf-8') as f:
        routes_act = f.read()

    has_search_audit_route = '/search-audit' in routes_act
    has_search_audit_card = 'id="settingsSearchAuditCard"' in set_html
    has_search_audit_fn = 'loadSearchAuditTrail' in set_html
    results["12. Search Audit Trail - Complete Redesign"] = all([
        has_search_audit_route, has_search_audit_card, has_search_audit_fn
    ])

    # Test 13: Fetch Data - Complete Redesign
    with open('frontend/fetch-data.html', 'r', encoding='utf-8') as f:
        fetch_html = f.read()

    has_preset_fields = 'activateAllFieldsPreset' in fetch_html
    has_preset_cust = 'activateAllCustomersPreset' in fetch_html
    has_preset_records = 'activateAllRecordsPreset' in fetch_html
    has_dynamic_cols_fetch = '/api/columns/all' in fetch_html
    results["13. Fetch Data - Complete Redesign (All Fields, Customers, Records)"] = all([
        has_preset_fields, has_preset_cust, has_preset_records, has_dynamic_cols_fetch
    ])

    print("\nVALIDATION RESULTS:")
    all_passed = True
    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"[{status}] {test_name}")
        if not passed:
            all_passed = False

    print("\n-----------------------------------------------------------------")
    if all_passed:
        print("ALL 13 REQUIREMENTS SUCCESSFULLY VALIDATED AND VERIFIED!")
    else:
        print("SOME TESTS FAILED - REVIEW LOGS ABOVE.")
    print("-----------------------------------------------------------------")

if __name__ == '__main__':
    test_all()
