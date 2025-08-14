# Install with: pip install pypdf
from pypdf import PdfReader

def extract_pdf_text(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

pdf_text = extract_pdf_text("test\sample_input.pdf")
print("Extracted Text", pdf_text)

# Install with: pip install nltk
import nltk
nltk.download('punkt')
nltk.download('stopwords')
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords

def preprocess_text(text):
    # Sentence segmentation
    sentences = sent_tokenize(text)
    # Word tokenization & cleanup
    stop_words = set(stopwords.words('english'))
    processed = [
        ' '.join([w.lower() for w in word_tokenize(sent) if w.isalnum() and w.lower() not in stop_words])
        for sent in sentences
    ]
    return processed

clean_sentences = preprocess_text(pdf_text)
print("Cleaned sentences",clean_sentences, len(clean_sentences))

# import google.generativeai as genai

# genai.configure(api_key="AIzaSyDoUEbF0hApgCCwr49HXXMkbzNy35JpV0Q")

# model = genai.GenerativeModel("gemini-2.0-flash")

# # Format your prompt for question generation
# prompt = f"""
# Based on the following study notes, generate 5 quiz questions for student review. Format the result as a JSON array, each object should have 'question', 'options', and 'answer' keys.

# NOTES:
# {pdf_text[:4000]}  # Truncate to fit context limit
# """

# response = model.generate_content(prompt)
# print("API Response",response.text, len(response.text))

# pip install ollama
import ollama

prompt_template = """
You are an Anna University exam preparation assistant.

Student details:
- Batch: {batch}
- Subject code: {subject_code}
- Regulation: {regulation}
- Subject: {subject_name}

Anna University exams for this subject usually include:
- Direct definitions for 2-mark questions
- Short notes (8 marks)
- Descriptive answers (16 marks)

Your task:
From the following study notes, generate 5 multiple-choice quiz questions in the style of Anna University past papers. 
For each question:
- Provide exactly 4 answer options
- Mark the correct answer
- Avoid trivial or irrelevant questions
- Ensure the difficulty matches typical Anna University exams

Format as **pure JSON array** (no extra text), each object must have:
"question": "...",
"options": ["...", "...", "...", "..."],
"answer": "..."

NOTES:
{notes}
"""

def generate_quiz_with_ollama(notes, batch, subject_code, regulation, subject_name):
    prompt = prompt_template.format(
        batch=batch,
        subject_code=subject_code,
        regulation=regulation,
        subject_name=subject_name,
        notes=notes[:3000]  # truncate for small context models
    )
    
    response = ollama.chat(model="deepseek-r1:14b", messages=[{"role": "user", "content": prompt}])
    return response['message']['content']

quiz_json = generate_quiz_with_ollama(
    notes=pdf_text,
    batch="2021",       
    subject_code="CS6701",
    regulation="2017",
    subject_name="Cryptography and Network Security"
)

print("Generated Quiz:", quiz_json)
