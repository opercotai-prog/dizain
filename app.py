import streamlit as st
from google import genai
from google.genai import types
import json
import os
from PIL import Image
import io
import re

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(
    page_title="AI Interior Pro", 
    page_icon="🏡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- СТИЛИЗАЦИЯ (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background: linear-gradient(90deg, #007AFF 0%, #00C6FF 100%);
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.6rem;
        transition: 0.3s;
    }
    .stButton>button:hover { opacity: 0.9; transform: translateY(-2px); }
    .price-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-left: 5px solid #007AFF;
        margin-bottom: 1rem;
    }
    .shopping-item {
        background-color: #ffffff;
        padding: 10px 15px;
        border-radius: 10px;
        margin-bottom: 8px;
        border: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ИНИЦИАЛИЗАЦИЯ API ---
GEMINI_KEY = st.secrets.get("GEMINI_KEY") or os.environ.get("GEMINI_KEY")

if not GEMINI_KEY:
    st.error("🔑 API Ключ не найден. Добавьте его в Secrets.")
    st.stop()

client = genai.Client(api_key=GEMINI_KEY)

# --- ЛОГИКА ---
def get_design_data(image_bytes, text_query):
    model_id = "gemini-2.5-flash"
    
    prompt = f"""
    Ты — элитный дизайнер интерьеров. 
    Твоя задача:
    1. Проанализировать запрос: "{text_query}"
    2. Если есть фото, сохрани планировку, но полностью обнови стиль.
    3. Выдай ответ СТРОГО в JSON.
    4. Создай детальный промпт для фото-генератора на английском.

    JSON Structure:
    {{
      "concept": "Подробное описание идеи на русском",
      "total_budget": "Примерная сумма в рублях",
      "items": [
        {{"name": "Предмет мебели", "price": "Цена", "style": "Стиль"}}
      ],
      "visual_prompt": "Ultra-realistic 8k interior design, architectural photography, [STYLE], highly detailed, cinematic lighting"
    }}
    """
    
    contents = [prompt]
    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

    try:
        response = client.models.generate_content(model=model_id, contents=contents)
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        return json.loads(match.group()) if match else None
    except Exception as e:
        st.error(f"Ошибка ИИ: {e}")
        return None

# --- ИНТЕРФЕЙС ---
st.title("🏡 AI Interior Studio")
st.markdown("##### Превратите ваши идеи в готовый дизайн-проект за секунды")

col_in, col_out = st.columns([1, 1.2], gap="large")

with col_in:
    st.subheader("🛠 Параметры проекта")
    uploaded = st.file_uploader("Загрузите фото комнаты (необязательно)", type=["jpg", "png", "jpeg"])
    
    if uploaded:
        st.image(uploaded, caption="Исходное помещение", width='stretch')
    
    query = st.text_area(
        "Что мы создаем?", 
        placeholder="Например: Уютная спальня в стиле Джапанди с элементами светлого дерева...",
        height=120
    )
    
    run_btn = st.button("🚀 Создать дизайн")

with col_out:
    if run_btn:
        with st.spinner("💎 Создаем шедевр..."):
            img_data = uploaded.getvalue() if uploaded else None
            data = get_design_data(img_data, query)
            
            if data:
                # 1. ВИЗУАЛИЗАЦИЯ
                st.subheader("✨ Визуализация")
                v_prompt = data.get('visual_prompt', 'luxury interior').replace(' ', '_')
                # Используем seed для разнообразия
                image_url = f"https://pollinations.ai/p/{v_prompt}?width=1280&height=720&seed=42"
                st.image(image_url, width='stretch', caption="Предлагаемый концепт")
                
                # 2. БЮДЖЕТ И КОНЦЕПЦИЯ
                st.markdown(f"""
                <div class="price-card">
                    <h2 style='margin:0; color:#007AFF;'>{data.get('total_budget')} ₽</h2>
                    <p style='margin:0; opacity:0.8;'>Ориентировочный бюджет проекта</p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("📖 Описание идеи", expanded=True):
                    st.write(data.get('concept'))
                
                # 3. СПИСОК ПОКУПОК
                st.subheader("🛒 Предметы интерьера")
                for item in data.get('items', []):
                    search_query = f"купить {item['name']} {item.get('style', '')}".replace(' ', '+')
                    # Ссылки для поиска
                    google_link = f"https://www.google.com/search?q={search_query}"
                    
                    st.markdown(f"""
                    <div class="shopping-item">
                        <div style="display: flex; justify-content: space-between;">
                            <b>{item['name']}</b>
                            <span style="color: #007AFF; font-weight: bold;">{item['price']} ₽</span>
                        </div>
                        <div style="font-size: 0.85rem; opacity: 0.7;">Стиль: {item.get('style', 'Оригинальный')}</div>
                        <a href="{google_link}" target="_blank" style="font-size: 0.8rem; color: #007AFF; text-decoration: none;">🔍 Найти в магазинах</a>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.error("Не удалось сгенерировать данные. Попробуйте еще раз.")

# --- ПОДВАЛ ---
st.sidebar.markdown(f"""
**Конфигурация:**
- Модель: Gemini 2.5 Flash
- Регион: EU (Netherlands)
- Отрисовка: External Engine
---
v1.2 | 2026
""")
