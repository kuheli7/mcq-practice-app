import json
import streamlit as st

def load_mcqs_from_json(uploaded_file) -> list:
    """Load predefined MCQs from JSON file"""
    content = uploaded_file.read()
    data = json.loads(content)
    
    # Support both formats:
    # 1. {"questions": [...]}
    # 2. [...]
    if isinstance(data, dict) and "questions" in data:
        return data["questions"]
    elif isinstance(data, list):
        return data
    else:
        st.error("Invalid JSON format. Expected array of questions or {questions: [...]}")
        return []


# ---------- Streamlit UI ----------
st.title("🤖 Gemini MCQ Generator")

# Mode selector
mode = st.radio("Choose input mode:", ["Upload PPT", "Enter Topic"], horizontal=True)

if "mcqs" not in st.session_state:
    st.session_state.mcqs = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "user_answer" not in st.session_state:
    st.session_state.user_answer = None

if mode == "Upload PPT":
    uploaded_file = st.file_uploader("Upload PowerPoint file", type=["ppt", "pptx"])
    num_questions = st.number_input("Number of questions to generate", min_value=1, max_value=500, value=10)
    
    if uploaded_file and st.button("Generate Questions from PPT"):
        with st.spinner(f"Analyzing presentation and generating {num_questions} questions..."):
            st.session_state.mcqs = generate_mcq_from_file(uploaded_file, num_questions)
            st.session_state.current_index = 0
            st.session_state.user_answer = None
            st.success(f"✅ Generated {len(st.session_state.mcqs)} questions!")
else:
    topic = st.text_input("Enter topic", "Operating Systems")
    
    if st.button("Generate Question from Topic"):
        with st.spinner("Generating question..."):
            mcq = generate_mcq_from_topic(topic)
            st.session_state.mcqs = [mcq]
            st.session_state.current_index = 0
            st.session_state.user_answer = None

# Display MCQs
if st.session_state.mcqs:
    total = len(st.session_state.mcqs)
    idx = st.session_state.current_index
    
    st.progress((idx + 1) / total)
    st.write(f"**Question {idx + 1} of {total}**")
    
    mcq = st.session_state.mcqs[idx]
    st.subheader(mcq["question"])

    choice = st.radio(
        "Choose an answer:",
        mcq["options"],
        index=None,
        key=f"q_{idx}"
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Previous") and idx > 0:
            st.session_state.current_index -= 1
            st.session_state.user_answer = None
            st.rerun()
    
    with col2:
        if st.button("Check Answer") and choice is not None:
            correct = mcq["options"][mcq["correct_index"]]
            if choice == correct:
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Wrong. Correct answer: {correct}")
    
    with col3:
        if st.button("Next ➡️") and idx < total - 1:
            st.session_state.current_index += 1
            st.session_state.user_answer = None
            st.rerun()
    
    # Download all questions as JSON
    if st.button("📥 Download All Questions"):
        json_str = json.dumps(st.session_state.mcqs, indent=2)
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name="mcq_questions.json",
            mime="application/json"
        )
