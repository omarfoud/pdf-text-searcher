# PDF Text Search Engine

A simple desktop application built with Python and Tkinter that allows you to index and perform full-text searches across a collection of PDF files stored locally. It uses Whoosh for indexing/searching, PyPDF for text extraction, and NLTK for text normalization.

## Features

*   **Graphical User Interface (GUI):** Easy-to-use interface built with Tkinter.
*   **PDF Indexing:** Scans a specified directory for PDF files, extracts their text content, and builds a searchable index.
*   **Text Normalization:** Uses NLTK (tokenization, lowercasing, stemming, lemmatization) to process text before indexing and searching, improving search relevance.
*   **Full-Text Search:** Allows users to enter search queries and find matching PDF documents.
*   **Result Snippets:** Displays relevant snippets from the documents where the search terms were found (highlighting).
*   **Background Processing:** Indexing and searching operations run in separate threads to keep the GUI responsive.
*   **Configurable Directory:** Allows users to change the directory containing the PDF files via the GUI.
*   **Status Updates:** Provides feedback on the indexing and searching progress in the status bar.

## How It Works

1.  **Indexing:**
    *   The application scans the specified `BOOKS_DIR` for `.pdf` files.
    *   For each PDF, it uses `pypdf` to extract the text content page by page.
    *   The extracted text is then *normalized* using `nltk`: tokenized into words, converted to lowercase, stemmed (using PorterStemmer), and lemmatized (using WordNetLemmatizer).
    *   The normalized text, along with the file path and filename, is added to a `Whoosh` index stored in the `INDEX_DIR`.
2.  **Searching:**
    *   The user enters a search query in the GUI.
    *   The query string is *normalized* using the exact same `nltk` process applied during indexing.
    *   The `Whoosh` index is searched using the normalized query.
    *   Matching documents are retrieved, ranked by relevance (score), and relevant text snippets (highlights) are generated.
    *   Results (filename, path, score, snippet) are displayed in the GUI.

## Technologies Used

*   **Python 3**
*   **Tkinter:** Standard Python GUI library.
*   **PyPDF:** PDF text extraction.
*   **Whoosh:** Full-text indexing and search library.
*   **NLTK:** Natural Language Toolkit for text normalization (tokenization, stemming, lemmatization).
*   **Threading:** For background task execution.

## Setup and Installation

1.  **Prerequisites:**
    *   Python 3.x installed.
    *   `pip` (Python package installer).

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: The script will automatically attempt to download the necessary NLTK data (`punkt`, `wordnet`) on the first run if they are not found.*

## Usage

1.  **Place PDF Files:** Ensure the directory specified by `BOOKS_DIR` in the script (default: `D:\\books`) exists and contains the PDF files you want to index. You can change this default path directly in the script or use the "Change Dir" button in the application.
2.  **Run the Application:**
    ```bash
    python pdf-text-searcher.py
    ```
3.  **Index Files:** Click the "Index Files" button. Wait for the indexing process to complete (monitor the status bar). This only needs to be done once initially or when new PDFs are added/updated. The index is stored in `INDEX_DIR` (default: `whoosh_index`).
4.  **Search:** Enter your search query in the text box and press Enter or click the "Search" button.
5.  **View Results:** Search results, including filename, path, relevance score, and a text snippet, will be displayed in the main text area.

## Configuration

*   **`BOOKS_DIR`:** Modify the `BOOKS_DIR` variable at the top of `pdf-text-searcher.py` to set the default directory containing your PDF files. You can also change this temporarily using the "Change Dir" button in the UI.
*   **`INDEX_DIR`:** Modify the `INDEX_DIR` variable to change where the Whoosh search index is stored.
