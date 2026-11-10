const { chromium } = require('playwright');
const { pathToFileURL } = require('url');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const target = pathToFileURL(path.resolve(__dirname, '../index.html')).href;
  const failures = [];
  for (const spec of [
    { label: 'desktop', width: 1440, height: 900, js: true },
    { label: 'ipad', width: 1024, height: 1366, js: true },
    { label: 'mobile', width: 390, height: 844, js: true },
    { label: 'ipad-nojs', width: 1024, height: 1366, js: false },
    { label: 'mobile-nojs', width: 390, height: 844, js: false },
  ]) {
    const context = await browser.newContext({ viewport: { width: spec.width, height: spec.height }, javaScriptEnabled: spec.js });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(String(e.message || e)));
    await page.goto(target, { waitUntil: 'load' });
    const districtCount = await page.locator('#cgDistrictMap .cg-poly').count();
    const rosterCount = await page.locator('.cg-district-choice').count();
    if (districtCount !== 33 || rosterCount !== 33) failures.push(spec.label + ': expected 33 polygons + choices, got ' + districtCount + ', ' + rosterCount);
    if (!await page.locator('#cg-map-hub').isVisible()) failures.push(spec.label + ': map hub not visible');
    if (spec.js) {
      const n = await page.evaluate(() => JSON.parse(document.getElementById('archiveData').textContent).length);
      const extra = await page.evaluate(() => JSON.parse(document.getElementById('cgMapHistoricData').textContent).length);
      if (n !== 182 || extra !== 14) failures.push(spec.label + ': archive/history mismatch ' + n + '/' + extra);
      await page.locator('.cg-poly[data-name="Sakti"]').click();
      if ((await page.locator('#cgDistrictTitle').textContent()).trim() !== 'Sakti') failures.push(spec.label + ': Sakti selection failed');
      if (+(await page.locator('#cgDistrictTotal').textContent()) < 1) failures.push(spec.label + ': Sakti missing historical records');
      await page.selectOption('#cgMapLeader', 'Deepak Baij');
      await page.locator('.cg-poly[data-name="Dantewada"]').click();
      if ((await page.locator('#cgDistrictTitle').textContent()).trim() !== 'Dantewada') failures.push(spec.label + ': Dantewada click failed');
      if (+(await page.locator('#cgDistrictTotal').textContent()) < 1) failures.push(spec.label + ': Dantewada historic leader filter missing');
      await page.selectOption('#cgMapType', 'events');
      if ((await page.locator('#cgMapType').inputValue()) !== 'events') failures.push(spec.label + ': event filter failed');
      await page.click('#cgMapReset');
      if ((await page.locator('#cgMapLeader').inputValue()) !== 'all') failures.push(spec.label + ': reset failed');
    }
    const overflow = await page.evaluate(() => Math.max(0, document.documentElement.scrollWidth - window.innerWidth));
    if (overflow > 28) failures.push(spec.label + ': horizontal overflow ' + overflow + 'px');
    if (errors.length) failures.push(spec.label + ': runtime errors ' + errors.slice(0,3).join(' | '));
    await page.screenshot({ path: path.resolve(__dirname, '../smoke-' + spec.label + '.png'), fullPage: false });
    console.log('SMOKE', spec.label, JSON.stringify({ districtCount, rosterCount, overflow, errors }));
    await context.close();
  }
  await browser.close();
  if (failures.length) { console.error('FAILURES:\n' + failures.join('\n')); process.exit(1); }
  console.log('PASS: all interactive and static browser smoke checks');
})().catch(e => { console.error(e); process.exit(1); });