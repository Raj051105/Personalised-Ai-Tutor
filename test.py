from retriever import load_db

db = load_db()

docs = db.similarity_search("test", k=4)

for d in docs:

    print(len(d.page_content), d.metadata)