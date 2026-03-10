import streamlit as st
import google.generativeai as genai
import json
import requests
from PIL import Image
import os
import io

# --- НАСТРОЙКИ ---
GEMINI_KEY = os.environ.get('GEMINI_KEY') 
if not GEMINI_KEY:
    GEMINI_KEY = st.sidebar.text_input("Введите Gemini API Key", type="password")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="AI Дизайн Интерьера", layout="wide")
st.title("🎨 Дизайн и расчет стоимости ремонта (Gemini 2.5)")
st.write("Загрузите фото и напишите пожелания — ИИ создаст новый дизайн и посчитает смету.")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("Загрузите фото (необязательно)", type=["jpg", "jpeg", "png"])
    user_text = st.text_area("Что вы хотите изменить?", placeholder="Например: Сделай кухню в стиле лофт, бюджет 200к")
    submit_btn = st.button("Рассчитать и создать дизайн")

# --- ЛОГИКА ---
def get_design_analysis(image, text):
    # Используем модель 2.5-flash (Nano Banana)
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    
    prompt = f"""
    Ты эксперт по дизайну интерьера. Проанализируй запрос: "{text}".
    Если есть фото, используй его как основу.
    
    ЗАДАЧА:
    1. Выдай ответ СТРОГО в формате JSON со сметой.
    2. Сгенерируй реалистичное изображение (фото) нового дизайна интерьера.
    
    JSON СТРУКТУРА:
    {{
      "analysis": "краткое описание решения",
      "total_cost": "общая сумма в рублях",
      "items": [
        {{"name": "название предмета", "price": "цена"}}
      ]
    }}
    """
    
    content = [prompt]
    if image:
        content.append(image)
        
    response = model.generate_content(content)
    
    res_data = {"json": None, "image": None}
    
    # Разбираем мультимодальный ответ от 2.5-flash
    for part in response.candidates[0].content.parts:
        if part.text:
            # Очистка и загрузка JSON
            json_str = part.text.replace('```json', '').replace('```', '').strip()
            res_data["json"] = json.loads(json_str)
        if part.inline_data:
            # Получаем сгенерированное изображение напрямую из модели
            img_bytes = part.inline_data.data
            res_data["image"] = Image.open(io.BytesIO(img_bytes))
            
    return res_data

if submit_btn:
    if not GEMINI_KEY:
        st.error("Нужен API Ключ Gemini!")
    else:
        with st.spinner('Gemini 2.5 генерирует проект и изображение...'):
            img_input = Image.open(uploaded_file) if uploaded_file else None
            
            # Получаем результат (JSON + Image)
            result = get_design_analysis(img_input, user_text)
            data = result["json"]
            gen_image = result["image"]
            
            with col2:
                st.subheader("Результат:")
                
                # Показываем СГЕНЕРИРОВАННОЕ моделью фото
                if gen_image:
                    st.image(gen_image, caption="Дизайн от Gemini 2.5 Flash", use_container_width=True)
                else:
                    st.warning("Модель не вернула изображение. Проверьте настройки API.")

                if data:
                    st.write(f"**Идея:** {data['analysis']}")
                    st.write(f"### 💰 Ориентировочная стоимость: {data['total_cost']} руб.")
                    
                    st.write("### 🛒 Список покупок:")
                    for item in data['items']:
                        search_url = f"https://www.google.com/search?q=купить+{item['name'].replace(' ', '+')}"
                        st.markdown(f"- **{item['name']}** (~{item['price']}р) — [Найти в магазинах]({search_url})")

with st.expander("Инструкция"):
    st.write("Для работы используется модель gemini-2.5-flash с нативной генерацией изображений.")
