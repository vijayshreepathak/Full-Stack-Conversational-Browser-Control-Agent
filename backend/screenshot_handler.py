import base64

class ScreenshotHandler:
    async def capture(self, page, filename):
        await page.screenshot(path=filename, full_page=True)
        with open(filename, "rb") as img_file:
            b64_string = base64.b64encode(img_file.read()).decode('utf-8')
        return b64_string 