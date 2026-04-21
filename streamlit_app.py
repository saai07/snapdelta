import streamlit as st
import requests
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="SnapDelta", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%); }
    .main-title {
        text-align: center;
        background: linear-gradient(90deg, #ff6b6b, #ffa500, #ff6b6b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    .subtitle {
        text-align: center;
        color: #8888aa;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .stat-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #ff6b6b, #ffa500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-label { color: #8888aa; font-size: 0.9rem; }
    div[data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.03);
        border: 2px dashed rgba(255,255,255,0.15);
        border-radius: 12px;
        padding: 1rem;
    }
    .stButton > button {
        background: linear-gradient(90deg, #ff6b6b, #ffa500);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        width: 100%;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(255, 107, 107, 0.3);
    }
</style>
""", unsafe_allow_html=True)

import os
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.markdown('<p class="main-title">🔍 SnapDelta</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-powered visual diff detection — upload two screenshots and see what changed</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📸 Before Screenshot")
    before_file = st.file_uploader("Upload the BEFORE image", type=["png", "jpg", "jpeg", "webp"], key="before")

with col2:
    st.markdown("#### 📸 After Screenshot")
    after_file = st.file_uploader("Upload the AFTER image", type=["png", "jpg", "jpeg", "webp"], key="after")

st.markdown("")

if st.button("🚀 Detect Changes", disabled=not (before_file and after_file)):
    if before_file and after_file:
        with st.spinner("Analyzing screenshots..."):
            try:
                before_file.seek(0)
                after_file.seek(0)

                files = {
                    "before": (before_file.name, before_file.getvalue(), "image/png"),
                    "after": (after_file.name, after_file.getvalue(), "image/png"),
                }
                response = requests.post(f"{API_URL}/diff", files=files, timeout=300)
                response.raise_for_status()
                result = response.json()

                job_id = result["job_id"]
                changes = result["changes_detected"]

                st.markdown("---")

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-number">{changes}</div>
                        <div class="stat-label">Changes Detected</div>
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-number" style="font-size:1.2rem;">{job_id[:8]}...</div>
                        <div class="stat-label">Job ID</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("")
                st.markdown("#### Diff Result")

                img_response = requests.get(f"{API_URL}/result/{job_id}", timeout=30)
                img_response.raise_for_status()
                diff_image = Image.open(BytesIO(img_response.content))
                st.image(diff_image, caption="Changes highlighted with bounding boxes", width='stretch')

                buf = BytesIO()
                diff_image.save(buf, format="PNG")
                st.download_button(
                    label="Download Diff Image",
                    data=buf.getvalue(),
                    file_name=f"snapdelta_{job_id[:8]}.png",
                    mime="image/png",
                )

            except requests.ConnectionError:
                st.error(" Cannot connect to the API. Make sure the FastAPI server is running on port 8000.")
            except requests.HTTPError as e:
                st.error(f" API error: {e.response.status_code} — {e.response.text}")
            except Exception as e:
                st.error(f" Something went wrong: {str(e)}")
