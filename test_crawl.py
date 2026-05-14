import unittest
from crawl import normalize_url, get_heading_from_html, get_first_paragraph_from_html, get_urls_from_html, get_images_from_html, extract_page_data


class TestNormalizeUrl(unittest.TestCase):
    def test_strip_https(self):
        self.assertEqual(normalize_url("https://www.boot.dev/blog/path"), "www.boot.dev/blog/path")

    def test_strip_http(self):
        self.assertEqual(normalize_url("http://www.boot.dev/blog/path"), "www.boot.dev/blog/path")

    def test_strip_trailing_slash(self):
        self.assertEqual(normalize_url("https://www.boot.dev/blog/path/"), "www.boot.dev/blog/path")

    def test_http_trailing_slash(self):
        self.assertEqual(normalize_url("http://www.boot.dev/blog/path/"), "www.boot.dev/blog/path")

    def test_root_path(self):
        self.assertEqual(normalize_url("https://www.boot.dev/"), "www.boot.dev")

    def test_no_path(self):
        self.assertEqual(normalize_url("https://www.boot.dev"), "www.boot.dev")


class TestGetHeadingFromHtml(unittest.TestCase):
    def test_h1_basic(self):
        self.assertEqual(get_heading_from_html("<html><body><h1>Test Title</h1></body></html>"), "Test Title")

    def test_h2_fallback(self):
        self.assertEqual(get_heading_from_html("<html><body><h2>Subtitle</h2></body></html>"), "Subtitle")

    def test_h1_takes_priority_over_h2(self):
        html = "<html><body><h1>Main</h1><h2>Sub</h2></body></html>"
        self.assertEqual(get_heading_from_html(html), "Main")

    def test_no_heading(self):
        self.assertEqual(get_heading_from_html("<html><body><p>No heading here.</p></body></html>"), "")


class TestGetFirstParagraphFromHtml(unittest.TestCase):
    def test_basic_paragraph(self):
        self.assertEqual(get_first_paragraph_from_html("<html><body><p>Hello</p></body></html>"), "Hello")

    def test_main_priority(self):
        html = """<html><body>
            <p>Outside paragraph.</p>
            <main><p>Main paragraph.</p></main>
        </body></html>"""
        self.assertEqual(get_first_paragraph_from_html(html), "Main paragraph.")

    def test_fallback_when_no_main(self):
        html = "<html><body><p>First</p><p>Second</p></body></html>"
        self.assertEqual(get_first_paragraph_from_html(html), "First")

    def test_no_paragraph(self):
        self.assertEqual(get_first_paragraph_from_html("<html><body><h1>Title only</h1></body></html>"), "")


class TestGetUrlsFromHtml(unittest.TestCase):
    def test_absolute_url(self):
        html = '<html><body><a href="https://crawler-test.com"><span>Boot.dev</span></a></body></html>'
        self.assertEqual(get_urls_from_html(html, "https://crawler-test.com"), ["https://crawler-test.com"])

    def test_relative_url_converted(self):
        html = '<html><body><a href="/about">About</a></body></html>'
        self.assertEqual(get_urls_from_html(html, "https://example.com"), ["https://example.com/about"])

    def test_multiple_links(self):
        html = '<html><body><a href="/a">A</a><a href="/b">B</a></body></html>'
        self.assertEqual(get_urls_from_html(html, "https://example.com"), ["https://example.com/a", "https://example.com/b"])

    def test_anchor_without_href_skipped(self):
        html = '<html><body><a>No href</a><a href="/real">Real</a></body></html>'
        self.assertEqual(get_urls_from_html(html, "https://example.com"), ["https://example.com/real"])


class TestGetImagesFromHtml(unittest.TestCase):
    def test_relative_src_converted(self):
        html = '<html><body><img src="/logo.png" alt="Logo"></body></html>'
        self.assertEqual(get_images_from_html(html, "https://crawler-test.com"), ["https://crawler-test.com/logo.png"])

    def test_absolute_src_unchanged(self):
        html = '<html><body><img src="https://cdn.example.com/img.jpg" alt="img"></body></html>'
        self.assertEqual(get_images_from_html(html, "https://example.com"), ["https://cdn.example.com/img.jpg"])

    def test_multiple_images(self):
        html = '<html><body><img src="/a.png"><img src="/b.png"></body></html>'
        self.assertEqual(get_images_from_html(html, "https://example.com"), ["https://example.com/a.png", "https://example.com/b.png"])

    def test_image_without_src_skipped(self):
        html = '<html><body><img alt="no src"><img src="/real.png"></body></html>'
        self.assertEqual(get_images_from_html(html, "https://example.com"), ["https://example.com/real.png"])


class TestExtractPageData(unittest.TestCase):
    def test_basic(self):
        html = '''<html><body>
            <h1>Test Title</h1>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </body></html>'''
        self.assertEqual(extract_page_data(html, "https://crawler-test.com"), {
            "url": "https://crawler-test.com",
            "heading": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://crawler-test.com/link1"],
            "image_urls": ["https://crawler-test.com/image1.jpg"],
        })

    def test_empty_page(self):
        self.assertEqual(extract_page_data("<html><body></body></html>", "https://example.com"), {
            "url": "https://example.com",
            "heading": "",
            "first_paragraph": "",
            "outgoing_links": [],
            "image_urls": [],
        })

    def test_multiple_links_and_images(self):
        html = '''<html><body>
            <h2>Subtitle</h2>
            <main><p>Main paragraph.</p></main>
            <a href="/a">A</a><a href="https://other.com">B</a>
            <img src="/x.png"><img src="/y.png">
        </body></html>'''
        result = extract_page_data(html, "https://example.com")
        self.assertEqual(result["url"], "https://example.com")
        self.assertEqual(result["heading"], "Subtitle")
        self.assertEqual(result["first_paragraph"], "Main paragraph.")
        self.assertEqual(result["outgoing_links"], ["https://example.com/a", "https://other.com"])
        self.assertEqual(result["image_urls"], ["https://example.com/x.png", "https://example.com/y.png"])


if __name__ == "__main__":
    unittest.main()
