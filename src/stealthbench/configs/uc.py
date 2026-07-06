from stealthbench.configs.selenium_handle import SeleniumHandle


class UcConfig:
    """undetected-chromedriver. Pass chrome_major to match the installed Chrome."""

    label = "undetected-chromedriver"

    def __init__(self, chrome_major: int | None = None):
        self.chrome_major = chrome_major

    def build(self) -> SeleniumHandle:
        import undetected_chromedriver as uc

        o = uc.ChromeOptions()
        o.add_argument("--no-sandbox")
        o.add_argument("--disable-dev-shm-usage")
        o.add_argument("--window-size=1280,900")
        driver = uc.Chrome(options=o, use_subprocess=True, version_main=self.chrome_major)
        return SeleniumHandle(driver)
