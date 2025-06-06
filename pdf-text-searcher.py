import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import threading
from pypdf import PdfReader
from whoosh.index import create_in, open_dir, EmptyIndexError
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer

# Download the necessary NLTK data sets for tokenization and lemmatization
nltk.download('punkt')
nltk.download('wordnet')

# Define the directory where PDF books are stored and the index directory
BOOKS_DIR = "D:\\books"
INDEX_DIR = "whoosh_index"

# Define the schema for Whoosh index, including file path, filename, and content
schema = Schema(
    path=ID(stored=True, unique=True),
    filename=TEXT(stored=True),
    content=TEXT(stored=True)
)

def normalize_text(text):
    """
    Normalizes text using NLTK by performing the following operations:
    - Tokenizing the text into words.
    - Converting all tokens to lowercase.
    - Applying stemming to reduce words to their root form.
    - Applying lemmatization to get the canonical form of words.
    
    The final normalized string is generated by joining the processed tokens.
    """
    # Tokenize the input text into words
    tokens = word_tokenize(text)
    # Create instances of the stemmer and lemmatizer
    ps = PorterStemmer()
    lemmatizer = WordNetLemmatizer()
    normalized_tokens = []
    for token in tokens:
        # Convert each token to lowercase for case-insensitive matching
        token = token.lower()
        # Stem the token to reduce to a base form
        stemmed = ps.stem(token)
        # Further lemmatize the stemmed token to get its canonical form
        lemma = lemmatizer.lemmatize(stemmed)
        normalized_tokens.append(lemma)
    # Join and return the normalized tokens as a single string
    return " ".join(normalized_tokens)

def create_or_open_index(indexdir):
    """Creates a new index or opens an existing one in the specified directory."""
    if not os.path.exists(indexdir):
        os.makedirs(indexdir)
    try:
        ix = open_dir(indexdir)
    except EmptyIndexError:
        ix = create_in(indexdir, schema)
    return ix

def index_pdfs(books_dir, index_dir, status_callback):
    """
    Indexes all PDF files found in the 'books_dir'.
    For each PDF, the function extracts text, normalizes it using the same normalization process,
    and updates the Whoosh index with the normalized content.
    """
    if not os.path.isdir(books_dir):
        status_callback(f"Error: Books directory not found: {books_dir}", error=True)
        return
    ix = create_or_open_index(index_dir)
    writer = ix.writer(limitmb=256, procs=os.cpu_count(), multisegment=True)
    indexed_files = 0
    error_files = 0
    try:
        status_callback("Starting indexing...")
        all_files = [f for f in os.listdir(books_dir) if f.lower().endswith(".pdf")]
        total_files = len(all_files)
        status_callback(f"Found {total_files} PDF files in {books_dir}.")
        for i, filename in enumerate(all_files):
            full_path = os.path.join(books_dir, filename)
            try:
                status_callback(f"Indexing ({i+1}/{total_files}): {filename}")
                reader = PdfReader(full_path)
                extracted_text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"
                if extracted_text:
                    # Normalize text before indexing it to ensure consistency
                    normalized_text = normalize_text(extracted_text)
                    writer.update_document(
                        path=full_path,
                        filename=filename,
                        content=normalized_text
                    )
                    indexed_files += 1
                else:
                    status_callback(f"Warning: No text extracted from {filename}", error=True)
                    error_files += 1
            except Exception as e:
                status_callback(f"Error indexing {filename}: {e}", error=True)
                error_files += 1
        status_callback(f"Committing {indexed_files} documents to index...")
        writer.commit()
        status_callback(f"Indexing complete. Indexed: {indexed_files}, Errors/Skipped: {error_files}", success=True)
    except Exception as e:
        status_callback(f"Fatal indexing error: {e}", error=True)
        writer.cancel()

def search_index(index_dir, query_string, results_callback, status_callback):
    """
    Searches the index for documents matching the given query string.
    The query string is normalized using the same normalization process used during indexing,
    ensuring that both the indexed content and the query text are processed identically.
    """
    try:
        ix = open_dir(index_dir)
    except EmptyIndexError:
        status_callback("Error: Index is empty or not found. Please index files first.", error=True)
        results_callback([])
        return
    results_list = []
    try:
        with ix.searcher() as searcher:
            # Normalize the user's search query
            normalized_query = normalize_text(query_string)
            parser = QueryParser("content", schema=ix.schema)
            # Parse the normalized query into a Whoosh query object
            query = parser.parse(normalized_query)
            status_callback(f"Running query: {query_string}")
            results = searcher.search(query, limit=50)
            results.fragmenter.maxchars = 150
            results.fragmenter.surround = 40
            status_callback(f"Found {len(results)} results.")
            for hit in results:
                highlight = hit.highlights("content", top=1)
                results_list.append({
                    "filename": hit['filename'],
                    "path": hit['path'],
                    "score": hit.score,
                    "highlight": highlight if highlight else "[No relevant snippet found]"
                })
        results_callback(results_list)
    except Exception as e:
        status_callback(f"Error during search: {e}", error=True)
        results_callback([])
    finally:
        if 'ix' in locals() and ix:
            ix.close()

class PdfSearchApp:
    def __init__(self, root):
        self.root = root
        root.title("PDF Search Engine")
        root.geometry("800x600")
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.top_frame = ttk.Frame(root, padding="10")
        self.top_frame.pack(fill=tk.X)
        self.books_dir_label = ttk.Label(self.top_frame, text=f"Books Dir: {BOOKS_DIR}")
        self.books_dir_label.pack(side=tk.LEFT, padx=5)
        self.browse_button = ttk.Button(self.top_frame, text="Change Dir", command=self.browse_books_dir)
        self.browse_button.pack(side=tk.LEFT, padx=5)
        self.index_button = ttk.Button(self.top_frame, text="Index Files", command=self.start_indexing_thread)
        self.index_button.pack(side=tk.LEFT, padx=5)
        self.search_label = ttk.Label(self.top_frame, text="Search:")
        self.search_label.pack(side=tk.LEFT, padx=(10, 0))
        self.search_entry = ttk.Entry(self.top_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<Return>", self.start_search_thread)
        self.search_button = ttk.Button(self.top_frame, text="Search", command=self.start_search_thread)
        self.search_button.pack(side=tk.LEFT, padx=5)
        self.results_frame = ttk.Frame(root, padding="10")
        self.results_frame.pack(fill=tk.BOTH, expand=True)
        self.results_text = scrolledtext.ScrolledText(self.results_frame, wrap=tk.WORD, state=tk.DISABLED, height=20)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding="2 5")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status("Ready.")
        self.current_books_dir = BOOKS_DIR

    def browse_books_dir(self):
        """Allows the user to select a different books directory."""
        directory = filedialog.askdirectory(title="Select Books Directory")
        if directory:
            self.current_books_dir = directory
            self.books_dir_label.config(text=f"Books Dir: {self.current_books_dir}")
            self.update_status(f"Books directory changed to: {self.current_books_dir}")

    def update_status(self, message, error=False, success=False):
        """Updates the status bar with messages and color codes based on the message type."""
        def _update():
            self.status_var.set(message)
            if error:
                self.status_bar.config(foreground="red")
            elif success:
                self.status_bar.config(foreground="green")
            else:
                self.status_bar.config(foreground="black")
            self.root.update_idletasks()
        self.root.after(0, _update)

    def display_results(self, results):
        """Displays search results in the text area of the GUI."""
        def _display():
            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            if not results:
                self.results_text.insert(tk.END, "No results found.")
            else:
                for i, result in enumerate(results):
                    self.results_text.insert(tk.END, f"{i+1}. File: {result['filename']}\n")
                    self.results_text.insert(tk.END, f"   Path: {result['path']}\n")
                    self.results_text.insert(tk.END, f"   Score: {result['score']:.4f}\n")
                    self.results_text.insert(tk.END, f"   Snippet: {result['highlight']}\n\n")
            self.results_text.config(state=tk.DISABLED)
        self.root.after(0, _display)

    def start_indexing_thread(self):
        """Starts the indexing process on a separate thread."""
        self.update_status("Starting indexing process...")
        self.index_button.config(state=tk.DISABLED)
        self.search_button.config(state=tk.DISABLED)
        thread = threading.Thread(target=self._run_indexing, daemon=True)
        thread.start()

    def _run_indexing(self):
        """Worker function to index PDFs."""
        try:
            index_pdfs(self.current_books_dir, INDEX_DIR, self.update_status)
        finally:
            self.root.after(0, self._enable_buttons)

    def start_search_thread(self, event=None):
        """Starts the search process on a separate thread."""
        query = self.search_entry.get().strip()
        if not query:
            self.update_status("Please enter a search query.", error=True)
            return
        self.update_status("Starting search...")
        self.index_button.config(state=tk.DISABLED)
        self.search_button.config(state=tk.DISABLED)
        thread = threading.Thread(target=self._run_search, args=(query,), daemon=True)
        thread.start()

    def _run_search(self, query):
        """Worker function to execute the search."""
        try:
            search_index(INDEX_DIR, query, self.display_results, self.update_status)
        finally:
            self.root.after(0, self._enable_buttons)

    def _enable_buttons(self):
        """Re-enables GUI buttons after indexing or search completes."""
        self.index_button.config(state=tk.NORMAL)
        self.search_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    if not os.path.exists(BOOKS_DIR):
        try:
            os.makedirs(BOOKS_DIR)
            print(f"Created directory: {BOOKS_DIR}")
            print("Please place your PDF files in this directory.")
        except OSError as e:
            print(f"Error creating directory {BOOKS_DIR}: {e}")
    root = tk.Tk()
    app = PdfSearchApp(root)
    root.mainloop()
