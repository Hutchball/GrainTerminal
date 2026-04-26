// ── Grain Bot ─────────────────────────────────────────────────────────────────
// Read-only terminal knowledge assistant.
// Answers questions from embedded database only. Cannot modify data.
// Change requests are logged as pending notes for Paul's approval.
// ─────────────────────────────────────────────────────────────────────────────

(function () {
    'use strict';

    // ── State ─────────────────────────────────────────────────────────────────
    let panelOpen    = false;
    let changeNotes  = [];   // In-memory log of change requests this session
    let noteCounter  = 1;

    // ── Bootstrap (run after DOM ready) ───────────────────────────────────────
    document.addEventListener('DOMContentLoaded', function () {
        injectHTML();
    });

    function injectHTML() {
        const widget = document.createElement('div');
        widget.id = 'grainbot-root';
        widget.innerHTML = `
        <!-- Floating button -->
        <button id="grainbot-fab" class="grainbot-fab" onclick="GrainBot.toggle()" title="Ask Grain Bot">
            <span class="grainbot-fab-icon">🌾</span>
            <span class="grainbot-fab-label">Grain Bot</span>
        </button>

        <!-- Chat panel -->
        <div id="grainbot-panel" class="grainbot-panel grainbot-hidden">
            <div class="grainbot-header">
                <div class="grainbot-header-left">
                    <div class="grainbot-avatar">🌾</div>
                    <div>
                        <div class="grainbot-name">Grain Bot</div>
                        <div class="grainbot-status" id="grainbot-status">Terminal knowledge assistant</div>
                    </div>
                </div>
                <button class="grainbot-close" onclick="GrainBot.toggle()" title="Close">✕</button>
            </div>

            <div class="grainbot-messages" id="grainbot-messages"></div>

            <div class="grainbot-suggestions" id="grainbot-suggestions">
                <button onclick="GrainBot.ask('Roller codes for RB1')">RB1 roller codes</button>
                <button onclick="GrainBot.ask('BMH dimensions')">BMH dimensions</button>
                <button onclick="GrainBot.ask('What info is still required?')">Missing data</button>
                <button onclick="GrainBot.ask('How many drawings in MCC5?')">MCC5 drawings</button>
            </div>

            <div class="grainbot-input-row">
                <input  id="grainbot-input"
                        class="grainbot-input"
                        placeholder="Ask about the terminal…"
                        autocomplete="off"
                        onkeydown="if(event.key==='Enter')GrainBot.send()" />
                <button class="grainbot-send" onclick="GrainBot.send()">&#9658;</button>
            </div>

            <div class="grainbot-footer">
                Read-only · Data from verified records only · Change requests go to Paul
            </div>
        </div>`;
        document.body.appendChild(widget);
    }

    // ── Public API ────────────────────────────────────────────────────────────
    window.GrainBot = {

        toggle: function () {
            panelOpen = !panelOpen;
            const panel = document.getElementById('grainbot-panel');
            const fab   = document.getElementById('grainbot-fab');
            panel.classList.toggle('grainbot-hidden', !panelOpen);
            fab.classList.toggle('grainbot-fab-open', panelOpen);
            if (panelOpen) {
                if (document.getElementById('grainbot-messages').children.length === 0) {
                    greet();
                }
                setTimeout(() => document.getElementById('grainbot-input').focus(), 150);
            }
        },

        send: function () {
            const input = document.getElementById('grainbot-input');
            const text  = input.value.trim();
            if (!text) return;
            input.value = '';
            addMessage(text, 'user');
            hideSuggestions();
            setStatus('Thinking…');
            setTimeout(() => {
                const reply = query(text, text);
                addMessage(reply, 'bot');
                setStatus('Terminal knowledge assistant');
            }, 200);
        },

        ask: function (text) {
            document.getElementById('grainbot-input').value = text;
            GrainBot.send();
        }
    };

    // ── UI helpers ────────────────────────────────────────────────────────────
    function addMessage(html, sender) {
        const msgs = document.getElementById('grainbot-messages');
        const wrap = document.createElement('div');
        wrap.className = 'gb-msg-wrap gb-wrap-' + sender;

        const bubble = document.createElement('div');
        bubble.className = 'gb-msg gb-' + sender;
        if (sender === 'user') {
            bubble.textContent = html;
        } else {
            const reply = normaliseReply(html);
            bubble.innerHTML = reply.html + buildReplyFooter(reply);
        }
        wrap.appendChild(bubble);
        msgs.appendChild(wrap);
        msgs.scrollTop = msgs.scrollHeight;
    }

    function greet() {
        addMessage(
            `Hi, I'm <strong>Grain Bot</strong> 🌾<br>
I can answer questions about Seaforth Grain Terminal using the verified data in this database.<br><br>
Try asking me:<br>
&nbsp;• <em>"What rollers does RB1 use?"</em><br>
&nbsp;• <em>"What components does Main Elevator 2 have?"</em><br>
&nbsp;• <em>"BMH ship unloader dimensions"</em><br>
&nbsp;• <em>"How many drawings in MCC3?"</em><br>
&nbsp;• <em>"What info is still required?"</em><br><br>
To request a data change, say: <em>"Please note that…"</em> and I will log it for Paul's approval.<br><br>
<span class="gb-warning">⚠ I only work from verified records. I will not guess or make anything up.</span>`,
            'bot'
        );
    }

    function setStatus(text) {
        const el = document.getElementById('grainbot-status');
        if (el) el.textContent = text;
    }

    function normaliseReply(reply) {
        if (reply && typeof reply === 'object' && typeof reply.html === 'string') return reply;
        return { html: String(reply || ''), sources: [], feedback: true };
    }

    function dedupeSources(sources) {
        const seen = new Set();
        return (sources || []).filter(source => {
            if (!source || !source.link) return false;
            const key = `${source.link}|${source.label || ''}`;
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });
    }

    function sourceFromDocument(doc) {
        if (!doc || !doc.pdf_link) return null;
        return {
            label: doc.drawing_ref || doc.description || doc.filename,
            path: doc.file_path,
            link: doc.pdf_link,
        };
    }

    function buildReplyFooter(reply) {
        const sources = dedupeSources(reply.sources || []);
        const sourceHtml = sources.length > 0
            ? `<div class="gb-source-box">
                <div class="gb-source-title">Check the original file:</div>
                <div class="gb-source-links">
                    ${sources.map(source => `<a href="${source.link}" target="_blank" rel="noopener">${esc(source.label || 'Source')}</a>`).join('')}
                </div>
            </div>`
            : `<div class="gb-source-box gb-source-missing">No direct source link attached to this reply yet.</div>`;
        const feedbackHtml = reply.feedback === false || !window.PKAFeedback
            ? ''
            : window.PKAFeedback.renderPanel({
                item_type: 'grainbot_answer',
                item_id: reply.itemId || '',
                item_label: reply.itemLabel || 'Grain Bot answer',
                query_text: reply.queryText || '',
                response_text: reply.plainText || reply.html.replace(/<[^>]+>/g, ' ').trim(),
                sources,
                channel: 'grainbot',
            }, true);
        return `<div class="gb-reply-footer">${sourceHtml}${feedbackHtml}</div>`;
    }

    function hideSuggestions() {
        const el = document.getElementById('grainbot-suggestions');
        if (el) el.style.display = 'none';
    }

    function esc(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    function specBadge(text) {
        return `<span class="gb-spec">${esc(text)}</span>`;
    }

    // ── Query router ──────────────────────────────────────────────────────────
    function query(raw, originalQuery) {
        const q = raw.toLowerCase().trim();

        // Guard: data not loaded yet
        if (typeof DATA_LAYOUT === 'undefined') {
            return { html: 'The database is still loading — please try again in a moment.', sources: [], queryText: originalQuery || raw };
        }

        // Change / note request
        if (/\b(please note|note that|add a note|change request|request to (add|change|update)|update request|record that|log that)\b/.test(q)) {
            return handleChangeRequest(raw);
        }

        // Help
        if (/^help$|what can you (do|tell|answer)|how (do i use|does this work)/.test(q)) {
            return helpText();
        }

        // Roller codes — check before general asset lookup so "rollers for RB1" is caught
        if (/roller/.test(q)) {
            return rollerQuery(q);
        }

        // Drawing / MCC count
        if (/\b(mcc\d+|mcc\s\d+|drawing|schematic|scp|scale room)\b/.test(q)) {
            return drawingQuery(q, raw);
        }

        // Stats
        if (/how many (drawings|schematics|pdf)/.test(q)) return statsDrawings(q);
        if (/how many (assets|items|machines|pieces of equipment)/.test(q)) return statsAssets();

        // BMH / Siwertell / ship unloader
        if (/\b(bmh|ship unloader|siwertell|unloader)\b/.test(q)) {
            return bmhQuery(q);
        }

        // Info required / missing data
        if (/\b(info.?required|missing data|awaiting data|not yet recorded|unknown|what.*still needed|what.*still required)\b/.test(q)) {
            return infoRequiredList(q);
        }

        // Specific asset lookup
        const found = findAsset(q);
        if (found) return assetResponse(found.asset, found.location);

        // Location overview
        const loc = findLocation(q);
        if (loc) return locationResponse(loc);

        // No match
        return {
            html: `I couldn't find data matching <em>"${esc(raw)}"</em> in the database.<br><br>
I can only answer from verified records. Try being more specific — e.g. name the belt, elevator, or drawing reference — or type <strong>help</strong> for examples.`,
            sources: [],
            queryText: originalQuery || raw,
        };
    }

    // ── Handlers ──────────────────────────────────────────────────────────────

    function helpText() {
        return { html: `<strong>What I can answer:</strong><br><br>
<strong>Equipment & components</strong><br>
&nbsp;• <em>"What components does RB5 have?"</em><br>
&nbsp;• <em>"Show me Main Elevator 3"</em><br>
&nbsp;• <em>"What's in the Receiving area?"</em><br><br>
<strong>Roller codes</strong><br>
&nbsp;• <em>"Roller codes for RB1"</em><br>
&nbsp;• <em>"What rollers does Basement Belt 2 use?"</em><br><br>
<strong>BMH / Ship Unloader</strong><br>
&nbsp;• <em>"BMH dimensions"</em><br>
&nbsp;• <em>"What is the leg length of the ship unloader?"</em><br><br>
<strong>Drawings</strong><br>
&nbsp;• <em>"How many drawings in MCC2?"</em><br>
&nbsp;• <em>"Find drawing DTX-361-AA"</em><br><br>
<strong>Missing data</strong><br>
&nbsp;• <em>"What info is still required?"</em><br>
&nbsp;• <em>"What's missing for the BMH?"</em><br><br>
<strong>Change requests (logged for Paul's approval)</strong><br>
&nbsp;• <em>"Please note that Compressor 1 is an Atlas Copco GA55"</em>`, feedback: false };
    }

    function rollerQuery(q) {
        const beltId = extractBeltId(q);
        let results  = [];

        DATA_LAYOUT.locations.forEach(loc => {
            loc.assets.forEach(asset => {
                const idUp   = asset.id.toUpperCase();
                const nameUp = asset.name.toUpperCase();
                const match  = beltId
                    ? idUp === beltId || idUp.includes(beltId) || nameUp.includes(beltId)
                    : false;
                if (match) {
                    const rollers = asset.components.filter(c => /roller/i.test(c.name));
                    if (rollers.length > 0) results.push({ asset, loc, rollers });
                }
            });
        });

        if (results.length === 0 && beltId) {
            return { html: `No roller data found for <strong>${beltId}</strong>. That asset may not yet be in the database, or roller codes have not been recorded for it.`, sources: [] };
        }
        if (results.length === 0) {
            return { html: `Please specify which belt you need roller codes for, e.g. <em>"Roller codes for RB1"</em>`, sources: [] };
        }

        let html = '';
        results.forEach(r => {
            html += `<strong>${r.asset.name}</strong> — ${r.loc.name}<br>`;
            r.rollers.forEach(c => {
                html += `&nbsp;• ${esc(c.name)}: `;
                html += c.spec ? specBadge(c.spec) : '<em class="gb-awaiting">Awaiting data</em>';
                html += '<br>';
            });
            html += `<small class="gb-source">Source: Rulmeca reference sheet (Roller_Codes_Rulmeca.jpeg)</small>`;
        });
        return {
            html,
            itemId: beltId || 'roller-query',
            itemLabel: `Roller data ${beltId || ''}`.trim(),
            sources: dedupeSources([
                sourceFromDocument(DATA_DOCUMENTS.find(d => (d.file_path || '').includes('Roller_Codes_Rulmeca.jpeg'))),
                sourceFromDocument(DATA_DOCUMENTS.find(d => (d.file_path || '').includes('Roller_Codes.html'))),
                window.PKASources ? window.PKASources.layoutRegisterSource : null,
            ]),
        };
    }

    function statsDrawings(q) {
        const total   = DATA_STATS.electrical_drawings || 0;
        const obsolete = DATA_STATS.obsolete_drawings  || 0;
        const mccM    = q.match(/mcc\s*(\d+)/i);
        if (mccM) {
            const key   = 'MCC' + mccM[1];
            const count = DATA_STATS.mcc_counts && DATA_STATS.mcc_counts[key];
            if (count != null) {
                return {
                    html: `<strong>${key}</strong> has <strong>${count}</strong> drawings in the database.`,
                    itemId: key,
                    itemLabel: `${key} drawings`,
                    sources: dedupeSources(DATA_DOCUMENTS.filter(d => d.mcc === key).slice(0, 8).map(sourceFromDocument)),
                };
            }
            return { html: `I don't have a drawing count specifically for MCC${mccM[1]}.`, sources: [] };
        }
        if (/scp/.test(q)) {
            const c = DATA_STATS.mcc_counts && DATA_STATS.mcc_counts['SCP'];
            if (c != null) {
                return {
                    html: `<strong>SCP (System Control Panel)</strong> has <strong>${c}</strong> drawings.`,
                    itemId: 'SCP',
                    itemLabel: 'SCP drawings',
                    sources: dedupeSources(DATA_DOCUMENTS.filter(d => d.mcc === 'SCP').slice(0, 8).map(sourceFromDocument)),
                };
            }
        }
        return {
            html: `The database holds <strong>${total}</strong> active electrical drawings and <strong>${obsolete}</strong> obsolete drawings across all switchrooms.`,
            itemId: 'all-drawings',
            itemLabel: 'All drawings summary',
            sources: dedupeSources(DATA_DOCUMENTS.filter(d => d.category === 'electrical_drawing').slice(0, 10).map(sourceFromDocument)),
        };
    }

    function statsAssets() {
        let count = 0;
        DATA_LAYOUT.locations.forEach(l => count += l.assets.length);
        return {
            html: `There are currently <strong>${count}</strong> assets recorded across <strong>${DATA_LAYOUT.locations.length}</strong> locations. This list is incomplete — more data is being added.`,
            itemId: 'asset-count',
            itemLabel: 'Asset count',
            sources: [window.PKASources ? window.PKASources.layoutRegisterSource : null],
        };
    }

    function drawingQuery(q, raw) {
        // MCC count query
        const mccM = q.match(/mcc\s*(\d+)/i);
        if (mccM) {
            const key   = 'MCC' + mccM[1];
            const count = DATA_STATS.mcc_counts && DATA_STATS.mcc_counts[key];
            if (count != null) {
                return {
                    html: `<strong>${key}</strong> has <strong>${count}</strong> drawings in the database.`,
                    itemId: key,
                    itemLabel: `${key} drawings`,
                    sources: dedupeSources(DATA_DOCUMENTS.filter(d => d.mcc === key).slice(0, 8).map(sourceFromDocument)),
                };
            }
            return { html: `I don't have a drawing count for MCC${mccM[1]}.`, sources: [] };
        }
        if (/scp/.test(q)) {
            const c = DATA_STATS.mcc_counts && DATA_STATS.mcc_counts['SCP'];
            if (c != null) {
                return {
                    html: `<strong>SCP</strong> has <strong>${c}</strong> drawings.`,
                    itemId: 'SCP',
                    itemLabel: 'SCP drawings',
                    sources: dedupeSources(DATA_DOCUMENTS.filter(d => d.mcc === 'SCP').slice(0, 8).map(sourceFromDocument)),
                };
            }
        }
        // Drawing ref search
        const refM = q.match(/([a-z]{2,5}[-\s]\d{3}[-\s][a-z0-9]{1,3})/i);
        if (refM) {
            const ref    = refM[1].replace(/\s/g, '-').toUpperCase();
            const hits   = DATA_DOCUMENTS.filter(d =>
                d.drawing_ref && d.drawing_ref.toUpperCase().includes(ref)
            );
            if (hits.length > 0) {
                let html = `Found <strong>${hits.length}</strong> drawing(s) matching <strong>${esc(ref)}</strong>:<br><br>`;
                hits.slice(0, 8).forEach(d => {
                    html += `&nbsp;• <strong>${esc(d.drawing_ref)}</strong>`;
                    if (d.description) html += ` — ${esc(d.description)}`;
                    if (d.mcc)         html += ` <em>(${esc(d.mcc)})</em>`;
                    if (d.status === 'obsolete') html += ' <span class="gb-obsolete">OBSOLETE</span>';
                    html += '<br>';
                });
                if (hits.length > 8) html += `<br>&nbsp;…and ${hits.length - 8} more.`;
                return {
                    html,
                    itemId: ref,
                    itemLabel: `Drawing ${ref}`,
                    sources: dedupeSources(hits.slice(0, 8).map(sourceFromDocument)),
                };
            }
            return { html: `No drawings found matching reference <strong>${esc(ref)}</strong>.`, sources: [] };
        }
        return statsDrawings(q);
    }

    function bmhQuery(q) {
        let asset = null, loc = null;
        DATA_LAYOUT.locations.forEach(l => {
            l.assets.forEach(a => {
                if (/bmh|siwertell|ship.?unloader/i.test(a.name) || /bmh|ship.?unloader/i.test(l.name)) {
                    asset = a; loc = l;
                }
            });
        });
        if (!asset) return { html: 'BMH Ship Unloader data is not yet in the database.', sources: [] };

        // Specific dimension queries
        if (/leg|design length/.test(q)) {
            const c = asset.components.find(c => /leg/i.test(c.name));
            if (c && c.spec) return {
                html: `Siwertell screw conveyor <strong>leg design length</strong>: ${specBadge(c.spec)}`,
                itemId: 'BMH-leg',
                itemLabel: 'BMH leg length',
                sources: [sourceFromDocument(DATA_DOCUMENTS.find(d => (d.file_path || '').includes('Siwertell_Ship_Unloader_Overview.jpg')))],
            };
        }
        if (/boom|arm|span|reach/.test(q)) {
            const c = asset.components.find(c => /boom/i.test(c.name));
            if (c && c.spec) return {
                html: `BMH <strong>boom arm overall span</strong>: ${specBadge(c.spec)}`,
                itemId: 'BMH-boom',
                itemLabel: 'BMH boom span',
                sources: [sourceFromDocument(DATA_DOCUMENTS.find(d => (d.file_path || '').includes('Siwertell_Ship_Unloader_Overview.jpg')))],
            };
        }
        if (/hoist/.test(q)) {
            const c = asset.components.find(c => /hoist/i.test(c.name));
            if (c && c.spec) return {
                html: `<strong>Auxiliary hoist</strong>: ${specBadge(c.spec)}`,
                itemId: 'BMH-hoist',
                itemLabel: 'BMH auxiliary hoist',
                sources: [sourceFromDocument(DATA_DOCUMENTS.find(d => (d.file_path || '').includes('Siwertell_Ship_Unloader_Overview.jpg')))],
            };
        }
        if (/free height|clearance/.test(q)) {
            const c = asset.components.find(c => /free height/i.test(c.name));
            if (c && c.spec) return {
                html: `<strong>Free height (clearance)</strong>: ${specBadge(c.spec)}`,
                itemId: 'BMH-clearance',
                itemLabel: 'BMH clearance',
                sources: [sourceFromDocument(DATA_DOCUMENTS.find(d => (d.file_path || '').includes('Siwertell_Ship_Unloader_Overview.jpg')))],
            };
        }
        if (/rail|travel/.test(q)) {
            const c = asset.components.find(c => /travel/i.test(c.name));
            if (c && c.spec) return {
                html: `<strong>Travel rail length</strong>: ${specBadge(c.spec)}`,
                itemId: 'BMH-travel',
                itemLabel: 'BMH travel rail length',
                sources: [sourceFromDocument(DATA_DOCUMENTS.find(d => (d.file_path || '').includes('Siwertell_Ship_Unloader_Overview.jpg')))],
            };
        }

        // General BMH overview
        return assetResponse(asset, loc);
    }

    function infoRequiredList(q) {
        let items = [];
        DATA_LAYOUT.locations.forEach(loc => {
            loc.assets.forEach(asset => {
                asset.components
                    .filter(c => c.category === 'info_required')
                    .forEach(c => items.push({ locName: loc.name, assetName: asset.name, field: c.name }));
            });
        });

        // Filter by area if mentioned
        if (/receiv/.test(q))             items = items.filter(i => /receiv/i.test(i.locName));
        else if (/silo/.test(q))          items = items.filter(i => /silo/i.test(i.locName));
        else if (/bmh|ship|siwertell/.test(q)) items = items.filter(i => /bmh/i.test(i.locName));

        if (items.length === 0) {
            return {
                html: 'No fields currently flagged as Info Required — either everything is recorded, or no matching assets were found.',
                sources: [window.PKASources ? window.PKASources.layoutRegisterSource : null],
            };
        }

        let html = `<strong>${items.length}</strong> field(s) still require data:<br><br>`;
        let lastAsset = null;
        items.slice(0, 25).forEach(i => {
            if (i.assetName !== lastAsset) {
                html += `<strong>${esc(i.assetName)}</strong> <em class="gb-loc">(${esc(i.locName)})</em><br>`;
                lastAsset = i.assetName;
            }
            html += `&nbsp;• ${esc(i.field)}<br>`;
        });
        if (items.length > 25) {
            html += `<br><em>…and ${items.length - 25} more. Open the Equipment tab to see all.</em>`;
        }
        return {
            html,
            itemId: 'info-required',
            itemLabel: 'Missing information list',
            sources: [window.PKASources ? window.PKASources.layoutRegisterSource : null],
        };
    }

    function assetResponse(asset, loc) {
        const typeLabel = (typeof TYPE_LABELS !== 'undefined' && TYPE_LABELS[asset.type]) || asset.type || '';
        let html = `<strong>${esc(asset.name)}</strong>`;
        if (loc)       html += ` — <em class="gb-loc">${esc(loc.name)}</em>`;
        if (typeLabel) html += `<br><span class="gb-type">${esc(typeLabel)}</span>`;
        if (asset.notes) html += `<br><small>${esc(asset.notes)}</small>`;
        html += '<br><br>';

        const groups = { electrical: [], mechanical: [], dust_control: [], info_required: [] };
        asset.components.forEach(c => {
            (groups[c.category] || groups.mechanical).push(c);
        });

        const catMeta = {
            electrical:    { label: '⚡ Electrical',    colour: '#4299e1' },
            mechanical:    { label: '⚙️ Mechanical',    colour: '#ed8936' },
            dust_control:  { label: '💨 Dust Control',  colour: '#68d391' },
            info_required: { label: '❓ Info Required', colour: '#fc8181' },
        };

        Object.entries(catMeta).forEach(([cat, meta]) => {
            const comps = groups[cat];
            if (!comps || comps.length === 0) return;
            html += `<span style="color:${meta.colour};font-weight:600">${meta.label}</span><br>`;
            comps.forEach(c => {
                html += `&nbsp;• ${esc(c.name)}`;
                if (c.spec) html += `: ${specBadge(c.spec)}`;
                html += '<br>';
            });
            html += '<br>';
        });

        const matchedEquipment = (typeof allEquipment !== 'undefined' ? allEquipment : []).filter(e =>
            e.name.toUpperCase().includes(asset.name.toUpperCase()) ||
            asset.name.toUpperCase().includes(e.name.toUpperCase())
        );
        return {
            html: html.trimEnd(),
            itemId: asset.id,
            itemLabel: asset.name,
            sources: window.PKASources ? window.PKASources.gatherSourcesForAsset(asset, matchedEquipment) : [],
        };
    }

    function locationResponse(loc) {
        const count = loc.assets.length;
        let html = `<strong>${esc(loc.name)}</strong> — ${count} asset${count !== 1 ? 's' : ''}:<br><br>`;
        loc.assets.forEach(a => {
            const infoN = a.components.filter(c => c.category === 'info_required').length;
            const tLabel = (typeof TYPE_LABELS !== 'undefined' && TYPE_LABELS[a.type]) || a.type || 'Equipment';
            html += `&nbsp;• <strong>${esc(a.name)}</strong> <em>(${esc(tLabel)})</em>`;
            if (infoN > 0) html += ` <span style="color:#fc8181">— ${infoN} info needed</span>`;
            html += '<br>';
        });
        return {
            html,
            itemId: loc.id,
            itemLabel: loc.name,
            sources: [window.PKASources ? window.PKASources.layoutRegisterSource : null],
        };
    }

    function handleChangeRequest(raw) {
        const ts  = new Date().toLocaleString('en-GB', { dateStyle: 'short', timeStyle: 'short' });
        const ref = 'CR-' + String(noteCounter++).padStart(3, '0') + '-' + Date.now().toString(36).toUpperCase();
        changeNotes.push({ ref, ts, request: raw, status: 'Pending' });

        return { html: `<strong>Change request logged ✓</strong><br><br>
<div class="gb-cr-box">
  <div><strong>Ref:</strong> ${esc(ref)}</div>
  <div><strong>Time:</strong> ${esc(ts)}</div>
  <div><strong>Request:</strong> ${esc(raw)}</div>
  <div><strong>Status:</strong> <span style="color:#ed8936">Pending Paul's approval</span></div>
</div>
<small>This has <strong>not</strong> been applied to the database. Paul will review and approve before any change is made. Quote the ref above if following up.</small>`, feedback: false };
    }

    // ── Data helpers ──────────────────────────────────────────────────────────

    function findAsset(q) {
        // Direct ID match first (e.g. "rb1", "rb 1", "rb-1")
        const normId = q.replace(/[\s\-_]/g, '').toUpperCase();
        for (const loc of DATA_LAYOUT.locations) {
            for (const asset of loc.assets) {
                if (asset.id.replace(/_/g, '').toUpperCase() === normId) return { asset, location: loc };
                if (asset.name.replace(/[\s\-_]/g, '').toUpperCase() === normId) return { asset, location: loc };
            }
        }

        // Token scoring
        const tokens = q.replace(/[^a-z0-9\s]/g, ' ').split(/\s+/).filter(t => t.length >= 2);
        let best = null, bestScore = 0;
        DATA_LAYOUT.locations.forEach(loc => {
            loc.assets.forEach(asset => {
                const name = asset.name.toLowerCase();
                const id   = asset.id.toLowerCase().replace(/_/g, ' ');
                let score  = 0;
                tokens.forEach(t => {
                    if (name.includes(t) || id.includes(t)) score++;
                });
                if (score > bestScore) { bestScore = score; best = { asset, location: loc }; }
            });
        });
        return bestScore >= 2 ? best : null;
    }

    function findLocation(q) {
        return DATA_LAYOUT.locations.find(loc =>
            q.includes(loc.name.toLowerCase()) || q.includes(loc.id.toLowerCase())
        ) || null;
    }

    function extractBeltId(q) {
        // e.g. "rb1", "rb 1", "rb-1" → "RB1"
        let m = q.match(/\b(rb\s*\d+|rc\s*\d+|me\s*\d+)\b/);
        if (m) return m[1].replace(/[\s\-]/g, '').toUpperCase();

        // "basement belt 1" → "SILO1_BB1"
        m = q.match(/basement belt\s*(\d+)/);
        if (m) return 'SILO1_BB' + m[1];

        // "main elevator 1" → "SILO1_ME1"
        m = q.match(/main elevator\s*(\d+)/);
        if (m) return 'SILO1_ME' + m[1];

        // "junction house elevator 1"
        m = q.match(/junction house elevator\s*(\d+)/);
        if (m) return 'JH_ELEVATOR_' + m[1];

        return null;
    }

})();
