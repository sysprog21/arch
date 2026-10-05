// Run with node tests/test_homework1.js; checks the actual picker script.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const page = fs.readFileSync(`${__dirname}/../homework1.html`, 'utf8');
assert.match(page, /<html lang="en">/);
assert.doesNotMatch(page, /[\u3400-\u9fff]/);
assert.match(page, /{% if fork.has_updates %} \*{% endif %}/);
const rows = ['Alice', 'alex', 'Bob'].map(owner => ({
  dataset: { owner },
  querySelector: () => ({ textContent: `${owner}/minirubik${owner === 'Alice' ? ' *' : ''}`, href: `https://github.com/${owner}/minirubik` })
}));
const elements = Object.fromEntries(['prefix', 'fork-picker', 'selected', 'matches'].map(id =>
  [id, { value: '', listeners: {}, addEventListener(type, fn) { this.listeners[type] = fn; } }]));
const picker = elements['fork-picker'];
picker.options = [{}];
Object.defineProperty(picker, 'length', { set(length) { this.options.length = length; } });
picker.add = option => picker.options.push(option);
vm.runInNewContext(fs.readFileSync(`${__dirname}/../assets/js/homework1.js`, 'utf8'), {
  document: { getElementById: id => elements[id], querySelectorAll: () => rows },
  Option: function(textContent, value) { Object.assign(this, { textContent, value }); }
});
assert.equal(picker.options.length, 4);
elements.prefix.value = ' AL ';
elements.prefix.listeners.input();
assert.deepEqual(rows.map(row => row.hidden), [false, false, true]);
assert.equal(picker.options.length, 3);
picker.value = picker.options[1].value;
picker.selectedOptions = [picker.options[1]];
picker.listeners.change();
assert.equal(elements.selected.href, 'https://github.com/Alice/minirubik');
assert.equal(elements.selected.hidden, false);
assert.equal(elements.selected.textContent, 'Open Alice/minirubik *');
elements.prefix.value = 'nobody';
elements.prefix.listeners.input();
assert.equal(picker.disabled, true);
assert.equal(elements.selected.hidden, true);
assert.equal(elements.matches.textContent, '0 matching / 3 total forks');
console.log('homework1 picker checks passed');
