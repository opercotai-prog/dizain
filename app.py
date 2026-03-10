import streamlit as st
from google import genai
from google.genai import types
import json
import os
import re
import urllib.parse # Добавили для очистки ссылок

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(page_title="AI Interior Pro", page_icon="🏡", layout="wide")

# (Тут идет твой CSS из прошлого сообщения, я его пропущу для краткости)

GEMINI_KEY = st.secrets.get("GEMINI_KEY") or os.environ.get("GEMINI_KEY")
client = genai.Client(api_key=GEMINI_KEY)

def get_design_data(image_bytes, text_query):
    model_id = "gemini-2.5-flash"
    prompt = f"""
    Ты — элитный дизайнер. Проанализируй запрос: "{text_query}".
    Выдай ответ СТРОГО в JSON.
    JSON:
    {{
      "concept": "описание",
      "total_budget": "сумма",
      "items": [{{"name": "товар", "price": "цена"}}],
      "visual_prompt": "A professional interior design photo of a room, {text_query}, photorealistic, 8k, highly detailed"
    }}
    """
    contents = [prompt]
    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

    try:
        response = client.models.generate_content(model=model_id, contents=contents)
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        return json.loads(match.group()) if match else None
    except:
        return None

# --- ИНТЕРФЕЙС ---
st.title("🏡 AI Interior Studio")

col_in, col_out = st.columns([1, 1.2])

with col_in:
    uploaded = st.file_uploader("Загрузите фото", type=["jpg", "png", "jpeg"])
    query = st.text_area("Что изменить?", "Современная кухня")
    run_btn = st.button("🚀 Создать дизайн")

with col_out:
    if run_btn:
        with st.spinner("💎 Генерируем проект..."):
            img_data = uploaded.getvalue() if uploaded else None
            data = get_design_data(img_data, query)
            
            if data:
                st.subheader("✨ Визуализация")
                
                # --- ИСПРАВЛЕННЫЙ БЛОК ГЕНЕРАЦИИ КАРТИНКИ ---
                raw_prompt = data.get('visual_prompt', f"professional interior design for {query}")
                
                # 1. Очищаем промпт от лишних символов и кодируем для URL
                clean_prompt = urllib.parse.quote(raw_prompt)
                
                # 2. Формируем надежную ссылку (добавляем seed для уникальности)
                import random
                seed = random.randint(1, 1000)
                image_url = f"https://pollinations.ai/p/{clean_prompt}?width=1280&height=720&seed={seed}&model=flux"
                
                # 3. Выводим картинку с обработкой ошибки
                try:
                    st.image(image_url, width='stretch', caption="Ваш новый интерьер")
                except:
                    st.error("Не удалось загрузить изображение. Попробуйте нажать кнопку еще раз.")
                
                # --- ВЫВОД ДАННЫХ ---
                st.metric("Бюджет", f"{data.get('total_budget')} ₽")
                st.write(f"**Идея:** {data.get('concept')}")
                
                for item in data.get('items', []):
                    st.markdown(f"✅ {item['name']} — **{item['price']} ₽**")
            else:
                st.error("ИИ не смог составить смету. Попробуйте другой запрос.")
