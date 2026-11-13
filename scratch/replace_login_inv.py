with open('frontend/settings.html', 'r', encoding='utf-8') as f:
    html = f.read()

card_start = html.find('<div class="card" id="settingsLoginInventoryCard"')
card_end = html.find('</section>', card_start)

new_content = """<div class="card" id="settingsLoginInventoryCard" style="padding:28px;border-radius:18px;border:1px solid var(--line);background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.03);margin-bottom:24px">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;margin-bottom:20px;border-bottom:1px solid var(--line);padding-bottom:16px">
            <div>
              <h2 style="margin:0 0 6px;font-size:20px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:10px">
                <span>🔑</span> <span>Login Inventory</span>
              </h2>
              <p style="margin:0;font-size:13.5px;color:var(--muted)">Directory of system user accounts, assigned access roles, login identifiers, and authentication records.</p>
            </div>
            <div style="display:flex;gap:10px;align-items:center">
              <input type="text" id="loginInvSearch" placeholder="Filter by User ID, Name, or Role…" oninput="filterLoginInventory(this.value)" style="height:38px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px;width:260px" />
              <button type="button" class="b" onclick="loadLoginInventory()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">🔄 Refresh</button>
            </div>
          </div>

          <div id="loginInventoryTableWrap">
            <div class="empty">Loading Login Inventory accounts…</div>
          </div>
        </div>

        <!-- SEARCH AUDIT TRAIL SECTION -->
        <div class="card" id="settingsSearchAuditCard" style="padding:28px;border-radius:18px;border:1px solid var(--line);background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.03);margin-bottom:24px">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;margin-bottom:20px;border-bottom:1px solid var(--line);padding-bottom:16px">
            <div>
              <h2 style="margin:0 0 6px;font-size:20px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:10px">
                <span>🔍</span> <span>Search Audit Trail</span>
              </h2>
              <p style="margin:0;font-size:13.5px;color:var(--muted)">Comprehensive enterprise audit log of all system searches, IMEI lookups, customer queries, and inventory filtering events.</p>
            </div>
            <button type="button" class="b" id="satRefresh" onclick="loadSearchAuditTrail()" style="font-weight:700;padding:8px 16px;border-radius:9px;font-size:13px">🔄 Refresh Audit</button>
          </div>

          <!-- Filter & Search Controls -->
          <div class="row" style="margin-bottom:18px;gap:12px;flex-wrap:wrap;align-items:flex-end">
            <div style="flex:1;min-width:220px">
              <label for="satQuery" style="display:block;font-size:12px;font-weight:700;margin-bottom:6px">Search Audit Records</label>
              <input id="satQuery" placeholder="Search by username, user ID, keyword, or customer…" style="width:100%;height:38px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px" />
            </div>
            <div style="width:170px">
              <label for="satType" style="display:block;font-size:12px;font-weight:700;margin-bottom:6px">Search Type</label>
              <select id="satType" style="width:100%;height:38px;padding:0 10px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px">
                <option value="all">All Types</option>
                <option value="quick_search">Quick Search</option>
                <option value="imei_search">IMEI Search</option>
                <option value="customer_filter">Customer Filter</option>
                <option value="column_search">Column Search</option>
                <option value="bulk_fetch">Bulk Fetch</option>
              </select>
            </div>
            <div style="width:150px">
              <label for="satSort" style="display:block;font-size:12px;font-weight:700;margin-bottom:6px">Sort By</label>
              <select id="satSort" style="width:100%;height:38px;padding:0 10px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px">
                <option value="search_date">Date / Time</option>
                <option value="username">Username</option>
                <option value="search_type">Search Type</option>
              </select>
            </div>
            <div style="width:110px">
              <label for="satDir" style="display:block;font-size:12px;font-weight:700;margin-bottom:6px">Order</label>
              <select id="satDir" style="width:100%;height:38px;padding:0 10px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px">
                <option value="desc">Newest</option>
                <option value="asc">Oldest</option>
              </select>
            </div>
            <div style="width:110px">
              <label for="satPageSize" style="display:block;font-size:12px;font-weight:700;margin-bottom:6px">Per Page</label>
              <select id="satPageSize" style="width:100%;height:38px;padding:0 10px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px">
                <option value="15">15</option>
                <option value="25" selected>25</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
            </div>
            <button class="b" type="button" id="satClearBtn" onclick="resetSearchAuditFilters()" style="height:38px;padding:0 14px;font-size:13px;font-weight:700">Clear</button>
          </div>

          <div id="satTableWrap">
            <div class="empty">Loading Search Audit records…</div>
          </div>
        </div>
        """

html = html[:card_start] + new_content + html[card_end:]

with open('frontend/settings.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("SUCCESS: Successfully replaced Login Inventory and added Search Audit Trail!")

