#!/usr/bin/env python3
"""Convert the cellpose_mcp_poster.html to PDF using Playwright."""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def html_to_pdf(html_path: Path, pdf_path: Path):
    """Convert HTML file to PDF using Playwright.
    
    Args:
        html_path: Path to the input HTML file
        pdf_path: Path to the output PDF file
    """
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch()
        
        # Set viewport to match poster dimensions
        # 3456pt × 2592pt converted to pixels at 1.333 ratio = 4608px × 3456px
        page = await browser.new_page(viewport={
            "width": 4608,  # 3456pt * 1.333
            "height": 3456  # 2592pt * 1.333
        })
        
        # Load the HTML file
        html_url = f"file://{html_path.resolve()}"
        await page.goto(html_url, wait_until="networkidle")
        
        # Wait for fonts and images to load
        await page.wait_for_timeout(2000)
        
        # Remove the transform scaling from the body element
        # This ensures content renders at full size in PDF
        await page.evaluate("""
            () => {
                document.body.style.transform = 'none';
                document.body.style.transformOrigin = 'top left';
                document.documentElement.style.background = '#000';
                document.documentElement.style.overflow = 'visible';
            }
        """)
        
        # Generate PDF with specific settings for the poster
        # The poster is 3456pt × 2592pt (48" × 36" at 72 DPI, 4:3 aspect ratio)
        await page.pdf(
            path=str(pdf_path),
            width="48in",  # 3456pt = 48 inches
            height="36in",  # 2592pt = 36 inches
            print_background=True,
            prefer_css_page_size=False,
            margin={
                "top": "0",
                "right": "0",
                "bottom": "0",
                "left": "0"
            },
            scale=1.0
        )
        
        await browser.close()
    
    print(f"✓ PDF saved to: {pdf_path}")


async def main():
    """Main conversion function."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    # Input and output paths
    html_file = script_dir / "cellpose_mcp_poster.html"
    pdf_file = script_dir / "cellpose_mcp_poster.pdf"
    
    if not html_file.exists():
        print(f"Error: HTML file not found at {html_file}")
        return 1
    
    print(f"Converting {html_file.name} to PDF...")
    await html_to_pdf(html_file, pdf_file)
    print(f"Conversion complete!")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
