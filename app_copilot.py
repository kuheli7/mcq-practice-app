import json
import streamlit as st
import requests

def generate_mcq_with_copilot(topic: str, num_questions: int = 1) -> list:
    """Generate MCQs using GitHub Copilot API"""
    
    # Note: GitHub Copilot doesn't have a public API for chat/generation
    # This is a placeholder. You would need to use:
    # 1. GitHub Copilot Chat API (if available through extensions)
    # 2. Or use GitHub Models (preview) which gives access to various AI models
    
    st.error("GitHub Copilot doesn't currently offer a public API for question generation.")
    st.info("However, you can use GitHub Models (free preview) which provides access to GPT-4o, Claude, etc.")
    return []

def generate_mcq_with_github_models(topic: str, num_questions: int = 1, github_token: str = "") -> list:
    """Generate MCQs using GitHub Models API"""
    
    if not github_token:
        st.error("GitHub Personal Access Token required")
        return []
    
    prompt = f"""Generate {num_questions} multiple-choice questions about {topic}.

Return ONLY valid JSON in this format:
[
  {{
    "question": "...",
    "options": ["A", "B", "C", "D"],
    "correct_index": 0
  }}
]"""
    
    try:
        # GitHub Models API endpoint
        response = requests.post(
            "https://models.inference.ai.azure.com/chat/completions",
            headers={
                "Authorization": f"Bearer {github_token}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",  # or "claude-3.5-sonnet", "mistral-large"
                "messages": [
                    {"role": "system", "content": "You are an MCQ generator. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
        )
        
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            # Extract JSON
            start = content.find("[")
            end = content.rfind("]") + 1
            return json.loads(content[start:end])
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []


# ---------- Streamlit UI ----------
st.title("🤖 MCQ Generator with GitHub Models")

st.info("""
This app uses **GitHub Models** (free preview) to generate questions.

To get started:
1. Go to https://github.com/marketplace/models
2. Sign in and get access to GitHub Models (free preview)
3. Create a Personal Access Token at https://github.com/settings/tokens
   - Select 'Models' scope
4. Paste your token below
""")

github_token = st.text_input("GitHub Personal Access Token", type="password")

if "mcqs" not in st.session_state:
    st.session_state.mcqs = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "answered" not in st.session_state:
    st.session_state.answered = set()

# Mode selector
mode = st.radio("Choose mode:", ["Generate with AI", "Upload JSON"], horizontal=True)

if mode == "Generate with AI":
    topic = st.text_input("Enter topic", "Operating Systems Memory Management")
    num_questions = st.number_input("Number of questions", min_value=1, max_value=50, value=5)
    
    if st.button("Generate Questions") and github_token:
        with st.spinner(f"Generating {num_questions} questions..."):
            st.session_state.mcqs = generate_mcq_with_github_models(topic, num_questions, github_token)
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.answered = set()
            if st.session_state.mcqs:
                st.success(f"✅ Generated {len(st.session_state.mcqs)} questions!")
                st.rerun()
else:
    uploaded_file = st.file_uploader("Upload JSON file", type=["json"])
    if uploaded_file and st.button("Load Questions"):
        data = json.loads(uploaded_file.read())
        st.session_state.mcqs = data.get("questions", data) if isinstance(data, dict) else data
        st.session_state.current_index = 0
        st.session_state.score = 0
        st.session_state.answered = set()
        st.success(f"✅ Loaded {len(st.session_state.mcqs)} questions!")
        st.rerun()

# Display MCQs
if st.session_state.mcqs:
    total = len(st.session_state.mcqs)
    idx = st.session_state.current_index
    
    col1, col2 = st.columns(2)
    with col1:
        st.progress((idx + 1) / total)
        st.write(f"**Question {idx + 1} of {total}**")
    with col2:
        st.metric("Score", f"{st.session_state.score}/{len(st.session_state.answered)}")
    
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
            st.rerun()
    
    with col2:
        if st.button("Check Answer") and choice is not None:
            correct = mcq["options"][mcq["correct_index"]]
            if idx not in st.session_state.answered:
                st.session_state.answered.add(idx)
                if choice == correct:
                    st.session_state.score += 1
            
            if choice == correct:
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Wrong. Correct answer: {correct}")
    
    with col3:
        if st.button("Next ➡️") and idx < total - 1:
            st.session_state.current_index += 1
            st.rerun()
    
    if len(st.session_state.answered) == total:
        st.balloons()
        st.success(f"🎉 Quiz Complete! Final Score: {st.session_state.score}/{total} ({st.session_state.score/total*100:.1f}%)")
        
        if st.button("🔄 Restart"):
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.answered = set()
            st.rerun()
