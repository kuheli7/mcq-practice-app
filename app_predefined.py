import json
import streamlit as st
import requests

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

def explain_answer(question: str, options: list, correct_index: int, api_key: str = "", api_provider: str = "gemini") -> str:
    """Get AI explanation for the correct answer"""
    
    correct_answer = options[correct_index]
    
    prompt = f"""Question: {question}

Options:
{chr(10).join([f"{i+1}. {opt}" for i, opt in enumerate(options)])}

Correct Answer: {correct_answer}

Please provide a clear, concise explanation (2-3 sentences) of why this is the correct answer."""

    try:
        if api_provider == "gemini":
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            return response.text
        
        elif api_provider == "github":
            response = requests.post(
                "https://models.inference.ai.azure.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a helpful tutor explaining answers concisely."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 200
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"Error: {response.status_code}"
        
    except Exception as e:
        return f"Error getting explanation: {str(e)}"
    
    return "No explanation available."


# ---------- Streamlit UI ----------
st.title("🤖 MCQ Practice App with AI Tutor")
st.write("Upload your predefined MCQ questions in JSON format")

# Sidebar for AI configuration
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Questions per page
    st.subheader("📄 Display Options")
    questions_per_page = st.slider("Questions per page", min_value=1, max_value=15, value=5)
    
    st.divider()
    
    # AI Tutor
    st.subheader("🤖 AI Tutor")
    use_ai = st.checkbox("Enable AI Explanations", value=False)
    
    if use_ai:
        ai_provider = st.radio("Choose AI Provider:", ["Gemini (Free)", "GitHub Models (Free)"])
        
        if ai_provider == "Gemini (Free)":
            api_key = st.text_input("Gemini API Key", type="password", help="Get from https://aistudio.google.com/apikey")
            provider = "gemini"
        else:
            api_key = st.text_input("GitHub Token", type="password", help="Get from https://github.com/settings/tokens")
            provider = "github"
        
        st.caption("💡 AI will explain correct answers when you check them")
    else:
        api_key = ""
        provider = ""

if "mcqs" not in st.session_state:
    st.session_state.mcqs = []
if "current_page" not in st.session_state:
    st.session_state.current_page = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "answered" not in st.session_state:
    st.session_state.answered = {}  # Changed to dict to store user answers
if "explanations" not in st.session_state:
    st.session_state.explanations = {}

# Auto-load default questions if available
import os

if not st.session_state.mcqs:
    # Try to load os_questions.json automatically
    default_path = os.path.join(os.path.dirname(__file__), "os_questions.json")
    if os.path.exists(default_path):
        try:
            with open(default_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                st.session_state.mcqs = data.get("questions", data) if isinstance(data, dict) else data
                st.success(f"✅ Auto-loaded {len(st.session_state.mcqs)} OS questions!")
        except Exception as e:
            st.warning(f"Could not auto-load questions: {e}")

# File uploader (optional - can upload different questions)
with st.expander("📤 Upload Different Questions (Optional)"):
    uploaded_file = st.file_uploader("Upload JSON file with MCQs", type=["json"])
    
    if uploaded_file:
        if st.button("Load Questions"):
            st.session_state.mcqs = load_mcqs_from_json(uploaded_file)
            st.session_state.current_page = 0
            st.session_state.score = 0
            st.session_state.answered = {}
            st.session_state.explanations = {}
            st.success(f"✅ Loaded {len(st.session_state.mcqs)} questions!")
            st.rerun()

# Display format example
with st.expander("📋 JSON Format Example"):
    st.code("""
{
  "questions": [
    {
      "question": "What is the capital of France?",
      "options": ["London", "Berlin", "Paris", "Madrid"],
      "correct_index": 2
    },
    {
      "question": "What is 2 + 2?",
      "options": ["3", "4", "5", "6"],
      "correct_index": 1
    }
  ]
}

OR simply:

[
  {
    "question": "What is the capital of France?",
    "options": ["London", "Berlin", "Paris", "Madrid"],
    "correct_index": 2
  }
]
    """, language="json")

# Display MCQs
if st.session_state.mcqs:
    total = len(st.session_state.mcqs)
    total_pages = (total + questions_per_page - 1) // questions_per_page
    current_page = st.session_state.current_page
    
    # Calculate question range for current page
    start_idx = current_page * questions_per_page
    end_idx = min(start_idx + questions_per_page, total)
    
    # Progress and score
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.progress((current_page + 1) / total_pages)
        st.write(f"**Page {current_page + 1} of {total_pages}** | Questions {start_idx + 1}-{end_idx} of {total}")
    with col2:
        st.metric("Answered", f"{len(st.session_state.answered)}/{total}")
    with col3:
        st.metric("Score", f"{st.session_state.score}/{len(st.session_state.answered)}" if st.session_state.answered else "0/0")
    
    st.divider()
    
    # Display questions for current page
    for idx in range(start_idx, end_idx):
        mcq = st.session_state.mcqs[idx]
        
        with st.container():
            st.subheader(f"Q{idx + 1}. {mcq['question']}")
            
            # Check if already answered
            default_choice = st.session_state.answered.get(idx, None)
            
            choice = st.radio(
                "Choose an answer:",
                mcq["options"],
                index=mcq["options"].index(default_choice) if default_choice else None,
                key=f"q_{idx}_{current_page}"
            )
            
            col1, col2 = st.columns([1, 4])
            
            with col1:
                if st.button("Check Answer", key=f"check_{idx}") and choice is not None:
                    correct = mcq["options"][mcq["correct_index"]]
                    
                    # Update score only if first time answering
                    if idx not in st.session_state.answered:
                        st.session_state.answered[idx] = choice
                        if choice == correct:
                            st.session_state.score += 1
                    
                    if choice == correct:
                        st.success("✅ Correct!")
                    else:
                        st.error(f"❌ Wrong. Correct answer: {correct}")
                    
                    # Show AI explanation if enabled
                    if use_ai and api_key:
                        if idx not in st.session_state.explanations:
                            with st.spinner("🤔 Getting explanation..."):
                                explanation = explain_answer(
                                    mcq["question"],
                                    mcq["options"],
                                    mcq["correct_index"],
                                    api_key,
                                    provider
                                )
                                st.session_state.explanations[idx] = explanation
                        
                        st.info(f"💡 **Explanation:** {st.session_state.explanations[idx]}")
            
            with col2:
                # Show if already answered
                if idx in st.session_state.answered:
                    prev_choice = st.session_state.answered[idx]
                    correct = mcq["options"][mcq["correct_index"]]
                    if prev_choice == correct:
                        st.success(f"✅ Previously answered: {prev_choice}")
                    else:
                        st.error(f"❌ Previously answered: {prev_choice} (Correct: {correct})")
                    
                    # Show cached explanation if available
                    if idx in st.session_state.explanations:
                        st.info(f"💡 {st.session_state.explanations[idx]}")
            
            st.divider()
    
    # Page navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Previous Page", disabled=(current_page == 0)):
            st.session_state.current_page -= 1
            st.rerun()
    
    with col2:
        st.write(f"Page {current_page + 1} of {total_pages}")
    
    with col3:
        if st.button("Next Page ➡️", disabled=(current_page >= total_pages - 1)):
            st.session_state.current_page += 1
            st.rerun()
    
    # Final score
    if len(st.session_state.answered) == total:
        st.balloons()
        st.success(f"🎉 Quiz Complete! Final Score: {st.session_state.score}/{total} ({st.session_state.score/total*100:.1f}%)")
        
        if st.button("🔄 Restart Quiz"):
            st.session_state.current_page = 0
            st.session_state.score = 0
            st.session_state.answered = {}
            st.session_state.explanations = {}
            st.rerun()
