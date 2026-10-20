import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome", headless=True)
        pg = await b.new_page(viewport={"width":400,"height":300})
        await pg.set_content("<h1 style='font-family:Microsoft YaHei'>测试 OK</h1>")
        await pg.screenshot(path=r"C:\Users\32768\Desktop\douyin-coding-video\research\pw-test.png")
        print("title:", await pg.title())
        await b.close()
asyncio.run(main())
