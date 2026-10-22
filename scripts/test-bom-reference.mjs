// Browser-independent contract tests execute the real viewer script and exports.
// A separate local browser smoke covers actual DOM controls and downloads.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createContext, runInContext } from 'node:vm';
import test from 'node:test';

const root = new URL('../', import.meta.url);
const html = readFileSync(new URL('bom/index.html', root), 'utf8');
const script = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)]
    .map(m => m[1]).find(s => s.includes('const App ='));
const config = readFileSync(new URL('config.js', root), 'utf8');
const data = JSON.parse(readFileSync(new URL('bom/data.json', root), 'utf8'));

async function viewer(input = data) {
    const elements = new Map();
    const downloads = [];
    const blobs = new Map();
    let ready;
    function element() {
        return {
            style: {}, hidden: false, innerHTML: '',
            set textContent(value) { this.innerHTML = String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); },
            classList: { toggle() {}, add() {}, remove() {} },
            appendChild() {}, removeChild() {}, remove() {},
            click() { downloads.push({ name: this.download, blob: blobs.get(this.href) }); }
        };
    }
    class DownloadURL extends URL {}
    DownloadURL.createObjectURL = blob => { const id = `blob:test-${blobs.size}`; blobs.set(id, blob); return id; };
    DownloadURL.revokeObjectURL = () => {};
    const context = createContext({
        console, Blob, URL: DownloadURL, setTimeout() {},
        fetch: async () => ({ ok: true, json: async () => structuredClone(input) }),
        window: { open() { throw new Error('Unexpected external action'); } },
        document: {
            addEventListener(name, fn) { if (name === 'DOMContentLoaded') ready = fn; },
            getElementById(id) { if (!elements.has(id)) elements.set(id, element()); return elements.get(id); },
            createElement: element, body: element()
        }
    });
    runInContext(config + '\n' + script, context);
    await ready();
    return {
        run: code => runInContext(code, context),
        panel: id => elements.get(id),
        async exported(fn) {
            runInContext(`${fn}()`, context);
            const item = downloads.at(-1);
            assert.ok(item?.blob, `${fn} produced a downloadable file`);
            return { name: item.name, text: await item.blob.text() };
        }
    };
}

function csvRows(text) {
    const rows = []; let row = [], cell = '', quoted = false;
    for (let i = 0; i < text.length; i++) {
        const c = text[i];
        if (c === '"') { if (quoted && text[i + 1] === '"') { cell += '"'; i++; } else quoted = !quoted; }
        else if (c === ',' && !quoted) { row.push(cell); cell = ''; }
        else if (c === '\n' && !quoted) { row.push(cell); rows.push(row); row = []; cell = ''; }
        else cell += c;
    }
    row.push(cell); rows.push(row);
    const keys = rows.shift();
    return rows.map(values => Object.fromEntries(keys.map((k, i) => [k, values[i]])));
}

const partsFromJSON = value => value.categories.flatMap(c => c.parts);

test('default BOM and separate reference CAD/mount revisions are visible', async () => {
    const v = await viewer();
    assert.equal(v.run('App.activeModel'), 'M3-2');
    assert.equal(v.run('App.parts.length'), 74);
    const panel = v.panel('referenceCAD');
    assert.equal(panel.hidden, false);
    for (const text of ['158 modeled occurrences', '32 V-wheels', 'older boxed', 'New mount STL', data.version]) assert.ok(panel.innerHTML.includes(text), text);
    const rows = v.panel('bomContent').innerHTML;
    assert.ok(rows.includes('Older boxed STEP'));
    assert.ok(rows.includes('New open-access STL'));
    v.run('renderCADLibrary()');
    assert.ok(v.panel('cadLibraryBody').innerHTML.includes('New open-access STL'));
});

test('both models export their actual quantities and preserve the M3-2 CAD identity', async () => {
    const v = await viewer();
    for (const model of ['M3-1', 'M3-2']) {
        v.run(`setModel('${model}')`);
        const json = JSON.parse((await v.exported('exportJSON')).text);
        const manifest = JSON.parse((await v.exported('exportCADManifest')).text);
        assert.equal(json.model, model);
        assert.equal(manifest.model, model);
        assert.equal(json.bom_revision, data.version);
        assert.deepEqual(json.reference_assembly, data.reference_assembly);
        assert.equal(manifest.reference_assembly.model, 'M3-2');
        const expected = model === 'M3-1' ? 0 : data.parts.find(p => p.id === 5).qty;
        assert.equal(partsFromJSON(json).find(p => p.name === 'Straight Line Internal Connectors (20-Series)').qty, expected);
        assert.equal([...manifest.parts_with_cad, ...manifest.parts_without_cad].find(p => p.name === 'Straight Line Internal Connectors (20-Series)').qty, expected);
        for (const p of data.parts.filter(p => p.category !== 'Concrete Extrusion System')) {
            const display = JSON.parse(v.run(`JSON.stringify(getPartDisplay(App.parts.find(p => p.id === ${p.id})))`));
            const exported = [...manifest.parts_with_cad, ...manifest.parts_without_cad].find(x => x.name === display.name);
            assert.equal(exported.qty, display.qty);
            assert.equal(exported.unit, display.unit);
        }
        assert.equal(v.panel('referenceCAD').innerHTML.includes('selected BOM is M3-1'), model === 'M3-1');
    }
});

test('quantity, exclusion and Buy/Print/CNC selections survive CSV and JSON export', async () => {
    const v = await viewer();
    const mount = data.parts.find(p => p.id === 24);
    const option = mount.suppliers.find(s => s.approved);
    for (const method of ['buy', 'print', 'cnc']) {
        v.run(`App.userChoices = {}; adjustOrderQty(24, 2); toggleExclude(24, true); setMfgChoice(24, '${method}'); setPreferredSupplier(24, ${option.id})`);
        const json = JSON.parse((await v.exported('exportJSON')).text);
        const part = partsFromJSON(json).find(p => p.name === mount.name);
        assert.equal(part.qty, 4);
        assert.equal(part.order_qty, 6);
        assert.equal(part.user_excluded, true);
        assert.equal(part.user_build_method, method);
        assert.equal(part.user_preferred_supplier, option.supplier_name);
        assert.ok(part.suppliers.some(s => s.stl_url === data.reference_assembly.new_mount_stl_url));
        const csv = csvRows((await v.exported('exportCSV')).text).filter(p => p['Part Name'] === mount.name);
        for (const row of csv) {
            assert.equal(row['Order Qty'], '6'); assert.equal(row['User Excluded'], 'yes'); assert.equal(row['User Build Method'], method);
        }
        assert.ok(csv.some(row => row.Notes.includes(data.reference_assembly.new_mount_stl_url)));
    }
    v.run('resetOrderQty(24); toggleExclude(24, false); setMfgChoice(24, "cnc")');
    const reset = partsFromJSON(JSON.parse((await v.exported('exportJSON')).text)).find(p => p.name === mount.name);
    assert.equal(reset.order_qty, 4); assert.equal(reset.user_excluded, false); assert.equal(reset.user_build_method, null);
});

test('multi-supplier filtering retains custom choices and empty supplier gaps', async () => {
    const v = await viewer();
    v.run('adjustOrderQty(24, 1); toggleSupplierFilter("Amazon"); toggleSupplierFilter("Self-Manufacture")');
    const csv = await v.exported('exportCSV');
    assert.match(csv.name, /amazon\+self_manufacture/);
    const rows = csvRows(csv.text);
    assert.ok(rows.some(row => !row.Supplier));
    assert.ok(rows.every(row => !row.Supplier || /Amazon|Self-Manufacture/.test(row.Supplier)));
    assert.ok(rows.filter(row => row['Part Name'] === data.parts.find(p => p.id === 24).name).every(row => row['Order Qty'] === '5'));
    v.run('clearSupplierFilter()');
    assert.equal(v.run('App.activeSuppliers.size'), 0);
});

test('missing metadata hides the panel; hostile reference links and text are not rendered as markup', async () => {
    const missing = structuredClone(data); delete missing.reference_assembly;
    assert.equal((await viewer(missing)).panel('referenceCAD').hidden, true);
    const hostile = structuredClone(data);
    hostile.reference_assembly.step_url = 'javascript:alert(1)';
    hostile.reference_assembly.new_mount_stl_url = 'https://untrusted.invalid/file.stl';
    hostile.reference_assembly.scope_note = '<script>alert(1)</script>';
    const panel = (await viewer(hostile)).panel('referenceCAD').innerHTML;
    assert.ok(!panel.includes('javascript:') && !panel.includes('untrusted.invalid'));
    assert.ok(panel.includes('&lt;script&gt;'));
});
