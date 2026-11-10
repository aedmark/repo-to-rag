from repo_to_rag.converter import html_to_markdown


def test_html_to_markdown_basic():
    html = """
    <html>
      <head><title>Test Title</title></head>
      <body>
        <h1>Heading 1</h1>
        <p>This is a paragraph with <code>inline code</code>.</p>
        <h2>Heading 2</h2>
        <ul>
          <li>Item 1</li>
          <li>Item 2</li>
        </ul>
        <pre><code>def hello():\n    return "world"\n</code></pre>
      </body>
    </html>
    """
    md = html_to_markdown(html)
    assert "# Heading 1" in md
    assert "## Heading 2" in md
    assert "This is a paragraph with `inline code`." in md
    assert "- Item 1" in md
    assert "- Item 2" in md
    assert "```" in md
    assert "def hello():" in md


def test_html_to_markdown_ignores_script_and_style():
    html = """
    <p>Visible</p>
    <style>.hide { display: none; }</style>
    <script>alert('evil');</script>
    <p>Also Visible</p>
    """
    md = html_to_markdown(html)
    assert "Visible" in md
    assert "Also Visible" in md
    assert "display: none" not in md
    assert "alert" not in md
