from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RUNTIME = (ROOT / "static" / "landing-runtime-safe.js").read_text(encoding="utf-8")


def test_private_beta_pricing_note_does_not_advertise_available_annual_discount():
    assert "alignPrivateBetaPricingCopy" in RUNTIME
    assert "Priser exkl. moms. Årsbetalning öppnas efter privat beta." in RUNTIME
    assert "Prices exclude VAT. Annual billing opens after the private beta." in RUNTIME
    assert "alignPrivateBetaPricingCopy();" in RUNTIME


def test_premium_visual_pass_keeps_annual_billing_locked():
    import subprocess

    script = r'''
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const sv = {}, en = {}, attributes = new Map();
const yearly = {disabled:false,
  setAttribute(k,v){attributes.set(k,v);},
  querySelector(s){return s === '.pricing-sv' ? sv : en;}};
const context = vm.createContext({
  window:{}, localStorage:{getItem(){return '1';}},
  document:{readyState:'loading',
    documentElement:{dataset:{vexmeraSoundInstalled:'1'}},
    querySelector(s){return s === '[data-billing="yearly"]' ? yearly : {};},
    addEventListener(){}}
});
let source = fs.readFileSync('static/landing-premium.js','utf8');
// Expose the shipped function only in this isolated offline test context.
source = source.replace(/\}\)\(\);\s*$/, 'window.lockAnnualBilling=lockAnnualBilling;})();');
vm.runInContext(source,context);
context.window.lockAnnualBilling();
assert.equal(yearly.disabled,true);
assert.equal(attributes.get('aria-disabled'),'true');
assert.equal(sv.textContent,'Efter privat beta');
assert.equal(en.textContent,'After private beta');
// A repeated visual pass must preserve the billing lock.
context.window.lockAnnualBilling();
assert.equal(yearly.disabled,true);
'''
    result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
