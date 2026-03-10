import streamlit as st
from google import genai
from google.genai import types
import json
import os
from PIL import Image
import io
import re

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(page_title="AI Дизайн-Сервис", layout="wide")

# Получение ключа из Secrets
GEMINI_KEY = st.secrets.get("GEMINI_KEY") or os.environ.get("GEMINI_KEY")

if not GEMINI_KEY:
    st.error("Ошибка: Добавьте GEMINI_KEY в Secrets (на Streamlit Cloud).")
    st.stop()

# Инициализация нового SDK
client = genai.Client(api_key=GEMINI_KEY)

def get_design_data(image_bytes, text_query):
    model_id = "gemini-2.5-flash"
    
    # Промпт оптимизирован: мы просим ИИ создать "Image Prompt" для отрисовки
    prompt = f"""
    Ты — эксперт по дизайну интерьеров. 
    1. Проанализируй фото (если есть) и запрос: {text_query}.
    2. Составь смету в JSON.
    3. Составь подробный промпт на английском для генерации ФОТО этого дизайна.
    
    Ответ выдай СТРОГО в формате JSON:
    {{
      "concept": "описание идеи на русском",
      "total_price": "сумма в рублях",
      "items": [{{"n": "товар", "p": "цена"}}],
      "visual_prompt": "detailed professional interior design photo, [STYLE], photorealistic, 8k, architectural lighting"
    }}
    """
    
    contents = [prompt]
    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

    try:
        response = client.models.generate_content(model=model_id, contents=contents)
        
        # Чистим ответ и достаем JSON
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return None
    except Exception as e:
        st.error(f"Ошибка ИИ: {e}")
        return None

# --- ИНТЕРФЕЙС ---
st.title("🏡 AI Студия Дизайна (Gemini 2.5 Flash)")
st.write("Создание дизайна и расчет стоимости предметов.")

col_in, col_out = st.columns([1, 1], gap="large")

with col_in:
    uploaded = st.file_uploader("Загрузите фото комнаты", type=["jpg", "png", "jpeg"])
    if uploaded:
        st.image(uploaded, caption="Текущее состояние", use_container_width=True)
    
    query = st.text_area("Что вы хотите изменить?", "Например: современная кухня в стиле минимализм с черными акцентами")
    run_btn = st.button("🚀 Создать дизайн-проект")

with col_out:
    if run_btn:
        with st.spinner("Gemini 2.5 анализирует и планирует..."):
            img_data = uploaded.getvalue() if uploaded else None
            data = get_design_data(img_data, query)
            
            if data:
                # 1. ГЕНЕРАЦИЯ КАРТИНКИ (Внешний движок, обходящий блокировку EU)
                st.subheader("Визуализация проекта:")
                # Берем промпт, созданный Gemini, и скармливаем его генератору
                clean_prompt = data.get('visual_prompt', 'interior design').replace(' ', '_')
                # Добавляем случайный seed для уникальности
                image_url = f"https://pollinations.ai/p/{clean_prompt}?width=1280&height=720&seed=123"
                st.image(image_url, use_container_width=True, caption="Ваш будущий интерьер")
                
                # 2. ВЫВОД ДАННЫХ
                st.success(f"### Смета: {data.get('total_price')} ₽")
                
                with st.expander("📄 Описание концепции"):
                    st.write(data.get('concept'))
                
                st.subheader("🛒 Предметы интерьера:")
                for item in data.get('items', []):
                    search_url = f"https://www.google.com/search?q=купить+{item['n'].replace(' ', '+')}"
                    st.markdown(f"- **[{item['n']}]({search_url})** — {item['p']} ₽")
            else:
                st.error("Не удалось получить данные. Попробуйте еще раз.")

# --- ПОДВАЛ ---
st.sidebar.markdown("""
**Статус системы:**
- SDK: Google GenAI (Active)
- Модель: Gemini 2.5 Flash
- Регион: EU Optimized
""")
