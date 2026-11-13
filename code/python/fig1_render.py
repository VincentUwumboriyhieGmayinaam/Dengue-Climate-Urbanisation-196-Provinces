import sys, asyncio
from playwright.async_api import async_playwright
svg = open('out/Figure1_conceptual_framework.svg', encoding='utf-8').read()
import re
W, H = map(int, re.search(r'viewBox="0 0 (\d+) (\d+)"', svg).groups())
scale = float(sys.argv[1]) if len(sys.argv) > 1 else 1
out = sys.argv[2] if len(sys.argv) > 2 else 'preview.png'
html = f'<html><body style="margin:0;background:#fff">{svg}</body></html>'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=scale)
        await pg.set_content(html); await pg.wait_for_timeout(300)
        await pg.screenshot(path=out, full_page=False)
        if '--pdf' in sys.argv:
            await pg.pdf(path=out.replace('.png', '.pdf'), width=f'{W}px', height=f'{H}px', print_background=True, page_ranges='1')
        await b.close()
asyncio.run(main())
