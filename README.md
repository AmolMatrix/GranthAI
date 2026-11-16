# Granth AI — Smart Library (Software Phase)

A Flask + SQLite smart-library prototype focused on **concept-level book discovery**.
The searchable catalog contains exactly 50 curated engineering/computing books.

## Core demo features

- Student registration and login; librarian login.
- Concept search using explainable TF-IDF + cosine similarity, with phrase-match boosting.
- Deep book indexing: core concepts, chapter map, subtopics/alternate terms, learning outcomes, prerequisites, and applications.
- Content-based recommendations, similar-book suggestions, shelf locations, issue/return, and waitlist management.

## Run locally

Python 3.10+ is recommended (the code uses only standard-library search logic).

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

### Demo accounts

- Librarian: `librarian@granthai.edu` / `librarian123`
- Student: `demo.student@gmail.com` / `student123`

Change these credentials and set a strong `SECRET_KEY` before any public deployment.

## Search demo queries

Try `deadlock prevention`, `TF-IDF cosine similarity`, `Bayesian networks`,
`B+ tree indexing`, `A* heuristic search`, `TCP congestion control`, or
`CNN pooling and backpropagation`. Results are ranked from the book's deep
index text, not only its title and author.

## Catalog and database behaviour

On first launch, tables are created and the 50-book catalog is seeded. If the
existing database contains the previous sample catalog, startup replaces its
book/circulation sample rows with the curated 50-book catalog while retaining
user accounts. Back up `instance/granthai.db` before running this version if
you need to preserve old issue/reservation history. A database with this
version's 50-book catalog is left unchanged on later launches.

The chapter map is topic-level metadata, not fabricated page-number mapping.
Actual page-level references require the corresponding book editions/PDFs.

## Environment variables

- `SECRET_KEY`: strong random value for Flask sessions.
- `DATABASE_URL`: optional SQLAlchemy database URL; defaults to local SQLite.
- `FLASK_DEBUG=1`: enable Flask debug mode for local development only.
