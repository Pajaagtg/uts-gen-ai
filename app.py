import streamlit as st
import google.generativeai as genai
import requests
import time
import os
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_available_model():
    preferred_models = ["gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-2.0-flash"]
    for model_name in preferred_models:
        try:
            model = genai.GenerativeModel(model_name)
            model.generate_content("test")
            return model_name
        except Exception:
            continue
    try:
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                return model.name
    except Exception:
        pass
    return None

def generate_recipe(ingredients, retries=3):
    model_name = get_available_model()
    if not model_name:
        return "Error: Tidak ada model Gemini yang tersedia."

    prompt = f"""
    Pengguna memiliki bahan: "{ingredients}"
    Berikan 1 resep makanan sehat.
    Format: Nama Masakan, Bahan, Langkah, Tips Kesehatan.
    """
    model = genai.GenerativeModel(model_name)

    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) and attempt < retries - 1:
                wait_time = (2 ** attempt) * 10
                time.sleep(wait_time)
            else:
                return f"Error: {str(e)}"

def generate_food_image_url(recipe_text):
    image_prompt = f"Realistic photo of healthy dish: {recipe_text[:100]}"
    encoded_prompt = requests.utils.quote(image_prompt)
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}"

def download_image(url):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200 and 'image' in response.headers.get('content-type', ''):
            return Image.open(BytesIO(response.content))
    except Exception:
        pass
    return None

st.set_page_config(page_title="Personal Diet Planner", page_icon=":salad:")
st.title("Personal Diet Planner AI")
st.markdown("Masukkan bahan makanan di kulkas, dapatkan resep sehat dan gambar masakan.")

user_input = st.text_area("Bahan makanan (pisahkan dengan koma)", height=100)

if st.button("Generate Resep dan Gambar"):
    if not user_input.strip():
        st.warning("Masukkan bahan makanan terlebih dahulu.")
    else:
        with st.spinner("Memproses resep..."):
            recipe = generate_recipe(user_input)

        if recipe.startswith("Error"):
            st.error(recipe)
        else:
            st.subheader("Resep Sehat")
            st.write(recipe)

            st.subheader("Visual Masakan")
            with st.spinner("Mengunduh gambar..."):
                image_url = generate_food_image_url(recipe)
                image = download_image(image_url)
                if image:
                    st.image(image, use_container_width=True)
                else:
                    st.warning("Gambar tidak dapat dimuat. Coba lagi nanti.")
                    st.image("https://via.placeholder.com/512x512?text=Gambar+Tidak+Ada", use_container_width=True)