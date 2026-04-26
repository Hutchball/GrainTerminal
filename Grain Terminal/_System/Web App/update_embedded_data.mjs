import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const base = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(base, 'data');
const appPath = path.join(base, 'app.js');

const json = (name) => JSON.parse(fs.readFileSync(path.join(dataDir, name), 'utf8'));
const compact = (value) => JSON.stringify(value);

const block = [
  '// ── Embedded data (auto-generated — do not edit manually) ───────────────────',
  `const DATA_STATS = ${compact(json('stats.json'))};`,
  `const DATA_DOCUMENTS = ${compact(json('documents.json'))};`,
  `const DATA_EQUIPMENT = ${compact(json('equipment.json'))};`,
  `const DATA_ATTRS = ${compact(json('equipment_attributes.json'))};`,
  `const DATA_RELATIONS = ${compact(json('equipment_relationships.json'))};`,
  `const DATA_PHOTOS = ${compact(json('photos.json'))};`,
  `const DATA_LAYOUT = ${compact(json('site_layout.json'))};`,
  `const DATA_LUBRICANTS = ${compact(json('lubricants.json'))};`,
  `const DATA_EQUIPMENT_LUBRICANTS = ${compact(json('equipment_lubricants.json'))};`,
  `const DATA_EQUIPMENT_PULLEYS = ${compact(json('equipment_pulleys.json'))};`,
  `const DATA_EQUIPMENT_GEARBOXES = ${compact(json('equipment_gearboxes.json'))};`,
  `const DATA_ELECTRICAL_MOTORS = ${compact(json('electrical_motors.json'))};`,
  `const DATA_DUST_BAG_STOCK = ${compact(json('dust_bag_stock.json'))};`,
  `const DATA_EQUIPMENT_DUST_BAGS = ${compact(json('equipment_dust_bags.json'))};`,
  `const DATA_DUST_BAG_CHANGE_HISTORY = ${compact(json('dust_bag_change_history.json'))};`,
  '',
].join('\n');

const app = fs.readFileSync(appPath, 'utf8');
const marker = '// Port of Liverpool Grain Terminal';
const markerIndex = app.indexOf(marker);
if (markerIndex === -1) {
  throw new Error(`Could not find marker: ${marker}`);
}

fs.writeFileSync(appPath, block + app.slice(markerIndex), 'utf8');
console.log('Embedded app.js data refreshed.');
