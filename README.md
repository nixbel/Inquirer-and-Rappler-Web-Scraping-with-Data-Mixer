# 📰 Philippine News Scraper & Dataset Builder

A collection of Python tools for scraping news articles from Philippine news outlets — **Inquirer** and **Rappler** — and merging the collected data into a unified CSV dataset. Designed for building labeled datasets for NLP and fake news detection tasks.

---

## 📁 Project Structure

```
.
├── WebScraping_Inquirer.py   # Flask app for scraping Inquirer articles
├── WebScraping_Rappler.py    # Flask app for scraping Rappler articles
├── mixer.py                  # Utility to merge two CSV datasets into one
└── train.csv                 # Output dataset (auto-generated)
```

---

## 🧩 Components

### 1. `WebScraping_Inquirer.py` — Inquirer News Scraper

A Flask web application that scrapes news articles from [Inquirer.net](https://inquirer.net) and its sub-domains (e.g., `pop.inquirer.net`, `business.inquirer.net`).

**How it works:**

- Serves a simple browser-based UI at `http://localhost:5000`
- User pastes an Inquirer article URL into the text area
- On input, the app automatically sends the URL to the `/save_article` endpoint
- The article is scraped and saved to `train.csv`
- Duplicate detection is performed based on article **title** and **publication date**

**Scraped fields:**

| Field | Description |
|---|---|
| `title` | Article headline (from `<h1>`) |
| `author` | Byline author (from meta tags or class-based lookup) |
| `publication_date` | Date published (from `<time>`, meta tags, scripts, or URL pattern) |
| `content` | Article body paragraphs (filtered by known CSS class names) |
| `news_source` | Always `"Inquirer"` |
| `link` | Original article URL |
| `classification` | Label for the article (default: `"1"`) |

**Category-aware content extraction:**

The scraper detects the article's category from the URL path (e.g., `newsinfo`, `business`, `entertainment`, `lifestyle`, `sports`, `bandera`) and uses category-specific CSS class names to locate the article body more accurately.

**Author extraction strategy (in order of priority):**
1. `rel="tag"` anchor (for `pop.inquirer.net`)
2. `<meta name="author">` tag
3. Common byline CSS classes: `byline__author-name`, `author__name`, `author`, `byline`, etc.

**Date extraction strategy (in order of priority):**
1. `<time datetime="...">` attribute
2. `<time>` tag text content
3. Common date CSS classes across `<time>`, `<span>`, `<div>`, `<p>` tags
4. `<meta property="article:published_time">` tag
5. Inline `<script>` tag date pattern (`YYYY-MM-DD`)
6. URL path date pattern (`YYYY/MM/DD`)

---

### 2. `WebScraping_Rappler.py` — Rappler News Scraper

A Flask web application that scrapes news articles from [Rappler.com](https://rappler.com).

**How it works:**

- Serves a browser-based UI at `http://localhost:5000`
- User enters a Rappler article URL into the input field
- On input, the URL is sent to the `/scrape` endpoint
- The article is scraped and appended to `train.csv`
- Duplicate detection is based on the article **link/URL**

**Scraped fields:**

| Field | Description |
|---|---|
| `title` | Article headline (from `<h1>`) |
| `author` | Byline author (from meta tags or class-based lookup) |
| `publication_date` | Date published (from `<time>` tag) |
| `content` | Article body paragraphs |
| `news_source` | `"Rappler"` if URL contains `rappler.com`, else `"Unknown"` |
| `link` | Original article URL |
| `classification` | Label for the article (default: `1`) |

**Author extraction strategy:**
1. `<meta name="author">` tag
2. Common byline CSS classes: `byline__author-name`, `author__name`, `author`, `byline`, etc.

**Content extraction strategy:**
Searches for article body in divs with the following classes (in order): `article-body`, `article-content`, `main-article`, `post-content`, `content`. Falls back to any `<div>` containing more than 5 `<p>` tags.

---

### 3. `mixer.py` — CSV Merger

A standalone command-line utility to merge two CSV files into a single `train.csv` output file.

**How it works:**

- Prompts the user for the paths of two CSV files
- Reads both files using `pandas`
- Concatenates them row-by-row (ignoring original indices)
- Saves the result as `train.csv` in the current directory

**Usage:**

```bash
python mixer.py
```

```
Enter the path to the first CSV file: inquirer_data.csv
Enter the path to the second CSV file: rappler_data.csv
Combined CSV file saved as: train.csv
```

> **Note:** The output file is always named `train.csv` and saved in the current working directory. Existing `train.csv` files will be overwritten.

---

## 📦 Requirements

### Python Version
Python 3.7+

### Dependencies

Install all required packages using pip:

```bash
pip install flask requests beautifulsoup4 pandas
```

| Package | Used In | Purpose |
|---|---|---|
| `flask` | Both scrapers | Web server and routing |
| `requests` | Both scrapers | Fetching article HTML |
| `beautifulsoup4` | Both scrapers | Parsing HTML content |
| `pandas` | `mixer.py` | Reading and merging CSV files |

---

## 🚀 Getting Started

### Step 1 — Clone or download the project files

Place all `.py` files in the same directory.

### Step 2 — Install dependencies

```bash
pip install flask requests beautifulsoup4 pandas
```

### Step 3 — Run a scraper

**For Inquirer articles:**
```bash
python WebScraping_Inquirer.py
```

**For Rappler articles:**
```bash
python WebScraping_Rappler.py
```

Both apps run on `http://localhost:5000` by default. Open that URL in your browser.

### Step 4 — Scrape articles

Paste or type an article URL into the input field. The app will:
- Automatically scrape the article
- Save it to `train.csv` in the project directory
- Display a success or error message

### Step 5 — Merge datasets (optional)

If you have scraped articles separately using both scrapers and want to combine them:

```bash
python mixer.py
```

Enter the paths to both CSV files when prompted. The merged output will be saved as `train.csv`.

---

## 📄 Output Format

All scrapers write to a CSV file (`train.csv`) with the following columns:

```
title, author, publication_date, content, news_source, link, classification
```

**Example row:**

| title | author | publication_date | content | news_source | link | classification |
|---|---|---|---|---|---|---|
| Senate approves bill... | Juan dela Cruz | 2024-03-15 | The Senate on Thursday... | Inquirer | https://inquirer.net/... | 1 |

---

## ⚠️ Notes & Limitations

- **`classification` field:** Both scrapers default classification to `1`. You should manually update or extend the classification logic based on your labeling schema (e.g., `0` for fake, `1` for real).
- **Duplicate handling:**
  - Inquirer scraper checks for duplicate **title + publication date** combinations.
  - Rappler scraper checks for duplicate **URLs**.
- **Content filtering:** Both scrapers automatically strip AI-generated summary boilerplate texts such as `"This is AI generated summarization..."` and `"CONTAINMENT."` from the article body.
- **Fallback content extraction:** If no known CSS class is found, the scraper falls back to the first `<div>` containing more than 5 paragraphs — this may occasionally capture non-article content (e.g., sidebars).
- **Port conflicts:** Both scrapers run on port `5000` by default. Do not run them simultaneously without changing the port in one of them.
- **Rate limiting / blocking:** Both scrapers send standard browser-like `User-Agent` headers (Inquirer scraper), but repeated rapid scraping may result in blocks. Add delays between requests if scraping in bulk.

---

## 🔧 Configuration & Customization

### Changing the output filename

In both scrapers, the filename is hardcoded as `'train.csv'`. To change it, locate this line and update the value:

```python
filename = 'train.csv'
```

### Changing the classification label

In `WebScraping_Inquirer.py`:
```python
classification = '1'  # Change to your desired label
```

In `WebScraping_Rappler.py`:
```python
'classification': 1  # Change to your desired label
```

### Running on a different port

```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Change port here
```

### Disabling debug mode for production

```python
app.run(debug=False)
```

---

## 🗂️ Typical Workflow

```
1. Run WebScraping_Inquirer.py  →  Collect Inquirer articles  →  inquirer_train.csv
2. Run WebScraping_Rappler.py   →  Collect Rappler articles   →  rappler_train.csv
3. Run mixer.py                 →  Merge both files            →  train.csv (combined)
4. Use train.csv for model training or data analysis
```

---

## 📜 License

This project is intended for academic and research purposes.
