"""
Template Loader Utility

This module provides functionality to load HTML report and their associated
CSS and JavaScript files. It supports both inline embedding and external file references.
"""

import os
from pathlib import Path
from typing import Dict, Any


class TemplateLoader:
    """Load and manage HTML report with CSS and JavaScript assets."""

    def __init__(self, templates_dir: str = None):
        """
        Initialize the template loader.

        Args:
            templates_dir: Directory containing report. Defaults to template/report/
        """
        if templates_dir is None:
            current_dir = Path(__file__).parent
            templates_dir = current_dir / 'report'

        self.templates_dir = Path(templates_dir)
        self.template_root = Path(__file__).parent
        self.assets_dir = self.templates_dir / 'assets'

    def load_template(self, template_name: str) -> str:
        """
        Load an HTML template file.

        Args:
            template_name: Name of the template file (e.g., 'report_template.html')

        Returns:
            Template content as string
        """
        template_path = self.templates_dir / template_name
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_css(self, css_name: str) -> str:
        """
        Load a CSS file from the assets directory.

        Args:
            css_name: Name of the CSS file (e.g., 'report.css')

        Returns:
            CSS content as string
        """
        css_path = self.assets_dir / css_name
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_js(self, js_name: str) -> str:
        """
        Load a JavaScript file from the assets directory.

        Args:
            js_name: Name of the JavaScript file (e.g., 'report.js')

        Returns:
            JavaScript content as string
        """
        js_path = self.assets_dir / js_name
        with open(js_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_inline_template(self, template_name: str,
                            css_names: list = None,
                            js_names: list = None) -> str:
        """
        Load template with CSS and JS embedded inline.

        This is useful when you want a single standalone HTML file.

        Args:
            template_name: Name of the template file
            css_names: List of CSS files to embed (optional)
            js_names: List of JavaScript files to embed (optional)

        Returns:
            Complete HTML with inline CSS and JS
        """
        template = self.load_template(template_name)

        # Embed CSS if provided
        if css_names:
            css_content = '\n'.join(self.load_css(css) for css in css_names)
            # Escape curly braces in CSS for Python string formatting
            css_content = css_content.replace('{', '{{').replace('}', '}}')
            css_tag = f"<style>\n{css_content}\n</style>"
            # Replace the CSS link or insert before </head>
            if "<link rel='stylesheet'" in template:
                # Replace link tag
                import re
                template = re.sub(r"<link rel='stylesheet'[^>]*>", css_tag, template)
            else:
                template = template.replace('</head>', f'{css_tag}\n</head>')

        # Embed JS if provided
        if js_names:
            js_content = '\n'.join(self.load_js(js) for js in js_names)
            # Escape curly braces in JS for Python string formatting
            js_content = js_content.replace('{', '{{').replace('}', '}}')
            js_tag = f"<script>\n{js_content}\n</script>"
            # Replace the JS script tag or insert before </body>
            if "<script src='assets/" in template:
                # Replace last script tag with assets reference
                import re
                template = re.sub(r"<script src='assets/[^']*'></script>", js_tag, template)
            else:
                template = template.replace('</body>', f'{js_tag}\n</body>')

        return template

    def copy_assets_to_output(self, output_dir: str, asset_names: list = None):
        """
        Copy asset files to the output directory.

        This is useful when you want to keep external CSS/JS files.

        Args:
            output_dir: Directory where the HTML report will be saved
            asset_names: List of asset files to copy. If None, copies all assets.
        """
        import shutil

        output_path = Path(output_dir)
        output_assets = output_path / 'assets'
        output_assets.mkdir(parents=True, exist_ok=True)

        if asset_names is None:
            # Copy all files from assets directory
            if self.assets_dir.exists():
                for asset_file in self.assets_dir.iterdir():
                    if asset_file.is_file():
                        shutil.copy2(asset_file, output_assets / asset_file.name)
        else:
            # Copy only specified assets
            for asset_name in asset_names:
                src = self.assets_dir / asset_name
                if src.exists():
                    shutil.copy2(src, output_assets / asset_name)

    def render_template(self, template_name: str,
                       context: Dict[str, Any],
                       inline_assets: bool = True,
                       css_files: list = None,
                       js_files: list = None) -> str:
        """
        Render a template with context variables.

        Args:
            template_name: Name of the template file
            context: Dictionary of variables to substitute in template
            inline_assets: Whether to embed CSS/JS inline (True) or use external files (False)
            css_files: List of CSS files to include (for inline mode)
            js_files: List of JS files to include (for inline mode)

        Returns:
            Rendered HTML content
        """
        if inline_assets and (css_files or js_files):
            template = self.load_inline_template(template_name, css_files, js_files)
        else:
            template = self.load_template(template_name)

        # Render template with context
        return template.format(**context)

    def render_jinja_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a Jinja2 template with context variables.

        Args:
            template_name: Name of the template file
            context: Dictionary of variables to substitute in template

        Returns:
            Rendered HTML content
        """
        try:
            from jinja2 import Template
        except ImportError:
            raise ImportError("Jinja2 is required for rendering baseline selection templates. Install with: pip install jinja2")

        template_path = self.template_root / template_name
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        template = Template(template_content)
        return template.render(**context)