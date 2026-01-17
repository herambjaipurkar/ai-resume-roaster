import streamlit as st
import google.genai as genai  # Updated import
import PyPDF2
import stripe
import json
import os  # For env var

# Set Gemini key from secret
os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

# Set Stripe from secrets
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
STRIPE_PUBLISHABLE_KEY = st.secrets["STRIPE_PUBLISHABLE_KEY"]  # Optional
STRIPE_PRICE_ID = st.secrets["STRIPE_PRICE_ID"]  # Optional

client = genai.Client()  # Uses env var now

stripe.api_key = STRIPE_SECRET_KEY

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Function to get AI response (updated for new SDK)
def get_ai_response(user_resume):
    prompt = f"""
    Act as a ruthless senior tech recruiter.
    1. Read this resume: {user_resume}
    2. Give a "Roast": A 2-sentence savage critique of why this resume is bad. Be funny but harsh.
    3. Give "The Fix": 3 concrete, professional improvements they must make immediately.
    Return as JSON: {{ "roast": "", "fix": [] }}
    """

    # New generation call
    response = client.models.generate_content(
        model='gemini-2.5-flash',  # Updated model (fast and available in 2026)
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json"  # Ensures JSON output
        )
    )

    try:
        json_response = json.loads(response.text.strip())  # Parse JSON
        return json_response
    except:
        return {"roast": "Error parsing response.", "fix": []}

# Streamlit App
st.title("AI Resume Roaster")
st.header("Your Resume Sucks. Let AI Tell You Why.")
st.write("Paste your resume text or upload a PDF. Get a free roast, pay $5 for fixes.")

# Input: Text or PDF upload
resume_text = st.text_area("Paste your resume text here:", height=300)
uploaded_file = st.file_uploader("Or upload PDF resume", type="pdf")

if uploaded_file:
    resume_text = extract_text_from_pdf(uploaded_file)

if st.button("Roast My Resume"):
    if resume_text:
        with st.spinner("Roasting..."):
            ai_response = get_ai_response(resume_text)
            st.subheader("The Roast (Free):")
            st.write(ai_response.get("roast", "No roast generated."))

            # Paid Fix Section
            st.subheader("Want The Fix? Pay $5")
            st.write("Get 3 pro tips to fix your resume.")

            # Stripe Payment (simple checkout)
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': STRIPE_PRICE_ID,
                    'quantity': 1,
                }],
                mode='payment',
                success_url="https://ai-resume-roaster-drbrsy5qtpk4ks62vcxmnb.streamlit.app/",  # For local testing; replace with https://your-streamlit-app-url.streamlit.app once deployed
                cancel_url="https://ai-resume-roaster-drbrsy5qtpk4ks62vcxmnb.streamlit.app/",  # Same as above
            )
            st.markdown(f'<a href="{session.url}" target="_blank"><button>Pay $5 Now</button></a>', unsafe_allow_html=True)

            # After payment (check session – simple for MVP)
            session_id = st.query_params.get('session_id', [None])[0]  # Updated: Use st.query_params instead
            if session_id:
                retrieved_session = stripe.checkout.Session.retrieve(session_id)
                if retrieved_session.payment_status == 'paid':
                    st.subheader("The Fix (Paid):")
                    for fix in ai_response.get("fix", []):
                        st.write(f"- {fix}")

# Demo Example on Home
st.subheader("Demo Example")
st.write("Roast: 'This resume looks like it was written by a robot who hates jobs. No achievements, just duties – you're basically saying you're average at everything.'")

st.write("Fix (Paid): 1. Add quantifiable achievements. 2. Tailor to job keywords. 3. Shorten to 1 page.")


