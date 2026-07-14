"""
Document Processor Module
Handles PDF text extraction and URL/HTML content scraping
"""

import io
import re
import requests
from bs4 import BeautifulSoup
import pdfplumber
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


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


def chunk_text_with_overlap(text: str, chunk_size: int = 1500, overlap: int = 200) -> list:
    """Split text into overlapping chunks (by words) to preserve context boundaries."""
    if not text:
        return []
    
    words = text.split()
    chunks = []
    
    if len(words) <= chunk_size:
        return [text]
        
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
            
    return chunks


def retrieve_relevant_chunks(text: str, query: str, top_k: int = 3, chunk_size: int = 1000, overlap: int = 150) -> str:
    """
    Chunks the document and retrieves the most relevant chunks using TF-IDF cosine similarity.
    This acts as a lightweight, in-memory RAG pipeline to drastically reduce LLM token usage.
    
    Args:
        text (str): Full document text.
        query (str): Keywords representing what we are looking for (e.g. 'students impact').
        top_k (int): Number of chunks to retrieve.
        
    Returns:
        str: Concatenated relevant chunks.
    """
    chunks = chunk_text_with_overlap(text, chunk_size=chunk_size, overlap=overlap)
    
    # If the document is small enough, return it fully
    if len(chunks) <= top_k:
        return "\n\n...\n\n".join(chunks)
        
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        # We append query to fit_transform so its vocabulary is included
        all_docs = chunks + [query]
        
        tfidf_matrix = vectorizer.fit_transform(all_docs)
        chunk_vectors = tfidf_matrix[:-1]
        query_vector = tfidf_matrix[-1]
        
        similarities = cosine_similarity(query_vector, chunk_vectors).flatten()
        
        # Get top k indices, sorted by highest similarity
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        # Sort indices ascending to maintain chronological document order
        top_indices = sorted(top_indices)
        
        relevant_chunks = [chunks[i] for i in top_indices]
        return "\n\n... [Skipped Irrelevant Content] ...\n\n".join(relevant_chunks)
        
    except Exception as e:
        print(f"Retrieval error: {e}")
        # Fallback to naive truncation
        return text[:12000]
