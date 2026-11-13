import re

file_path = 'frontend/cart.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

idx1 = content.find('window.restoreCustomer =')
idx2 = content.find('// Client-Side CSV Export')

assert idx1 != -1 and idx2 != -1, f"Could not find boundaries in cart.html: {idx1}, {idx2}"

new_cart_actions = """// --- Real-time Status & Progress Monitor Helper ---
    function showCartStatusProgress(opts) {
      const wrap = document.getElementById('cartEmptyProgressWrap');
      if (!wrap) return;
      wrap.hidden = false;

      const icon = document.getElementById('cartProgSpinIcon');
      const title = document.getElementById('cartProgTitle');
      const status = document.getElementById('cartProgStatus');
      const pct = document.getElementById('cartProgPct');
      const rows = document.getElementById('cartProgRowsCount');
      const bar = document.getElementById('cartProgBar');
      const log = document.getElementById('cartProgLiveDetailBox');

      if (icon) {
        icon.textContent = opts.icon || '⏳';
        icon.className = opts.spin ? 'spin' : '';
      }
      if (title) title.textContent = opts.title || 'Processing…';
      if (status) {
        status.textContent = opts.status || 'In progress…';
        status.style.color = opts.tone === 'ok' ? '#16a34a' : (opts.tone === 'warn' ? '#d97706' : '#dc2626');
      }
      if (pct) {
        pct.textContent = (opts.pct != null ? opts.pct : 0) + '%';
        pct.style.color = opts.tone === 'ok' ? '#16a34a' : (opts.tone === 'warn' ? '#d97706' : '#dc2626');
      }
      if (rows) rows.textContent = opts.rows || '';
      if (bar) {
        bar.style.width = (opts.pct != null ? opts.pct : 0) + '%';
        bar.style.background = opts.tone === 'ok' 
          ? 'linear-gradient(90deg, #10b981, #059669)' 
          : (opts.tone === 'warn' ? 'linear-gradient(90deg, #f59e0b, #d97706)' : 'linear-gradient(90deg, #ef4444, #dc2626)');
      }
      if (log && opts.detail) {
        const timeStr = new Date().toLocaleTimeString();
        if (opts.appendLog) {
          log.innerHTML += `<div><span style="opacity:0.8">[${timeStr}]</span> ${E(opts.detail)}</div>`;
        } else {
          log.innerHTML = `<div><span style="opacity:0.8">[${timeStr}]</span> ${E(opts.detail)}</div>`;
        }
      }
    }

    function hideCartStatusProgress(delayMs = 2000) {
      setTimeout(() => {
        const wrap = document.getElementById('cartEmptyProgressWrap');
        if (wrap) wrap.hidden = true;
      }, delayMs);
    }

    // Actions: Restore Customer
    window.restoreCustomer = async function(cid, custName) {
      showCartStatusProgress({
        icon: '🔄',
        spin: true,
        title: `Restoring Customer "${custName}"…`,
        status: 'Re-activating customer portfolio and associated SIM entries in database…',
        pct: 45,
        tone: 'ok',
        detail: `Starting restoration for customer #${cid} (${custName})…`
      });

      try {
        const res = await api(`/api/customers/${cid}/restore`, { method: 'POST' });
        showCartStatusProgress({
          icon: '✅',
          spin: false,
          title: `Customer "${custName}" Restored!`,
          status: 'Restoration 100% complete — records active in inventory.',
          pct: 100,
          tone: 'ok',
          detail: `✓ Successfully restored customer portfolio and ${res.devices || 'all'} associated SIM entries!`,
          appendLog: true
        });
        showToast(`✓ Customer "${custName}" restored to active inventory!`, 'ok');
        await loadCartContainer();
        hideCartStatusProgress(2500);
      } catch (err) {
        showCartStatusProgress({
          icon: '⚠️',
          spin: false,
          title: `Failed to Restore Customer "${custName}"`,
          status: err.message || 'Operation failed',
          pct: 0,
          tone: 'danger',
          detail: `Error: ${err.message || 'Unknown server error'}`,
          appendLog: true
        });
        showToast(err.message || 'Failed to restore customer', 'bad');
        hideCartStatusProgress(4000);
      }
    };

    // Actions: Purge Customer Forever
    window.purgeCustomerForever = async function(cid, custName) {
      const ok = await askConfirm(
        `Are you sure you want to permanently delete customer "${custName}" and all associated data records from the database and TiDB Cloud?\\n\\nThis action cannot be undone.`,
        { title: 'Delete Customer Forever?', okText: 'Delete Forever', tone: 'danger' }
      );
      if (!ok) return;

      showCartStatusProgress({
        icon: '🗑️',
        spin: true,
        title: `Permanently Erasing Customer "${custName}"…`,
        status: 'Dropping dedicated SQL table and purging records from TiDB Cloud…',
        pct: 50,
        tone: 'danger',
        detail: `Purging customer #${cid} (${custName}) and dropping cloud tables…`
      });

      try {
        const res = await api(`/api/customers/${cid}/purge`, { method: 'DELETE' });
        showCartStatusProgress({
          icon: '🗑️',
          spin: false,
          title: `Customer "${custName}" Purged Forever`,
          status: 'Permanent deletion complete — table dropped and data removed.',
          pct: 100,
          tone: 'danger',
          detail: `✓ Successfully purged customer #${cid} and erased ${res.devices || 0} SIM records forever.`,
          appendLog: true
        });
        showToast(`Customer "${custName}" permanently deleted`, 'ok');
        await loadCartContainer();
        hideCartStatusProgress(2500);
      } catch (err) {
        showCartStatusProgress({
          icon: '⚠️',
          spin: false,
          title: `Failed to Delete Customer "${custName}"`,
          status: err.message || 'Operation failed',
          pct: 0,
          tone: 'danger',
          detail: `Error: ${err.message || 'Unknown server error'}`,
          appendLog: true
        });
        showToast(err.message || 'Failed to permanently delete customer', 'bad');
        hideCartStatusProgress(4000);
      }
    };

    // Actions: Restore Device
    window.restoreDevice = async function(id, imei) {
      showCartStatusProgress({
        icon: '🔄',
        spin: true,
        title: `Restoring Device Record (${imei})…`,
        status: 'Re-activating record and updating active inventory tables…',
        pct: 50,
        tone: 'ok',
        detail: `Clearing deleted timestamp for device #${id} (IMEI ${imei})…`
      });

      try {
        await api(`/api/bin/${id}/restore`, { method: 'POST' });
        showCartStatusProgress({
          icon: '✅',
          spin: false,
          title: `Record (${imei}) Restored!`,
          status: 'Record restored successfully — active in Customer Inventory.',
          pct: 100,
          tone: 'ok',
          detail: `✓ Device record #${id} (IMEI ${imei}) is now active.`,
          appendLog: true
        });
        showToast(`✓ Record (${imei}) restored to inventory`, 'ok');
        await loadCartContainer();
        hideCartStatusProgress(2000);
      } catch (err) {
        showCartStatusProgress({
          icon: '⚠️',
          spin: false,
          title: `Failed to Restore Record (${imei})`,
          status: err.message || 'Operation failed',
          pct: 0,
          tone: 'danger',
          detail: `Error: ${err.message || 'Unknown server error'}`,
          appendLog: true
        });
        showToast(err.message || 'Failed to restore device', 'bad');
        hideCartStatusProgress(3500);
      }
    };

    // Actions: Purge Device Forever
    window.purgeDeviceForever = async function(id, imei) {
      const ok = await askConfirm(
        `Record with IMEI "${imei}" will be permanently erased from the database and cannot be recovered.`,
        { title: 'Delete Record Forever?', okText: 'Delete Forever', tone: 'danger' }
      );
      if (!ok) return;

      showCartStatusProgress({
        icon: '🗑️',
        spin: true,
        title: `Permanently Deleting Device (${imei})…`,
        status: 'Erasing device record permanently from TiDB Cloud…',
        pct: 50,
        tone: 'danger',
        detail: `Purging device #${id} (IMEI ${imei}) forever…`
      });

      try {
        await api(`/api/bin/${id}`, { method: 'DELETE' });
        showCartStatusProgress({
          icon: '🗑️',
          spin: false,
          title: `Record (${imei}) Erased Forever`,
          status: 'Permanent deletion complete — record purged from database.',
          pct: 100,
          tone: 'danger',
          detail: `✓ Device #${id} (IMEI ${imei}) erased permanently.`,
          appendLog: true
        });
        showToast(`✓ Record (${imei}) permanently deleted`, 'ok');
        await loadCartContainer();
        hideCartStatusProgress(2000);
      } catch (err) {
        showCartStatusProgress({
          icon: '⚠️',
          spin: false,
          title: `Failed to Delete Record (${imei})`,
          status: err.message || 'Operation failed',
          pct: 0,
          tone: 'danger',
          detail: `Error: ${err.message || 'Unknown server error'}`,
          appendLog: true
        });
        showToast(err.message || 'Failed to permanently delete record', 'bad');
        hideCartStatusProgress(3500);
      }
    };

    // Actions: Restore All Entries
    window.restoreAllCartEntries = async function() {
      const total = allCartDevs.length;
      if (!total) {
        showToast('No deleted customer entries in the cart to restore.', 'info');
        return;
      }

      const ok = await askConfirm(
        `Are you sure you want to restore all ${total.toLocaleString()} deleted customer entries back to active inventory?`,
        { title: 'Restore All Records?', okText: 'Restore All', tone: 'ok' }
      );
      if (!ok) return;

      const btn = document.getElementById('btnRestoreAllCart');
      if (btn) { btn.disabled = true; btn.textContent = 'Restoring…'; }

      showCartStatusProgress({
        icon: '🔄',
        spin: true,
        title: `Restoring All ${total.toLocaleString()} Records…`,
        status: 'Re-activating all deleted entries back to active inventory…',
        pct: 30,
        rows: `0 / ${total} records`,
        tone: 'ok',
        detail: `Beginning batch restore for ${total} deleted records…`
      });

      try {
        const res = await api('/api/bin/restore-all', { method: 'POST' });
        showCartStatusProgress({
          icon: '✅',
          spin: false,
          title: `All Records Restored!`,
          status: 'All records restored successfully — active in Customer Inventory.',
          pct: 100,
          rows: `${total} / ${total} records`,
          tone: 'ok',
          detail: `✓ Successfully restored ${res.restored || total} records back to active database inventory!`,
          appendLog: true
        });
        showToast(res.message || `✓ Successfully restored ${res.restored || total} records!`, 'ok');
        await loadCartContainer();
        hideCartStatusProgress(3000);
      } catch (err) {
        showCartStatusProgress({
          icon: '⚠️',
          spin: false,
          title: 'Failed to Restore All Records',
          status: err.message || 'Operation failed',
          pct: 0,
          tone: 'danger',
          detail: `Error: ${err.message || 'Unknown server error'}`,
          appendLog: true
        });
        showToast(err.message || 'Failed to restore all entries', 'bad');
        hideCartStatusProgress(4000);
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = '🔄 Restore All Entries'; }
      }
    };

    // Actions: Empty Entire Cart Forever
    window.emptyEntireCartForever = async function() {
      const totalCusts = allCartCusts.length;
      const totalDevs = allCartDevs.length;
      const grandTotal = totalCusts + totalDevs;

      if (!grandTotal) {
        showToast('Cart is already empty.', 'info');
        return;
      }

      const ok = await askConfirm(
        `⚠️ PERMANENT PURGE WARNING:\\n\\nYou are about to permanently erase all ${grandTotal.toLocaleString()} items in the Cart (${totalCusts} whole customer portfolios and ${totalDevs} customer device entries).\\n\\nThis will drop all customer tables and permanently delete every record from the database and cloud storage forever.\\n\\nType "EMPTY" to proceed.`,
        { title: 'Permanently Empty Cart Forever?', okText: 'Empty Cart Forever', tone: 'danger', typeToConfirm: 'EMPTY' }
      );
      if (!ok) return;

      const btn = document.getElementById('btnEmptyCartForever');
      if (btn) { btn.disabled = true; btn.textContent = 'Emptying…'; }

      showCartStatusProgress({
        icon: '🗑️',
        spin: true,
        title: 'Emptying Cart Forever (Permanent Deletion)…',
        status: 'Dropping dedicated customer tables and purging all entries from TiDB Cloud…',
        pct: 40,
        rows: `0 / ${grandTotal} items`,
        tone: 'danger',
        detail: `Starting irreversible deletion for ${totalCusts} portfolios and ${totalDevs} device records…`
      });

      try {
        const res = await api('/api/bin', { method: 'DELETE' });
        showCartStatusProgress({
          icon: '🗑️',
          spin: false,
          title: 'Cart Permanently Emptied!',
          status: 'Permanent deletion complete — all items erased forever.',
          pct: 100,
          rows: `${grandTotal} / ${grandTotal} items`,
          tone: 'danger',
          detail: `✓ Successfully emptied ${res.deleted_forever || grandTotal} items forever from database and cloud!`,
          appendLog: true
        });
        showToast(`Cart permanently emptied! Deleted ${res.deleted_forever || grandTotal} items forever.`, 'ok');
        await loadCartContainer();
        hideCartStatusProgress(3000);
      } catch (err) {
        showCartStatusProgress({
          icon: '⚠️',
          spin: false,
          title: 'Failed to Empty Cart',
          status: err.message || 'Operation failed',
          pct: 0,
          tone: 'danger',
          detail: `Error: ${err.message || 'Unknown server error'}`,
          appendLog: true
        });
        showToast(err.message || 'Failed to empty cart', 'bad');
        hideCartStatusProgress(4000);
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = '🗑️ Empty Cart Forever'; }
      }
    };

    """

content = content[:idx1] + new_cart_actions + content[idx2:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully updated frontend/cart.html with live status monitor!")

