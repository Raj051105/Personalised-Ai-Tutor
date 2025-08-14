from ingest import ingest_all
from retriever import get_context_scoped
from mcq_generator import generate_mcqs
from flashcard_generator import generate_flashcards

def main():
    # Step 1: Ingest syllabus, notes, past-papers into Chroma DB
    ingest_all("CS3491")

    # Step 2: Retrieve the fundamentals context once
    context_fundamentals = get_context_scoped(
        "Artifical Intelligence and Machine Learning",
        "CS3491",
        k=7,
        sources=["syllabus", "notes"]
    )

    print("Retrieved fundamentals context length:", len(context_fundamentals))

    student_info = {
        "name": "John Doe",
        "age": 19,
        "batch": "2023-2027",
        "subject_code": "CS3491",
        "regulation": "R2021"
    }

    # Step 3: Generate MCQs from same context
    mcqs = generate_mcqs(student_info, context_fundamentals)
    print(f"\n✅ Generated {len(mcqs)} MCQs")
    for m in mcqs:
        print(f"Q: {m['question']}\nOptions: {m['options']}\nAnswer: {m['correct_option']}\n")

    # Step 4: Generate flashcards from same context_fundamentals
    flashcards = generate_flashcards(student_info, context_fundamentals, num_cards=8) or []
    print(f"\n✅ Generated {len(flashcards)} flashcards")
    for f in flashcards:
        print(f"Front: {f['front']}\nBack: {f['back']}\n")

if __name__ == "__main__":
    main()
