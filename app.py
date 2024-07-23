import streamlit as st
import google.generativeai as genai
from pathlib import Path

# Streamlit app configuration
st.set_page_config(page_title="VitalImage Analytics", layout="wide")
st.image("logo.png", width=200)
st.title("👩‍⚕️🩺MedInsights: Your AI-Driven Healthcare Analytics Assistant👩‍⚕️🩺")
st.subheader(
    "Data is the pulse of modern healthcare. Harness its power with MedInsights."
)

# Model configuration
api_key = "YOUR-API-KEY"
genai.configure(api_key=api_key)
system_prompts = """Role: You are MedInsights, an advanced AI-driven healthcare assistant designed to provide detailed medical analysis and insights from uploaded medical images.

Responsibilities:

Detailed Analysis: Perform a thorough examination of the uploaded medical images, identifying any abnormalities or significant findings.
Scope of Response: Clearly define the scope of your analysis and provide context to your findings, ensuring the user understands the significance of the results.
Finding Reports: Generate comprehensive reports that summarize your findings in an understandable and actionable format.
Recommendations for Next Steps: Suggest appropriate next steps based on the analysis, including potential diagnostic tests or further imaging if necessary.
Treatment Suggestions: Offer potential treatment options or refer the user to relevant medical specialists based on the findings."""
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    # safety_settings = Adjust safety settings
    # See https://ai.google.dev/gemini-api/docs/safety-settings
)


def upload_to_gemini(file, mime_type):
    """Uploads the given file to Gemini."""
    uploaded_file = genai.upload_file(file, mime_type=mime_type)
    return uploaded_file


def add_to_history(title, image, result):
    """Add the analysis result to the history."""
    if "history" not in st.session_state:
        st.session_state.history = []
    st.session_state.history.append({"title": title, "image": image, "result": result})


# Initialize session state
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "selected_analysis" not in st.session_state:
    st.session_state.selected_analysis = None
if "history" not in st.session_state:
    st.session_state.history = []
if "saved" not in st.session_state:
    st.session_state.saved = False

# Sidebar navigation
with st.sidebar:
    st.title("MedInsights")
    st.subheader("Navigation")
    page = st.radio("Go to", ["Home", "History"])

    if page == "History":
        if st.session_state.history:
            titles = [entry["title"] for entry in st.session_state.history]
            if titles:
                selected_title = st.selectbox("Select an analysis", titles)
                if selected_title:
                    st.session_state.selected_analysis = next(
                        entry
                        for entry in st.session_state.history
                        if entry["title"] == selected_title
                    )
            else:
                st.write("No history available.")
        else:
            st.write("No history available.")

if page == "Home":
    # File uploader widget
    uploaded_file = st.file_uploader(
        "Upload the medical image for analysis",
        type=["png", "jpg", "jpeg"],
    )

    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file

    if st.session_state.uploaded_file is not None:
        mime_type = st.session_state.uploaded_file.type
        temp_file_path = Path("temp_" + st.session_state.uploaded_file.name)

        # Save the uploaded file temporarily
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(st.session_state.uploaded_file.getbuffer())

        # Upload to Gemini
        gemini_file = upload_to_gemini(temp_file_path, mime_type)

        # Display the analysis button
        if st.button("Get your analysis"):
            prompts_part = [gemini_file.uri, system_prompts]
            # Generate the response
            res = model.generate_content(prompts_part)

            # Display the uploaded image and the generated response
            st.image(st.session_state.uploaded_file, width=400)
            st.write(res.text)

            # Save to history
            title = st.text_input("Enter a title for this analysis")
            save_button = st.button("Save analysis", key="save_button")

            if save_button:
                add_to_history(title, st.session_state.uploaded_file, res.text)
                st.session_state.saved = True
                st.success("Analysis saved to history.")
elif page == "History" and st.session_state.selected_analysis:
    st.header("Analysis Details")
    st.image(st.session_state.selected_analysis["image"], width=400)
    st.write(st.session_state.selected_analysis["result"])

if st.session_state.saved:
    # Reset the saved state after showing the success message
    st.session_state.saved = False
