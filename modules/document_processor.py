"""
Document Processor Module
Handles PDF text extraction and URL/HTML content scraping
"""

import io
import re
import requests
from bs4 import BeautifulSoup
import pdfplumber


def extract_text_from_pdf(uploaded_file) -> str:
    """Extract text content from an uploaded PDF file."""
    try:
        pdf_bytes = uploaded_file.read()
        text_content = []

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_content.append(f"[Page {page_num}]\n{page_text}")

        full_text = "\n\n".join(text_content)
        return clean_text(full_text)

    except Exception as e:
        raise ValueError(f"Error extracting PDF text: {str(e)}")


def extract_text_from_url(url: str) -> str:
    """Scrape and extract text content from a URL."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")

        # If it's a PDF served from URL
        if "application/pdf" in content_type:
            with pdfplumber.open(io.BytesIO(response.content)) as pdf:
                text_parts = []
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"[Page {page_num}]\n{page_text}")
                return clean_text("\n\n".join(text_parts))

        # HTML content
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove scripts, styles, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Try to get main content areas first
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", class_=re.compile(r"content|main|body", re.I))
            or soup.body
        )

        if main_content:
            raw_text = main_content.get_text(separator="\n", strip=True)
        else:
            raw_text = soup.get_text(separator="\n", strip=True)

        return clean_text(raw_text)

    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error fetching URL: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error processing URL content: {str(e)}")


def clean_text(text: str) -> str:
    """Clean and normalize extracted text."""
    # Remove excessive whitespace and blank lines
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)

    # Join and normalize spaces
    text = "\n".join(cleaned_lines)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def truncate_text(text: str, max_chars: int = 12000) -> str:
    """Truncate text to fit within LLM token limits."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... Document truncated for processing ...]"
