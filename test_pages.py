import asyncio
import json
import os
import subprocess
import time
import urllib.request
import websockets

pages = [
    'index.html',
    'profile.html',
    '3d-view.html',
    'types.html',
    'gallery.html',
    'contact.html',
    'safety.html'
]

viewports = [
    (320, 650, 'Tiny Mobile (320px)'),
    (360, 740, 'Galaxy S8 (360px)'),
    (375, 667, 'iPhone SE (375px)'),
    (390, 844, 'iPhone 14 (390px)'),
    (412, 915, 'Pixel 7 (412px)'),
    (480, 850, 'Large Mobile (480px)'),
    (768, 1024, 'Tablet (768px)'),
    (1024, 768, 'Laptop (1024px)'),
    (1440, 900, 'Desktop (1440px)')
]

async def run():
    p = subprocess.Popen([
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new',
        '--remote-debugging-port=9222',
        r'--user-data-dir=C:\Users\hplap\AppData\Local\Temp\cd_verify_runner_v2'
    ])
    time.sleep(1.2)
    try:
        res = urllib.request.urlopen('http://localhost:9222/json')
        targets = json.loads(res.read().decode())
        page_target = [t for t in targets if t['type'] == 'page'][0]
        
        async with websockets.connect(page_target['webSocketDebuggerUrl'], max_size=50_000_000) as ws:
            msg_counter = [0]
            
            async def cmd(method, params=None):
                msg_counter[0] += 1
                cid = msg_counter[0]
                await ws.send(json.dumps({'id': cid, 'method': method, 'params': params or {}}))
                while True:
                    data = json.loads(await ws.recv())
                    if data.get('id') == cid:
                        return data.get('result', {})

            await cmd('Page.enable')
            await cmd('Runtime.enable')

            overflow_failures = []
            touch_warnings = []
            name_check_failures = []

            for page in pages:
                abs_path = os.path.abspath(page).replace('\\', '/')
                url = f'file:///{abs_path}'
                print(f"\n========================================\nPAGE: {page}\n========================================")

                for w, h, vp_label in viewports:
                    await cmd('Emulation.setDeviceMetricsOverride', {
                        'width': w,
                        'height': h,
                        'deviceScaleFactor': 1,
                        'mobile': w <= 768
                    })
                    await cmd('Page.navigate', {'url': url})
                    
                    # Ensure document is fully parsed and stylesheets applied
                    for _ in range(30):
                        r_state = await cmd('Runtime.evaluate', {'expression': 'document.readyState'})
                        if r_state.get('result', {}).get('value') == 'complete':
                            break
                        await asyncio.sleep(0.04)
                    await asyncio.sleep(0.2)

                    res = await cmd('Runtime.evaluate', {
                        'expression': '''
                        (() => {
                            const cw = document.documentElement.clientWidth;
                            const sw = document.documentElement.scrollWidth;
                            const bw = document.body ? document.body.scrollWidth : 0;
                            const hasOverflow = (sw > cw + 1) || (bw > cw + 1);

                            // Find overflowing elements (ignoring hidden drawer elements when drawer is closed)
                            const overElements = [];
                            if (hasOverflow) {
                                document.querySelectorAll('*').forEach(el => {
                                    if (el.closest('.mobile-nav-drawer:not(.open)')) return;
                                    if (el.offsetParent === null && el.tagName !== 'BODY') return;
                                    const r = el.getBoundingClientRect();
                                    if (r.right > cw + 1.5) {
                                        overElements.push({
                                            tag: el.tagName,
                                            cls: (el.className || '').toString().slice(0, 40),
                                            id: el.id,
                                            right: Math.round(r.right),
                                            width: Math.round(r.width),
                                            cw: cw
                                        });
                                    }
                                });
                            }

                            // Touch targets check on mobile (w <= 480)
                            const touchIssues = [];
                            if (cw <= 480) {
                                const interactives = document.querySelectorAll('button, a, input, select, textarea');
                                interactives.forEach(el => {
                                    if (el.closest('.mobile-nav-drawer:not(.open)')) return;
                                    if (el.closest('.floating-widget:not(.mobile-open):not(.open)')) return;
                                    if (!el.offsetParent) return;
                                    const r = el.getBoundingClientRect();
                                    // check if height or width is too small (< 40px)
                                    if (r.width > 0 && r.height > 0 && (r.height < 40 || r.width < 40)) {
                                        const isInlineText = el.tagName === 'A' && el.closest('p, .footer-copy, .map-card-body');
                                        if (!isInlineText) {
                                            touchIssues.push({
                                                tag: el.tagName,
                                                cls: (el.className || '').toString().slice(0, 30),
                                                id: el.id,
                                                text: (el.innerText || el.ariaLabel || el.getAttribute('aria-label') || '').trim().slice(0, 25),
                                                w: Math.round(r.width),
                                                h: Math.round(r.height)
                                            });
                                        }
                                    }
                                });
                            }

                            const fullText = (document.body ? document.body.innerText : '') + ' ' + document.title + ' ' + (document.querySelector('meta[name="description"]')?.content || '');
                            const hasSuresh = /suresh/i.test(fullText);
                            const hasNarendra = /narendra/i.test(fullText);
                            const authorMeta = document.querySelector('meta[name="author"]')?.content || '';

                            return {
                                cw,
                                sw,
                                bw,
                                hasOverflow,
                                overElements: overElements.slice(0, 5),
                                touchIssues: touchIssues.slice(0, 5),
                                touchCount: touchIssues.length,
                                hasSuresh,
                                hasNarendra,
                                authorMeta
                            };
                        })()
                        ''',
                        'returnByValue': True
                    })

                    val = res.get('result', {}).get('value', {})
                    if val.get('hasOverflow'):
                        msg = f"OVERFLOW: {page} @ {vp_label} (cw={val['cw']}, sw={val['sw']}, bw={val['bw']})"
                        print(f"❌ {msg}")
                        for item in val.get('overElements', []):
                            print(f"     <{item['tag']} class='{item['cls']}' id='{item['id']}'> width={item['width']}px, right={item['right']}px vs viewport={item['cw']}px")
                        overflow_failures.append(msg)
                    else:
                        print(f"✓ No overflow @ {vp_label} (cw={val['cw']}px, sw={val['sw']}px, bw={val['bw']}px)")

                    if val.get('hasSuresh'):
                        err = f"FOUND OLD NAME 'suresh' in {page}!"
                        print(f"❌ {err}")
                        name_check_failures.append(err)

                    if not val.get('hasNarendra'):
                        err = f"MISSING 'narendra' in {page}!"
                        print(f"❌ {err}")
                        name_check_failures.append(err)

                    if val.get('authorMeta') != 'Burla Narendra':
                        err = f"Missing or incorrect author meta in {page}: '{val.get('authorMeta')}'"
                        name_check_failures.append(err)

                    if val.get('touchCount', 0) > 0:
                        print(f"   ⚠️  Touch targets < 40px ({val['touchCount']} items) @ {vp_label}:")
                        for t in val.get('touchIssues', []):
                            print(f"        <{t['tag']} class='{t['cls']}'> '{t['text']}' ({t['w']}x{t['h']}px)")
                        touch_warnings.append(f"{page} @ {vp_label}: {val['touchCount']} small targets")

            print("\n================== VERIFICATION SUMMARY ==================")
            if overflow_failures:
                print(f"❌ FAILED: {len(overflow_failures)} overflow issues found!")
                for f in overflow_failures:
                    print("  - " + f)
            else:
                print("✅ PASSED: Zero horizontal overflow across ALL 7 pages and ALL 9 viewports (320px to 1440px)!")

            name_set = list(set(name_check_failures))
            if name_set:
                print(f"❌ FAILED NAME CHECKS: {len(name_set)}")
                for n in name_set:
                    print("  - " + n)
            else:
                print("✅ PASSED: All pages verified for Burla Narendra founder name & meta author tags!")

            if touch_warnings:
                print(f"⚠️  Touch target warnings: {len(touch_warnings)}")
            else:
                print("✅ PASSED: Zero touch target ergonomics warnings on mobile!")
    finally:
        p.terminate()

if __name__ == '__main__':
    asyncio.run(run())
