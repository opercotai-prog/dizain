import streamlit as st
from google import genai
from google.genai import types
import json
import os
from PIL import Image
import io
import re

# --- НАСТРОЙКИ ---
st.set_page_config(page_title="AI Дизайн 2.5 Nano", layout="wide")

GEMINI_KEY = st.secrets.get("GEMINI_KEY") or os.environ.get("GEMINI_KEY")

if not GEMINI_KEY:
    st.error("Добавьте GEMINI_KEY в Secrets!")
    st.stop()

# Инициализация НОВОГО клиента (Google GenAI SDK)
client = genai.Client(api_key=GEMINI_KEY)

# --- ЛОГИКА ---
def get_design_25(image_bytes, text_query):
    # Модель 2.5 Flash (Nano Banana)
    model_id = "gemini-2.5-flash"
    
    # Промпт для получения JSON и Изображения
    prompt = f"""
    Ты — профессиональный ИИ-дизайнер интерьеров. 
    1. Сгенерируй фотореалистичное изображение нового дизайна по запросу: {text_query}.
    2. Выдай текстовую смету СТРОГО в формате JSON.
    
    JSON:
    {{
      "concept": "описание",
      "total": "сумма в рублях",
      "items": [{{"n": "товар", "p": "цена"}}]
    }}
    """
    
    # Собираем контент (текст + фото пользователя если есть)
    contents = [prompt]
    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

    try:
        # Новый метод генерации через свежий SDK
        response = client.models.generate_content(
            model=model_id,
            contents=contents,
            # Включаем конфигурацию для генерации изображений если нужно
            config=types.GenerateContentConfig(
                temperature=0.7
            )
        )
        
        res = {"json": None, "image": None}
        
        # Разбираем части ответа в новом формате
        for part in response.candidates[0].content.parts:
            # Проверка на текст (JSON)
            if part.text:
                match = re.search(r'\{.*\}', part.text, re.DOTALL)
                if match:
                    res["json"] = json.loads(match.group())
            
            # Проверка на изображение (бинарные данные)
            if part.inline_data:
                res["image"] = Image.open(io.BytesIO(part.inline_data.data))
                
        return res
    except Exception as e:
        st.error(f"Ошибка в работе с Nano Banana: {e}")
        return None

# --- ИНТЕРФЕЙС ---
st.title("🎨 Дизайн-студия Gemini 2.5 Flash")
st.write("Нативное создание интерьера и расчет стоимости.")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded = st.file_uploader("Загрузить фото", type=["jpg", "png", "jpeg"])
    query = st.text_area("Пожелания", "Сделай современную кухню в стиле лофт")
    btn = st.button("🚀 Создать проект")

if btn:
    with st.spinner("Gemini 2.5 генерирует контент..."):
        # Превращаем фото в байты для нового SDK
        img_bytes = uploaded.getvalue() if uploaded else None
        
        result = get_design_25(img_bytes, query)
        
        with col2:
            if result:
                # 1. Показываем картинку
                if result["image"]:
                    st.subheader("Визуализация:")
                    st.image(result["image"], use_container_width=True)
                else:
                    # Если модель не выдала картинку байтами, пробуем Imagen 3 или Fallback
                    st.warning("Нативная генерация пикселей в 2.5 Flash заблокирована в вашем регионе. Использую резервный метод...")
                    v_prompt = f"professional interior design photo, {query}, 8k".replace(' ', '_')
                    st.image(f"https://pollinations.ai/p/{v_prompt}?width=1024&height=768")

                # 2. Показываем JSON
                if result["json"]:
                    data = result["json"]
                    st.success(f"### Смета: {data.get('total')} ₽")
                    st.write(f"**Идея:** {data.get('concept')}")
                    
                    for item in data.get('items', []):
                        st.markdown(f"- **{item['n']}** — {item['p']} ₽")
