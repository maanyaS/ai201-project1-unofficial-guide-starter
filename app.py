"""
app.py

Milestone 5: Gradio web interface.

Run with:
    python app.py

Then open http://localhost:7860 in your browser.
"""

import gradio as gr
from query import ask


# ── Handler ───────────────────────────────────────────────────────────────────
def handle_query(question: str):
    """
    Called by Gradio on every button click or Enter press.
    Returns (answer_text, sources_text) to populate the two output boxes.
    """
    if not question.strip():
        return "Please enter a question.", ""

    result = ask(question)

    answer = result["answer"]
    sources = "\n".join(f"• {s}" for s in result["sources"])

    return answer, sources


# ── Interface ─────────────────────────────────────────────────────────────────
with gr.Blocks(title="Unofficial Guide to Rutgers CS Professors") as demo:

    gr.Markdown("""
    # 📚 The Unofficial Guide to Rutgers CS Professors
    Ask questions about CS professors at Rutgers University New Brunswick,
    based on real student reviews from Rate My Professors.

    **Example questions:**
    - Is Tina Burns recommended for CS211?
    - What do students say about Menendez's exams?
    - Which professor gives the most useful feedback?
    - What is Ananda Gunawardena's teaching style like?
    """)

    with gr.Row():
        inp = gr.Textbox(
            label="Your question",
            placeholder="e.g. Is Tina Burns recommended for CS211?",
            lines=2,
            scale=4,
        )

    btn = gr.Button("Ask", variant="primary")

    with gr.Row():
        answer_box = gr.Textbox(
            label="Answer",
            lines=10,
            scale=3,
        )
        sources_box = gr.Textbox(
            label="Retrieved from",
            lines=10,
            scale=1,
        )

    gr.Markdown("""
    ---
    *Answers are grounded in student reviews only.
    If the documents don't cover your question, the system will say so.*
    """)

    # Trigger on button click or Enter key
    btn.click(handle_query, inputs=inp, outputs=[answer_box, sources_box])
    inp.submit(handle_query, inputs=inp, outputs=[answer_box, sources_box])

demo.launch()