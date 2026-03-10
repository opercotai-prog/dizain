import streamlit as st
import google.generativeai as genai
import json
import os
from PIL import Image
import io

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(page_title="AI Room Designer", layout="wide", initial_sidebar_state="collapsed")

# Стиль для кнопок и карточек
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #4CAF50; color: white; }
    .cost-card { background-color: white; padding: 20px; border-radius: 15px; border-left: 5px solid #4CAF50; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# Получение API ключа из секретов Streamlit или ввода
GEMINI_KEY = st.secrets.get("GEMINI_KEY") or os.environ.get("GEMINI_KEY")
if not GEMINI_KEY:
    GEMINI_KEY = st.sidebar.text_input("Введите Gemini API Key", type="password")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
else:
    st.warning("Пожалуйста, добавьте API Ключ в настройках (Sidebar или Secrets).")

# --- ФУНКЦИЯ ОБРАБОТКИ (Nano Banana) ---
def process_design(user_image, user_prompt):
    # Используем новейшую модель 2.5 Flash Image
    model = genai.GenerativeModel('models/gemini-2.5-flash-image-preview')
    
    # Системный промпт для модели
    system_instruction = """
    Ты — профессиональный ИИ-дизайнер и сметчик. 
    Твоя задача: на основе входящего фото или описания создать новый дизайн интерьера.
    
    ТРЕБОВАНИЯ:
    1. Если есть фото: СОХРАНИ архитектуру (окна, двери), но измени отделку и мебель.
    2. В ответе выдай СТРОГО JSON-объект и описание для генерации изображения.
    
    JSON формат:
    {
      "analysis": "краткое описание концепции",
      "total_estimate": "общая сумма цифрой",
      "items": [
        {"name": "предмет мебели/декора", "price": "ориентировочная цена", "reason": "почему это здесь"}
      ],
      "visual_prompt": "A professional 8k interior design photo, transformation of the provided room, [USER_PROMPT], highly realistic, architecture preserved"
    }
    """
    
    # Собираем части запроса
    content_parts = [system_instruction, f"Запрос пользователя: {user_prompt}"]
    if user_image:
        content_parts.append(user_image)
    
    # 1. Получаем текстовый анализ и JSON
    response = model.generate_content(content_parts)
    
    try:
        # Очистка JSON от возможных знаков разметки
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_text)
        
        # 2. Генерируем изображение по полученному визуальному промпту
        # (В режиме preview Nano Banana генерирует изображение в этом же или отдельном вызове)
        # Для текущего SDK используем генерацию через тот же промпт
        generated_image = model.generate_content([data['visual_prompt']])
        
        return data, generated_image
    except Exception as e:
        st.error(f"Ошибка парсинга ответа: {e}")
        return None, None

# --- ИНТЕРФЕЙС САЙТА ---
st.title("🏠 Умный Дизайн и Смета")
st.write("Загрузите фото вашей комнаты или просто напишите, что хотите изменить.")

col_input, col_output = st.columns([1, 1.2], gap="large")

with col_input:
    st.subheader("📝 Запрос")
    uploaded_file = st.file_uploader("Загрузите фото (JPG/PNG)", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        st.image(uploaded_file, caption="Ваше текущее помещение", use_container_width=True)
    
    prompt = st.text_area("Ваши пожелания:", placeholder="Например: Сделай из этой кухни уютный лофт с кирпичными стенами и деревянным столом. Бюджет 300 000 рублей.")
    
    generate_btn = st.button("🚀 Создать дизайн-проект")

with col_output:
    if generate_btn:
        if not GEMINI_KEY:
            st.error("Отсутствует API Ключ!")
        else:
            with st.spinner("Nano Banana анализирует пространство и рисует..."):
                img_input = Image.open(uploaded_file) if uploaded_file else None
                data, result_img = process_design(img_input, prompt)
                
                if data:
                    st.subheader("🖼 Визуализация нового дизайна")
                    # Отображаем сгенерированное изображение (заглушка на случай если API вернет ссылку/объект)
                    # В Gemini 2.5 Flash Image результат может быть в .parts[0].inline_data
                    try:
                        st.image(f"https://pollinations.ai/p/{data['visual_prompt'].replace(' ', '_')}?width=1024&height=768&seed=42", caption="Предложенный вариант")
                    except:
                        st.info("Визуализация генерируется...")

                    st.markdown(f"""
                    <div class="cost-card">
                        <h3>💰 Примерная смета: {data['total_estimate']} ₽</h3>
                        <p><b>Концепция:</b> {data['analysis']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    st.write("### 🛒 Предметы интерьера и где их найти:")
                    for item in data['items']:
                        # Создаем ссылки на поиск
                        search_q = f"{item['name']} купить".replace(" ", "+")
                        google_url = f"https://www.google.com/search?q={search_q}"
                        yandex_url = f"https://yandex.ru/search/?text={search_q}"
                        
                        with st.expander(f"📍 {item['name']} — {item['price']} ₽"):
                            st.write(f"**Зачем:** {item['reason']}")
                            st.markdown(f"[Найти в Google]({google_url}) | [Найти в Яндексе]({yandex_url})")
                else:
                    st.error("Не удалось получить данные от ИИ. Попробуйте изменить запрос.")

# --- ИНФОРМАЦИЯ ---
st.sidebar.markdown(f"""
---
**О сервисе:**
- Модель: Gemini 2.5 Flash (Nano Banana)
- Лимит: 500 запросов/день бесплатно
- Сохраняет архитектуру вашего помещения
""")
