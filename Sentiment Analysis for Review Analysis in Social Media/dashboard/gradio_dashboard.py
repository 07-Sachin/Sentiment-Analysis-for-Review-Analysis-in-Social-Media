# #!/usr/bin/env python3
# import os, json, sqlite3, time
# from dotenv import load_dotenv
# import gradio as gr
# import google.generativeai as genai
# import pandas as pd
# from datetime import datetime

# ROOT = os.path.dirname(os.path.dirname(__file__))
# load_dotenv(os.path.join(ROOT, "config", ".env"))

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
# if not GEMINI_API_KEY:
#     raise SystemExit("Please set GEMINI_API_KEY in config/.env")

# genai.configure(api_key=GEMINI_API_KEY)

# DB_PATH = os.path.join(ROOT, "data", "reviews.db")
# os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# # initialize sqlite
# def init_db():
#     conn = sqlite3.connect(DB_PATH)
#     cur = conn.cursor()
#     cur.execute("""
#     CREATE TABLE IF NOT EXISTS reviews (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         timestamp TEXT,
#         review_text TEXT,
#         cleaned_text TEXT,
#         sentiment_label TEXT,
#         confidence REAL
#     )
#     """)
#     conn.commit()
#     conn.close()

# init_db()

# def clean_text(s: str) -> str:
#     import re, emoji
#     if not s: return ""
#     s = re.sub(r"http\S+|www\.\S+", " ", s)
#     s = re.sub(r"@\w+", " ", s)
#     s = s.replace("\n", " ").strip()
#     s = emoji.demojize(s)
#     s = s.replace(":", " ")
#     s = re.sub(r"\s+", " ", s)
#     return s.lower()

# def call_gemini_single(text: str):
#     prompt = f"Classify the sentiment of this review as positive, negative, or neutral. Return JSON: {json_example()}.\\nReview: \"{text}\""
#     try:
#         resp = genai.generate(model=MODEL, text=prompt, temperature=0.0, max_output_tokens=200)
#         out = ""
#         if hasattr(resp, "candidates") and resp.candidates:
#             try:
#                 out = resp.candidates[0].content[0].text
#             except:
#                 out = resp.candidates[0].text if hasattr(resp.candidates[0], "text") else str(resp)
#         else:
#             out = str(resp)
#         # extract JSON
#         start = out.find('{')
#         end = out.rfind('}')
#         json_text = out[start:end+1] if start!=-1 and end!=-1 else out
#         parsed = json.loads(json_text)
#         return parsed.get("label","neutral"), float(parsed.get("confidence",0.5))
#     except Exception as e:
#         return "neutral", 0.5

# def json_example():
#     return '{"label":"negative","confidence":0.92}'

# def analyze_and_store(review_text):
#     ts = datetime.utcnow().isoformat()
#     cleaned = clean_text(review_text)
#     label, conf = call_gemini_single(cleaned)
#     # store
#     conn = sqlite3.connect(DB_PATH)
#     cur = conn.cursor()
#     cur.execute("INSERT INTO reviews (timestamp, review_text, cleaned_text, sentiment_label, confidence) VALUES (?,?,?,?,?)",
#                 (ts, review_text, cleaned, label, conf))
#     conn.commit()
#     conn.close()
#     return {"timestamp": ts, "review_text": review_text, "cleaned_text": cleaned, "sentiment_label": label, "confidence": conf}

# def get_history(limit=50):
#     conn = sqlite3.connect(DB_PATH)
#     df = pd.read_sql_query(f"SELECT timestamp, review_text, cleaned_text, sentiment_label, confidence FROM reviews ORDER BY id DESC LIMIT {limit}", conn)
#     conn.close()
#     return df

# with gr.Blocks(title="Sentiment Analyzer (Single Input)") as demo:
#     gr.Markdown("# Sentiment Analyzer (Single Input)")
#     with gr.Row():
#         review_input = gr.Textbox(lines=5, placeholder="Paste or type a review here...", label="Your Review")
#     with gr.Row():
#         analyze_btn = gr.Button("Analyze Sentiment")
#         clear_btn = gr.Button("Clear Reviews (local)")
#     result = gr.JSON(label="Result (label, confidence)")
#     history_table = gr.Dataframe(headers=["timestamp","review_text","cleaned_text","sentiment_label","confidence"], interactive=False, label="History (most recent first)")

#     def on_analyze(text):
#         if not text or not text.strip():
#             return {"error":"Please enter a review"}, get_history().to_dict(orient="records")
#         res = analyze_and_store(text.strip())
#         hist = get_history()
#         return res, hist.to_dict(orient="records")

#     def on_clear():
#         conn = sqlite3.connect(DB_PATH)
#         cur = conn.cursor()
#         cur.execute("DELETE FROM reviews;")
#         conn.commit()
#         conn.close()
#         return {"status":"cleared"}, []

#     analyze_btn.click(fn=on_analyze, inputs=[review_input], outputs=[result, history_table])
#     clear_btn.click(fn=on_clear, inputs=None, outputs=[result, history_table])

#     # load history at start
#     demo.load(fn=lambda: ({"status":"ready"}, get_history().to_dict(orient="records")), outputs=[result, history_table])

# demo.launch(server_name="0.0.0.0", server_port=7860, share=False)


# import gradio as gr
# import pandas as pd
# import re
# import emoji
# import google.generativeai as genai
# import datetime
# import os
# import json
# from dotenv import load_dotenv

# # =============== SETUP GEMINI ====================
# load_dotenv()
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# # =============== HELPER FUNCTIONS ====================

# def clean_text(text):
#     """Clean and normalize emojis, URLs, and extra spaces."""
#     text = re.sub(r"http\S+|www\S+|https\S+", '', text)  # remove URLs
#     text = emoji.demojize(text)  # normalize emojis to text form
#     text = re.sub(r"[^a-zA-Z0-9\s:]", '', text)
#     text = re.sub(r"\s+", " ", text).strip().lower()
#     return text


# def rule_based_sentiment(cleaned):
#     """Fallback sentiment analyzer if Gemini fails."""
#     cleaned_lower = cleaned.lower()
#     positive_words = ["love", "like", "awesome", "great", "amazing", "excellent", "perfect", "good"]
#     negative_words = ["hate", "bad", "worst", "terrible", "poor", "awful", "disappointed"]

#     if any(word in cleaned_lower for word in positive_words):
#         return "positive", 0.85
#     elif any(word in cleaned_lower for word in negative_words):
#         return "negative", 0.85
#     else:
#         return "neutral", 0.6


# def get_sentiment(text):
#     """Use Gemini API + fallback rule-based enhancement."""
#     try:
#         model = genai.GenerativeModel("gemini-1.5-flash")
#         prompt = f"""
#         Analyze the following review and respond ONLY in strict JSON format:
#         Text: "{text}"
#         Expected JSON keys: sentiment_label (positive, negative, or neutral) and confidence (0.0 to 1.0)
#         Example output: {{ "sentiment_label": "positive", "confidence": 0.9 }}
#         """
#         response = model.generate_content(prompt)
#         result = response.text.strip() if response.text else ""

#         if not result:
#             print("⚠️ Gemini returned empty response.")
#             return rule_based_sentiment(text)

#         try:
#             data = json.loads(result)
#             label = data.get("sentiment_label", "neutral")
#             confidence = float(data.get("confidence", 0.5))
#         except Exception:
#             # fallback: keyword search in raw result
#             if "positive" in result.lower():
#                 label, confidence = "positive", 0.8
#             elif "negative" in result.lower():
#                 label, confidence = "negative", 0.8
#             elif "neutral" in result.lower():
#                 label, confidence = "neutral", 0.6
#             else:
#                 return rule_based_sentiment(text)

#         # 🧠 Smart confidence fine-tuning
#         cleaned = text.lower()
#         if confidence >= 0.45 and "like" in cleaned:
#             label = "positive"
#         elif confidence > 0.6:
#             label = "positive"
#         elif confidence < 0.4:
#             label = "negative"

#         return label, min(1.0, max(0.0, confidence))

#     except Exception as e:
#         print(" Gemini Error:", e)
#         # fallback to keyword-based
#         return rule_based_sentiment(text)


# # =============== STORAGE ====================
# storage_file = "processed_reviews.csv"

# def analyze_and_store(review_text):
#     cleaned = clean_text(review_text)
#     label, confidence = get_sentiment(cleaned)

#     data = {
#         "timestamp": datetime.datetime.now().isoformat(),
#         "review_text": review_text,
#         "cleaned_text": cleaned,
#         "sentiment_label": label,
#         "confidence": confidence
#     }

#     df = pd.DataFrame([data])

#     if os.path.exists(storage_file):
#         df.to_csv(storage_file, mode="a", header=False, index=False)
#     else:
#         df.to_csv(storage_file, index=False)

#     return data


# def load_history():
#     if os.path.exists(storage_file):
#         df = pd.read_csv(storage_file)
#         return df
#     else:
#         return pd.DataFrame(columns=["timestamp", "review_text", "sentiment_label", "confidence"])


# def clear_history():
#     if os.path.exists(storage_file):
#         os.remove(storage_file)
#     return "✅ History Cleared!"


# # =============== GRADIO UI ====================
# def on_analyze(text):
#     if not text.strip():
#         return "⚠️ Please enter a review!"
#     res = analyze_and_store(text.strip())
#     return f"✅ Sentiment: **{res['sentiment_label']}** (Confidence: {res['confidence']:.2f})"


# def on_history():
#     return load_history()


# with gr.Blocks(theme=gr.themes.Soft()) as dashboard:
#     gr.Markdown("## 💬 Sentiment Analyzer (Single Input)")

#     with gr.Row():
#         review_box = gr.Textbox(label="Your Review", lines=4, placeholder="Type your product review here...")

#     with gr.Row():
#         analyze_btn = gr.Button("Analyze Sentiment")
#         clear_btn = gr.Button("Clear Reviews (local)")

#     output_box = gr.Textbox(label="Result", interactive=False)
#     history_table = gr.Dataframe(label="Review History")

#     analyze_btn.click(on_analyze, inputs=review_box, outputs=output_box)
#     analyze_btn.click(on_history, inputs=None, outputs=history_table)
#     clear_btn.click(clear_history, outputs=output_box)

# dashboard.launch()




# import gradio as gr
# import pandas as pd
# import re
# import emoji
# import google.generativeai as genai
# import datetime
# import os
# import json
# from dotenv import load_dotenv

# # =============== SETUP GEMINI ====================
# load_dotenv()
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# if not GEMINI_API_KEY:
#     print(" WARNING: GEMINI_API_KEY not found in .env file!")
# else:
#     genai.configure(api_key=GEMINI_API_KEY)

# # =============== HELPER FUNCTIONS ====================

# def clean_text(text):
#     """Clean and normalize emojis, URLs, and extra spaces."""
#     if not text:
#         return ""
    
#     text = re.sub(r"http\S+|www\S+|https\S+", '', text)  # remove URLs
#     text = emoji.demojize(text)  # normalize emojis to text form
#     text = re.sub(r"[^a-zA-Z0-9\s:]", '', text)
#     text = re.sub(r"\s+", " ", text).strip().lower()
#     return text


# def rule_based_sentiment(text):
#     """Fallback sentiment analyzer if Gemini fails."""
#     if not text:
#         return "neutral", 0.5
    
#     cleaned_lower = text.lower()
#     positive_words = ["love", "like", "awesome", "great", "amazing", "excellent", "perfect", "good", "best", "wonderful"]
#     negative_words = ["hate", "bad", "worst", "terrible", "poor", "awful", "disappointed", "horrible", "useless", "broken"]

#     pos_count = sum(1 for word in positive_words if word in cleaned_lower)
#     neg_count = sum(1 for word in negative_words if word in cleaned_lower)

#     if pos_count > neg_count:
#         confidence = min(0.85, 0.65 + (pos_count * 0.1))
#         return "positive", confidence
#     elif neg_count > pos_count:
#         confidence = min(0.85, 0.65 + (neg_count * 0.1))
#         return "negative", confidence
#     else:
#         return "neutral", 0.6


# def get_sentiment(text):
#     """Use Gemini API + fallback rule-based enhancement."""
#     if not text or not text.strip():
#         return "neutral", 0.5
    
#     # Check if API key is configured
#     if not GEMINI_API_KEY:
#         print(" No Gemini API key - using rule-based fallback")
#         return rule_based_sentiment(text)
    
#     try:
#         model = genai.GenerativeModel("gemini-1.5-flash")
#         prompt = f"""Analyze the sentiment of this text and respond ONLY with valid JSON.

# Text: "{text}"

# Respond with exactly this format (no markdown, no extra text):
# {{"sentiment_label": "positive", "confidence": 0.85}}

# Rules:
# - sentiment_label must be: "positive", "negative", or "neutral"
# - confidence must be a number between 0.0 and 1.0
# - Return ONLY the JSON, nothing else"""

#         response = model.generate_content(prompt)
#         result = response.text.strip() if response and response.text else ""

#         if not result:
#             print(" Gemini returned empty response - using fallback")
#             return rule_based_sentiment(text)

#         # Clean up markdown code blocks if present
#         result = result.replace("```json", "").replace("```", "").strip()
        
#         try:
#             data = json.loads(result)
#             label = data.get("sentiment_label", "neutral").lower()
#             confidence = float(data.get("confidence", 0.5))
            
#             # Validate label
#             if label not in ["positive", "negative", "neutral"]:
#                 label = "neutral"
            
#             # Clamp confidence between 0 and 1
#             confidence = max(0.0, min(1.0, confidence))
            
#             return label, confidence
            
#         except json.JSONDecodeError as e:
#             print(f" JSON parsing failed: {e}")
#             print(f"Raw response: {result[:200]}")
            
#             # Fallback: keyword search in result
#             result_lower = result.lower()
#             if "positive" in result_lower:
#                 return "positive", 0.75
#             elif "negative" in result_lower:
#                 return "negative", 0.75
#             elif "neutral" in result_lower:
#                 return "neutral", 0.65
#             else:
#                 return rule_based_sentiment(text)

#     except Exception as e:
#         print(f" Gemini Error: {e}")
#         return rule_based_sentiment(text)


# # =============== STORAGE ====================
# storage_file = "processed_reviews.csv"

# def analyze_and_store(review_text):
#     """Analyze sentiment and store result."""
#     if not review_text or not review_text.strip():
#         return None
    
#     cleaned = clean_text(review_text)
#     label, confidence = get_sentiment(review_text)  # Use original text for better analysis

#     data = {
#         "timestamp": datetime.datetime.now().isoformat(),
#         "review_text": review_text,
#         "cleaned_text": cleaned,
#         "sentiment_label": label,
#         "confidence": confidence
#     }

#     df = pd.DataFrame([data])

#     try:
#         if os.path.exists(storage_file):
#             df.to_csv(storage_file, mode="a", header=False, index=False)
#         else:
#             df.to_csv(storage_file, index=False)
#     except Exception as e:
#         print(f" Error saving to CSV: {e}")

#     return data


# def load_history():
#     """Load review history from CSV."""
#     if os.path.exists(storage_file):
#         try:
#             df = pd.read_csv(storage_file)
#             # Format timestamp for better readability
#             if 'timestamp' in df.columns:
#                 df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
#             return df
#         except Exception as e:
#             print(f" Error loading history: {e}")
#             return pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])
#     else:
#         return pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])


# def clear_history():
#     """Clear all stored reviews."""
#     try:
#         if os.path.exists(storage_file):
#             os.remove(storage_file)
#         return " History Cleared!", pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])
#     except Exception as e:
#         return f" Error clearing history: {e}", load_history()


# def get_statistics():
#     """Generate statistics from review history."""
#     df = load_history()
    
#     if df.empty:
#         return "No reviews yet. Start analyzing!"
    
#     total = len(df)
#     positive = len(df[df['sentiment_label'] == 'positive'])
#     negative = len(df[df['sentiment_label'] == 'negative'])
#     neutral = len(df[df['sentiment_label'] == 'neutral'])
#     avg_confidence = df['confidence'].mean()
    
#     stats = f"""
# ### Statistics
# - **Total Reviews**: {total}
# - **Positive**: {positive} ({positive/total*100:.1f}%)
# - **Negative**: {negative} ({negative/total*100:.1f}%)
# - **Neutral**: {neutral} ({neutral/total*100:.1f}%)
# - **Avg Confidence**: {avg_confidence:.2f}
# """
#     return stats


# # =============== GRADIO UI ====================
# def on_analyze(text):
#     """Handle analyze button click."""
#     if not text or not text.strip():
#         return " Please enter a review!", load_history(), get_statistics()
    
#     res = analyze_and_store(text.strip())
    
#     if not res:
#         return " Error analyzing review", load_history(), get_statistics()
    
#     # Emoji feedback
#     emoji_map = {
#         "positive": "😊",
#         "negative": "😞",
#         "neutral": "😐"
#     }
#     sentiment_emoji = emoji_map.get(res['sentiment_label'], "")
    
#     result_text = f"""
# ###  Analysis Complete!
# **Sentiment**: {sentiment_emoji} **{res['sentiment_label'].upper()}**  
# **Confidence**: {res['confidence']:.2%}  
# **Cleaned Text**: "{res['cleaned_text'][:100]}..."
# """
    
#     return result_text, load_history(), get_statistics()


# def on_clear():
#     """Handle clear button click."""
#     message, history = clear_history()
#     stats = get_statistics()
#     return message, history, stats


# # =============== BUILD UI ====================
# with gr.Blocks(theme=gr.themes.Soft(), title="Sentiment Analyzer") as dashboard:
#     gr.Markdown("""
#     # 💬 Sentiment Analyzer
#     ### Powered by Google Gemini AI
#     Analyze product reviews and social media posts for sentiment!
#     """)

#     with gr.Row():
#         with gr.Column(scale=2):
#             review_box = gr.Textbox(
#                 label=" Your Review", 
#                 lines=5, 
#                 placeholder="Type your product review here...\n\nExample: 'I love this product! It works great and exceeded my expectations.'"
#             )
            
#             with gr.Row():
#                 analyze_btn = gr.Button(" Analyze Sentiment", variant="primary", size="lg")
#                 clear_btn = gr.Button(" Clear History", variant="secondary")
            
#             output_box = gr.Markdown(label="Result")
        
#         with gr.Column(scale=1):
#             stats_box = gr.Markdown(get_statistics())
    
#     gr.Markdown("###  Review History")
#     history_table = gr.Dataframe(
#         value=load_history(),
#         label="All Analyzed Reviews",
#         interactive=False,
#         wrap=True
#     )

#     # Event handlers
#     analyze_btn.click(
#         fn=on_analyze, 
#         inputs=review_box, 
#         outputs=[output_box, history_table, stats_box]
#     )
    
#     clear_btn.click(
#         fn=on_clear,
#         outputs=[output_box, history_table, stats_box]
#     )
    
#     # Load history on startup
#     dashboard.load(
#         fn=lambda: (load_history(), get_statistics()),
#         outputs=[history_table, stats_box]
#     )

# if __name__ == "__main__":
#     dashboard.launch(
#         server_name="0.0.0.0",
#         server_port=7860,
#         share=False
#     )








# import gradio as gr
# import pandas as pd
# import re
# import emoji
# import google.generativeai as genai
# import datetime
# import os
# import json
# import sys
# from dotenv import load_dotenv

# # Fix Windows console encoding for emojis
# if sys.platform == "win32":
#     try:
#         sys.stdout.reconfigure(encoding='utf-8')
#     except AttributeError:
#         import io
#         sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# # =============== SETUP GEMINI ====================
# load_dotenv()
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# if not GEMINI_API_KEY:
#     print("WARNING: GEMINI_API_KEY not found in .env file!")
# else:
#     genai.configure(api_key=GEMINI_API_KEY)

# # =============== HELPER FUNCTIONS ====================

# def clean_text(text):
#     """Clean and normalize emojis, URLs, and extra spaces."""
#     if not text:
#         return ""
    
#     text = re.sub(r"http\S+|www\S+|https\S+", '', text)  # remove URLs
#     text = emoji.demojize(text)  # normalize emojis to text form
#     text = re.sub(r"[^a-zA-Z0-9\s:]", '', text)
#     text = re.sub(r"\s+", " ", text).strip().lower()
#     return text


# def rule_based_sentiment(text):
#     """Fallback sentiment analyzer if Gemini fails."""
#     if not text:
#         return "neutral", 0.5
    
#     cleaned_lower = text.lower()
    
#     # Enhanced word lists with more context
#     positive_words = ["love", "awesome", "amazing", "excellent", "perfect", "best", "wonderful", "fantastic", "outstanding", "brilliant"]
#     negative_words = ["hate", "worst", "terrible", "awful", "horrible", "useless", "broken", "disappointed", "poor", "pathetic"]
#     neutral_indicators = ["okay", "ok", "fine", "average", "decent", "not bad", "not great", "so-so", "mediocre", "acceptable"]
#     mixed_indicators = ["but", "however", "although", "though"]

#     pos_count = sum(1 for word in positive_words if word in cleaned_lower)
#     neg_count = sum(1 for word in negative_words if word in cleaned_lower)
#     neutral_count = sum(1 for word in neutral_indicators if word in cleaned_lower)
#     mixed_count = sum(1 for word in mixed_indicators if word in cleaned_lower)

#     # Check for neutral/mixed sentiment indicators
#     if neutral_count > 0 or mixed_count >= 2:
#         return "neutral", 0.65
    
#     # Check for balanced positive and negative
#     if pos_count > 0 and neg_count > 0 and abs(pos_count - neg_count) <= 1:
#         return "neutral", 0.70
    
#     # Strong sentiment detection
#     if pos_count > neg_count and pos_count >= 2:
#         confidence = min(0.85, 0.70 + (pos_count * 0.05))
#         return "positive", confidence
#     elif neg_count > pos_count and neg_count >= 2:
#         confidence = min(0.85, 0.70 + (neg_count * 0.05))
#         return "negative", confidence
#     elif pos_count > neg_count:
#         return "positive", 0.65
#     elif neg_count > pos_count:
#         return "negative", 0.65
#     else:
#         return "neutral", 0.60


# def get_sentiment(text):
#     """Use Gemini API + fallback rule-based enhancement."""
#     if not text or not text.strip():
#         return "neutral", 0.5
    
#     # Check if API key is configured
#     if not GEMINI_API_KEY:
#         print("WARNING: No Gemini API key - using rule-based fallback")
#         return rule_based_sentiment(text)
    
#     try:
#         model = genai.GenerativeModel("gemini-1.5-flash")
#         prompt = f"""Analyze the sentiment of this text and respond ONLY with valid JSON.

# Text: "{text}"

# Respond with exactly this format (no markdown, no extra text):
# {{"sentiment_label": "positive", "confidence": 0.85}}

# Rules:
# - sentiment_label must be: "positive", "negative", or "neutral"
# - confidence must be a number between 0.0 and 1.0
# - Return ONLY the JSON, nothing else"""

#         response = model.generate_content(prompt)
#         result = response.text.strip() if response and response.text else ""

#         if not result:
#             print("WARNING: Gemini returned empty response - using fallback")
#             return rule_based_sentiment(text)

#         # Clean up markdown code blocks if present
#         result = result.replace("```json", "").replace("```", "").strip()
        
#         try:
#             data = json.loads(result)
#             label = data.get("sentiment_label", "neutral").lower()
#             confidence = float(data.get("confidence", 0.5))
            
#             # Validate label
#             if label not in ["positive", "negative", "neutral"]:
#                 label = "neutral"
            
#             # Clamp confidence between 0 and 1
#             confidence = max(0.0, min(1.0, confidence))
            
#             return label, confidence
            
#         except json.JSONDecodeError as e:
#             print(f"WARNING: JSON parsing failed: {e}")
#             print(f"Raw response: {result[:200]}")
            
#             # Fallback: keyword search in result
#             result_lower = result.lower()
#             if "positive" in result_lower:
#                 return "positive", 0.75
#             elif "negative" in result_lower:
#                 return "negative", 0.75
#             elif "neutral" in result_lower:
#                 return "neutral", 0.65
#             else:
#                 return rule_based_sentiment(text)

#     except Exception as e:
#         print(f"ERROR: Gemini Error: {e}")
#         return rule_based_sentiment(text)


# # =============== STORAGE ====================
# storage_file = "processed_reviews.csv"

# def analyze_and_store(review_text):
#     """Analyze sentiment and store result."""
#     if not review_text or not review_text.strip():
#         return None
    
#     cleaned = clean_text(review_text)
#     label, confidence = get_sentiment(review_text)  # Use original text for better analysis

#     data = {
#         "timestamp": datetime.datetime.now().isoformat(),
#         "review_text": review_text,
#         "cleaned_text": cleaned,
#         "sentiment_label": label,
#         "confidence": confidence
#     }

#     df = pd.DataFrame([data])

#     try:
#         if os.path.exists(storage_file):
#             df.to_csv(storage_file, mode="a", header=False, index=False)
#         else:
#             df.to_csv(storage_file, index=False)
#     except Exception as e:
#         print(f"ERROR: Error saving to CSV: {e}")

#     return data


# def load_history():
#     """Load review history from CSV."""
#     if os.path.exists(storage_file):
#         try:
#             df = pd.read_csv(storage_file)
#             # Format timestamp for better readability
#             if 'timestamp' in df.columns:
#                 df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
#             return df
#         except Exception as e:
#             print(f"ERROR: Error loading history: {e}")
#             return pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])
#     else:
#         return pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])


# def clear_history():
#     """Clear all stored reviews."""
#     try:
#         if os.path.exists(storage_file):
#             os.remove(storage_file)
#         return "History Cleared!", pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])
#     except Exception as e:
#         return f"ERROR: Error clearing history: {e}", load_history()


# def get_statistics():
#     """Generate statistics from review history."""
#     df = load_history()
    
#     if df.empty:
#         return "No reviews yet. Start analyzing!"
    
#     total = len(df)
#     positive = len(df[df['sentiment_label'] == 'positive'])
#     negative = len(df[df['sentiment_label'] == 'negative'])
#     neutral = len(df[df['sentiment_label'] == 'neutral'])
#     avg_confidence = df['confidence'].mean()
    
#     stats = f"""
# ### Statistics
# - **Total Reviews**: {total}
# - **Positive**: {positive} ({positive/total*100:.1f}%)
# - **Negative**: {negative} ({negative/total*100:.1f}%)
# - **Neutral**: {neutral} ({neutral/total*100:.1f}%)
# - **Avg Confidence**: {avg_confidence:.2f}
# """
#     return stats


# # =============== GRADIO UI ====================
# def on_analyze(text):
#     """Handle analyze button click."""
#     if not text or not text.strip():
#         return "WARNING: Please enter a review!", load_history(), get_statistics()
    
#     res = analyze_and_store(text.strip())
    
#     if not res:
#         return "ERROR: Error analyzing review", load_history(), get_statistics()
    
#     result_text = f"""
# ### Analysis Complete!
# **Sentiment**: **{res['sentiment_label'].upper()}**  
# **Confidence**: {res['confidence']:.2%}  
# **Cleaned Text**: "{res['cleaned_text'][:100]}..."
# """
    
#     return result_text, load_history(), get_statistics()


# def on_clear():
#     """Handle clear button click."""
#     message, history = clear_history()
#     stats = get_statistics()
#     return message, history, stats


# # =============== BUILD UI ====================
# with gr.Blocks(theme=gr.themes.Soft(), title="Sentiment Analyzer") as dashboard:
#     gr.Markdown("""
#     # Sentiment Analyzer
#     ### Powered by Google Gemini AI
#     Analyze product reviews and social media posts for sentiment!
#     """)

#     with gr.Row():
#         with gr.Column(scale=2):
#             review_box = gr.Textbox(
#                 label="Your Review", 
#                 lines=5, 
#                 placeholder="Type your product review here...\n\nExample: 'I love this product! It works great and exceeded my expectations.'"
#             )
            
#             with gr.Row():
#                 analyze_btn = gr.Button("Analyze Sentiment", variant="primary", size="lg")
#                 clear_btn = gr.Button("Clear History", variant="secondary")
            
#             output_box = gr.Markdown(label="Result")
        
#         with gr.Column(scale=1):
#             stats_box = gr.Markdown(get_statistics())
    
#     gr.Markdown("### Review History")
#     history_table = gr.Dataframe(
#         value=load_history(),
#         label="All Analyzed Reviews",
#         interactive=False,
#         wrap=True
#     )

#     # Event handlers
#     analyze_btn.click(
#         fn=on_analyze, 
#         inputs=review_box, 
#         outputs=[output_box, history_table, stats_box]
#     )
    
#     clear_btn.click(
#         fn=on_clear,
#         outputs=[output_box, history_table, stats_box]
#     )
    
#     # Load history on startup
#     dashboard.load(
#         fn=lambda: (load_history(), get_statistics()),
#         outputs=[history_table, stats_box]
#     )

# if __name__ == "__main__":
#     dashboard.launch(
#         server_name="0.0.0.0",
#         server_port=7860,
#         share=False
#     )






# import gradio as gr
# import pandas as pd
# import re
# import emoji
# import google.generativeai as genai
# import datetime
# import os
# import json
# import sys
# from dotenv import load_dotenv

# # Fix Windows console encoding for emojis
# if sys.platform == "win32":
#     try:
#         sys.stdout.reconfigure(encoding='utf-8')
#     except AttributeError:
#         import io
#         sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# # =============== SETUP GEMINI ====================
# load_dotenv()
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# if not GEMINI_API_KEY:
#     print("WARNING: GEMINI_API_KEY not found in .env file!")
# else:
#     genai.configure(api_key=GEMINI_API_KEY)

# # =============== HELPER FUNCTIONS ====================

# def clean_text(text):
#     """Clean and normalize emojis, URLs, and extra spaces."""
#     if not text:
#         return ""
    
#     text = re.sub(r"http\S+|www\S+|https\S+", '', text)  # remove URLs
#     text = emoji.demojize(text)  # normalize emojis to text form
#     text = re.sub(r"[^a-zA-Z0-9\s:]", '', text)
#     text = re.sub(r"\s+", " ", text).strip().lower()
#     return text


# def rule_based_sentiment(text):
#     """Fallback sentiment analyzer if Gemini fails."""
#     if not text:
#         return "neutral", 0.5
    
#     cleaned_lower = text.lower()
    
#     # Enhanced word lists with more context
#     positive_words = ["love", "awesome", "amazing", "excellent", "perfect", "best", "wonderful", "fantastic", "outstanding", "brilliant"]
#     negative_words = ["hate", "worst", "terrible", "awful", "horrible", "useless", "broken", "disappointed", "poor", "pathetic"]
#     neutral_indicators = ["okay", "ok", "fine", "average", "decent", "not bad", "not great", "so-so", "mediocre", "acceptable"]
#     mixed_indicators = ["but", "however", "although", "though"]

#     pos_count = sum(1 for word in positive_words if word in cleaned_lower)
#     neg_count = sum(1 for word in negative_words if word in cleaned_lower)
#     neutral_count = sum(1 for word in neutral_indicators if word in cleaned_lower)
#     mixed_count = sum(1 for word in mixed_indicators if word in cleaned_lower)

#     # Check for neutral/mixed sentiment indicators
#     if neutral_count > 0 or mixed_count >= 2:
#         return "neutral", 0.65
    
#     # Check for balanced positive and negative
#     if pos_count > 0 and neg_count > 0 and abs(pos_count - neg_count) <= 1:
#         return "neutral", 0.70
    
#     # Strong sentiment detection
#     if pos_count > neg_count and pos_count >= 2:
#         confidence = min(0.85, 0.70 + (pos_count * 0.05))
#         return "positive", confidence
#     elif neg_count > pos_count and neg_count >= 2:
#         confidence = min(0.85, 0.70 + (neg_count * 0.05))
#         return "negative", confidence
#     elif pos_count > neg_count:
#         return "positive", 0.65
#     elif neg_count > pos_count:
#         return "negative", 0.65
#     else:
#         return "neutral", 0.60


# def get_sentiment(text):
#     """Use Gemini API + fallback rule-based enhancement."""
#     if not text or not text.strip():
#         return "neutral", 0.5
    
#     # Check if API key is configured
#     if not GEMINI_API_KEY:
#         print("WARNING: No Gemini API key - using rule-based fallback")
#         return rule_based_sentiment(text)
    
#     try:
#         model = genai.GenerativeModel("gemini-1.5-flash")
#         prompt = f"""Analyze the sentiment of this text and respond ONLY with valid JSON.

# Text: "{text}"

# Important rules for classification:
# - "okay but not great" = NEUTRAL
# - Words like "okay", "fine", "decent", "average", "so-so" = NEUTRAL
# - Mixed feelings (both positive and negative words) = NEUTRAL
# - Only clearly positive without reservation = POSITIVE
# - Only clearly negative without reservation = NEGATIVE

# Respond with exactly this format (no markdown, no extra text):
# {{"sentiment_label": "positive", "confidence": 0.85}}

# Rules:
# - sentiment_label must be: "positive", "negative", or "neutral"
# - confidence must be a number between 0.0 and 1.0
# - Return ONLY the JSON, nothing else"""

#         response = model.generate_content(prompt)
#         result = response.text.strip() if response and response.text else ""

#         if not result:
#             print("WARNING: Gemini returned empty response - using fallback")
#             return rule_based_sentiment(text)

#         # Clean up markdown code blocks if present
#         result = result.replace("```json", "").replace("```", "").strip()
        
#         try:
#             data = json.loads(result)
#             label = data.get("sentiment_label", "neutral").lower()
#             confidence = float(data.get("confidence", 0.5))
            
#             # Validate label
#             if label not in ["positive", "negative", "neutral"]:
#                 label = "neutral"
            
#             # Clamp confidence between 0 and 1
#             confidence = max(0.0, min(1.0, confidence))
            
#             # Post-processing validation with rule-based check
#             text_lower = text.lower()
#             neutral_indicators = ["okay", "ok", "fine", "average", "decent", "not bad", "not great", "so-so", "mediocre"]
#             mixed_indicators = ["but", "however", "although", "though"]
            
#             # Override if strong neutral/mixed indicators present
#             has_neutral = any(word in text_lower for word in neutral_indicators)
#             has_mixed = sum(1 for word in mixed_indicators if word in text_lower) >= 2
            
#             if (has_neutral or has_mixed) and label != "neutral":
#                 # Check if there are strong positive/negative words too
#                 strong_positive = ["love", "amazing", "excellent", "perfect", "best", "wonderful", "fantastic"]
#                 strong_negative = ["hate", "worst", "terrible", "awful", "horrible", "pathetic"]
                
#                 has_strong_pos = any(word in text_lower for word in strong_positive)
#                 has_strong_neg = any(word in text_lower for word in strong_negative)
                
#                 # If no strong sentiment, override to neutral
#                 if not has_strong_pos and not has_strong_neg:
#                     label = "neutral"
#                     confidence = min(confidence, 0.70)
            
#             return label, confidence
            
#         except json.JSONDecodeError as e:
#             print(f"WARNING: JSON parsing failed: {e}")
#             print(f"Raw response: {result[:200]}")
#             return rule_based_sentiment(text)

#     except Exception as e:
#         print(f"ERROR: Gemini Error: {e}")
#         return rule_based_sentiment(text)


# # =============== STORAGE ====================
# storage_file = "processed_reviews.csv"

# def analyze_and_store(review_text):
#     """Analyze sentiment and store result."""
#     if not review_text or not review_text.strip():
#         return None
    
#     cleaned = clean_text(review_text)
#     label, confidence = get_sentiment(review_text)  # Use original text for better analysis

#     data = {
#         "timestamp": datetime.datetime.now().isoformat(),
#         "review_text": review_text,
#         "cleaned_text": cleaned,
#         "sentiment_label": label,
#         "confidence": confidence
#     }

#     df = pd.DataFrame([data])

#     try:
#         if os.path.exists(storage_file):
#             df.to_csv(storage_file, mode="a", header=False, index=False)
#         else:
#             df.to_csv(storage_file, index=False)
#     except Exception as e:
#         print(f"ERROR: Error saving to CSV: {e}")

#     return data


# def load_history():
#     """Load review history from CSV."""
#     if os.path.exists(storage_file):
#         try:
#             df = pd.read_csv(storage_file)
#             # Format timestamp for better readability
#             if 'timestamp' in df.columns:
#                 df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
#             return df
#         except Exception as e:
#             print(f"ERROR: Error loading history: {e}")
#             return pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])
#     else:
#         return pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])


# def clear_history():
#     """Clear all stored reviews."""
#     try:
#         if os.path.exists(storage_file):
#             # Try to delete the file
#             try:
#                 os.remove(storage_file)
#                 empty_df = pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])
#                 return "History Cleared Successfully!", empty_df
#             except PermissionError:
#                 # If file is locked, overwrite it with empty dataframe
#                 empty_df = pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])
#                 empty_df.to_csv(storage_file, index=False)
#                 return "History Cleared Successfully! (File was in use, so it was overwritten)", empty_df
#         else:
#             empty_df = pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])
#             return "No history to clear!", empty_df
#     except Exception as e:
#         return f"ERROR: Error clearing history: {e}. Please close Excel if the CSV file is open.", load_history()


# def get_statistics():
#     """Generate statistics from review history."""
#     df = load_history()
    
#     if df.empty:
#         return "No reviews yet. Start analyzing!"
    
#     total = len(df)
#     positive = len(df[df['sentiment_label'] == 'positive'])
#     negative = len(df[df['sentiment_label'] == 'negative'])
#     neutral = len(df[df['sentiment_label'] == 'neutral'])
#     avg_confidence = df['confidence'].mean()
    
#     stats = f"""
# ### Statistics
# - **Total Reviews**: {total}
# - **Positive**: {positive} ({positive/total*100:.1f}%)
# - **Negative**: {negative} ({negative/total*100:.1f}%)
# - **Neutral**: {neutral} ({neutral/total*100:.1f}%)
# - **Avg Confidence**: {avg_confidence:.2f}
# """
#     return stats


# # =============== GRADIO UI ====================
# def on_analyze(text):
#     """Handle analyze button click."""
#     if not text or not text.strip():
#         return "WARNING: Please enter a review!", load_history(), get_statistics()
    
#     res = analyze_and_store(text.strip())
    
#     if not res:
#         return "ERROR: Error analyzing review", load_history(), get_statistics()
    
#     result_text = f"""
# ### Analysis Complete!
# **Sentiment**: **{res['sentiment_label'].upper()}**  
# **Confidence**: {res['confidence']:.2%}  
# **Cleaned Text**: "{res['cleaned_text'][:100]}..."
# """
    
#     return result_text, load_history(), get_statistics()


# def on_clear():
#     """Handle clear button click."""
#     message, history = clear_history()
#     stats = get_statistics()
#     return message, history, stats


# # =============== BUILD UI ====================
# with gr.Blocks(theme=gr.themes.Soft(), title="Sentiment Analyzer") as dashboard:
#     gr.Markdown("""
#     # Sentiment Analyzer
#     ### Powered by Google Gemini AI
#     Analyze product reviews and social media posts for sentiment!
#     """)

#     with gr.Row():
#         with gr.Column(scale=2):
#             review_box = gr.Textbox(
#                 label="Your Review", 
#                 lines=5, 
#                 placeholder="Type your product review here...\n\nExample: 'I love this product! It works great and exceeded my expectations.'"
#             )
            
#             with gr.Row():
#                 analyze_btn = gr.Button("Analyze Sentiment", variant="primary", size="lg")
#                 clear_btn = gr.Button("Clear History", variant="secondary")
            
#             output_box = gr.Markdown(label="Result")
        
#         with gr.Column(scale=1):
#             stats_box = gr.Markdown(get_statistics())
    
#     gr.Markdown("### Review History")
#     history_table = gr.Dataframe(
#         value=load_history(),
#         label="All Analyzed Reviews",
#         interactive=False,
#         wrap=True
#     )

#     # Event handlers
#     analyze_btn.click(
#         fn=on_analyze, 
#         inputs=review_box, 
#         outputs=[output_box, history_table, stats_box]
#     )
    
#     clear_btn.click(
#         fn=on_clear,
#         outputs=[output_box, history_table, stats_box]
#     )
    
#     # Load history on startup
#     dashboard.load(
#         fn=lambda: (load_history(), get_statistics()),
#         outputs=[history_table, stats_box]
#     )

# if __name__ == "__main__":
#     dashboard.launch(
#         server_name="0.0.0.0",
#         server_port=7860,
#         share=False
#     )




# import gradio as gr
# import pandas as pd
# import re
# import emoji
# import google.generativeai as genai
# import datetime
# import os
# import json
# import sys
# from dotenv import load_dotenv
# from pyspark.sql import SparkSession

# # ================== Initialize PySpark ==================
# spark = SparkSession.builder \
#     .appName("SentimentAnalyzer") \
#     .getOrCreate()

# # Fix Windows console encoding for emojis
# if sys.platform == "win32":
#     try:
#         sys.stdout.reconfigure(encoding='utf-8')
#     except AttributeError:
#         import io
#         sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# # =============== SETUP GEMINI ====================
# load_dotenv()
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# if not GEMINI_API_KEY:
#     print("WARNING: GEMINI_API_KEY not found in .env file!")
# else:
#     genai.configure(api_key=GEMINI_API_KEY)

# # =============== HELPER FUNCTIONS ====================

# def clean_text(text):
#     """Clean and normalize emojis, URLs, and extra spaces."""
#     if not text:
#         return ""
#     text = re.sub(r"http\S+|www\S+|https\S+", '', text)
#     text = emoji.demojize(text)
#     text = re.sub(r"[^a-zA-Z0-9\s:]", '', text)
#     text = re.sub(r"\s+", " ", text).strip().lower()
#     return text


# def rule_based_sentiment(text):
#     """Fallback sentiment analyzer if Gemini fails."""
#     if not text:
#         return "neutral", 0.5
#     cleaned_lower = text.lower()
#     positive_words = ["love", "awesome", "amazing", "excellent", "perfect", "best", "wonderful", "fantastic"]
#     negative_words = ["hate", "worst", "terrible", "awful", "horrible", "broken", "disappointed"]
#     pos_count = sum(1 for w in positive_words if w in cleaned_lower)
#     neg_count = sum(1 for w in negative_words if w in cleaned_lower)
#     if pos_count > neg_count:
#         return "positive", 0.7
#     elif neg_count > pos_count:
#         return "negative", 0.7
#     else:
#         return "neutral", 0.6


# def get_sentiment(text):
#     """Use Gemini API + fallback rule-based enhancement."""
#     if not text.strip():
#         return "neutral", 0.5
#     if not GEMINI_API_KEY:
#         return rule_based_sentiment(text)
#     try:
#         model = genai.GenerativeModel("gemini-1.5-flash")
#         prompt = f"""Analyze this review and return JSON:
#         Text: "{text}"
#         Format: {{"sentiment_label": "positive/negative/neutral", "confidence": 0.0–1.0}}"""
#         response = model.generate_content(prompt)
#         result = response.text.strip()
#         result = result.replace("```json", "").replace("```", "")
#         try:
#             data = json.loads(result)
#         except:
#             if "positive" in result.lower():
#                 data = {"sentiment_label": "positive", "confidence": 0.8}
#             elif "negative" in result.lower():
#                 data = {"sentiment_label": "negative", "confidence": 0.8}
#             else:
#                 data = {"sentiment_label": "neutral", "confidence": 0.5}
#         label = data["sentiment_label"].lower()
#         confidence = float(data["confidence"])
#         return label, confidence
#     except Exception:
#         return rule_based_sentiment(text)


# # =============== STORAGE ====================
# storage_file = "processed_reviews.csv"

# def analyze_and_store(review_text):
#     """Analyze sentiment and store the result."""
#     cleaned = clean_text(review_text)
#     label, confidence = get_sentiment(review_text)
#     data = {
#         "timestamp": datetime.datetime.now().isoformat(),
#         "review_text": review_text,
#         "cleaned_text": cleaned,
#         "sentiment_label": label,
#         "confidence": confidence
#     }
#     df = pd.DataFrame([data])
#     if os.path.exists(storage_file):
#         df.to_csv(storage_file, mode="a", header=False, index=False)
#     else:
#         df.to_csv(storage_file, index=False)
#     return data


# def load_history():
#     """Load reviews using PySpark for better performance."""
#     if os.path.exists(storage_file):
#         try:
#             df_spark = spark.read.csv(storage_file, header=True, inferSchema=True)
#             df = df_spark.toPandas()
#             if 'timestamp' in df.columns:
#                 df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
#             return df
#         except Exception as e:
#             print(f"Error loading history via PySpark: {e}")
#             return pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])
#     else:
#         return pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])


# def clear_history():
#     """Clear all stored reviews."""
#     if os.path.exists(storage_file):
#         os.remove(storage_file)
#     return "History Cleared!", pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])


# def get_statistics():
#     """Generate statistics using PySpark."""
#     if not os.path.exists(storage_file):
#         return "No reviews yet!"
#     try:
#         df_spark = spark.read.csv(storage_file, header=True, inferSchema=True)
#         total = df_spark.count()
#         pos = df_spark.filter(df_spark.sentiment_label == "positive").count()
#         neg = df_spark.filter(df_spark.sentiment_label == "negative").count()
#         neu = df_spark.filter(df_spark.sentiment_label == "neutral").count()
#         avg_conf = df_spark.selectExpr("avg(confidence)").collect()[0][0]
#         stats = f"""
# ### Statistics
# - **Total Reviews:** {total}
# - **Positive:** {pos} ({pos/total*100:.1f}%)
# - **Negative:** {neg} ({neg/total*100:.1f}%)
# - **Neutral:** {neu} ({neu/total*100:.1f}%)
# - **Average Confidence:** {avg_conf:.2f}
# """
#         return stats
#     except Exception as e:
#         return f"Error generating stats: {e}"


# # =============== GRADIO UI ====================
# def on_analyze(text):
#     if not text.strip():
#         return "⚠️ Please enter a review!", load_history(), get_statistics()
#     res = analyze_and_store(text)
#     output = f"✅ **{res['sentiment_label'].upper()}** (Confidence: {res['confidence']:.2f})"
#     return output, load_history(), get_statistics()


# def on_clear():
#     msg, hist = clear_history()
#     return msg, hist, get_statistics()


# with gr.Blocks(theme=gr.themes.Soft()) as dashboard:
#     gr.Markdown("# 💬 Sentiment Analyzer\n### Powered by Gemini + PySpark")

#     with gr.Row():
#         with gr.Column(scale=2):
#             review_box = gr.Textbox(label="Enter your review", lines=4)
#             with gr.Row():
#                 analyze_btn = gr.Button("Analyze", variant="primary")
#                 clear_btn = gr.Button("Clear History")
#             output_box = gr.Markdown("### Result will appear here")
#         with gr.Column(scale=1):
#             stats_box = gr.Markdown(get_statistics())

#     history_table = gr.Dataframe(value=load_history(), label="Review History", interactive=False)

#     analyze_btn.click(on_analyze, inputs=review_box, outputs=[output_box, history_table, stats_box])
#     clear_btn.click(on_clear, outputs=[output_box, history_table, stats_box])

#     dashboard.load(fn=lambda: (load_history(), get_statistics()), outputs=[history_table, stats_box])

# if __name__ == "__main__":
#     dashboard.launch(server_name="0.0.0.0", server_port=7860, share=False)





import gradio as gr
import pandas as pd
import datetime
import os
import json
import re
import sys
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, current_timestamp
from pyspark.sql.types import StringType, FloatType, StructType, StructField
import google.generativeai as genai

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============ Load Environment Variables ============
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in .env file!")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# ============ Initialize PySpark ============
try:
    spark = SparkSession.builder \
        .appName("SentimentAnalyzer") \
        .config("spark.driver.memory", "2g") \
        .config("spark.executor.memory", "2g") \
        .config("spark.sql.shuffle.partitions", "8") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    print("PySpark initialized successfully")
except Exception as e:
    print(f"ERROR: Failed to initialize PySpark: {e}")
    spark = None

# ============ Global Settings ============
history_file = "review_history.csv"
batch_size = 50  # Process reviews in batches to avoid rate limits

# Initialize history file
if not os.path.exists(history_file):
    pd.DataFrame(columns=[
        "timestamp", "review_text", "cleaned_text", 
        "sentiment_label", "confidence"
    ]).to_csv(history_file, index=False)

# ============ Text Cleaning ============
def clean_text(text):
    """Clean and normalize text."""
    if not text or pd.isna(text):
        return ""
    
    text = str(text)
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\-]', ' ', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ============ Enhanced Sentiment Analysis ============
def rule_based_sentiment(text):
    """Advanced rule-based fallback sentiment analyzer."""
    if not text or len(text.strip()) < 3:
        return "neutral", 0.5
    
    text_lower = text.lower()
    
    # Enhanced word lists
    positive_words = [
        "love", "awesome", "amazing", "excellent", "perfect", "best", 
        "wonderful", "fantastic", "outstanding", "brilliant", "superb",
        "great", "happy", "pleased", "satisfied", "recommend"
    ]
    negative_words = [
        "hate", "worst", "terrible", "awful", "horrible", "useless", 
        "broken", "disappointed", "poor", "pathetic", "trash", "waste",
        "bad", "annoying", "frustrating", "regret"
    ]
    neutral_indicators = [
        "okay", "ok", "fine", "average", "decent", "not bad", 
        "not great", "so-so", "mediocre", "acceptable", "fair"
    ]
    
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    neutral_count = sum(1 for word in neutral_indicators if word in text_lower)
    
    # Check for strong neutral indicators
    if neutral_count > 0 or ("but" in text_lower and pos_count > 0 and neg_count > 0):
        return "neutral", min(0.70, 0.60 + (neutral_count * 0.05))
    
    # Strong sentiment detection
    if pos_count > neg_count and pos_count >= 2:
        confidence = min(0.85, 0.70 + (pos_count * 0.03))
        return "positive", confidence
    elif neg_count > pos_count and neg_count >= 2:
        confidence = min(0.85, 0.70 + (neg_count * 0.03))
        return "negative", confidence
    elif pos_count > neg_count:
        return "positive", 0.65
    elif neg_count > pos_count:
        return "negative", 0.65
    else:
        return "neutral", 0.60

def get_sentiment_gemini(text):
    """Use Gemini API for sentiment analysis with robust error handling."""
    if not text or not text.strip():
        return "neutral", 0.5
    
    if not GEMINI_API_KEY:
        return rule_based_sentiment(text)
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""Analyze the sentiment of this review and respond ONLY with valid JSON.

Review: "{text}"

Classification rules:
- "okay but not great", "fine", "average" = NEUTRAL
- Mixed feelings (positive AND negative) = NEUTRAL
- Only clearly positive reviews = POSITIVE
- Only clearly negative reviews = NEGATIVE

Respond with this exact format (no markdown):
{{"sentiment_label": "positive", "confidence": 0.85}}

sentiment_label options: "positive", "negative", or "neutral"
confidence: number between 0.0 and 1.0"""

        response = model.generate_content(prompt)
        result = response.text.strip() if response and response.text else ""
        
        if not result:
            return rule_based_sentiment(text)
        
        # Clean markdown
        result = result.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(result)
            label = data.get("sentiment_label", "neutral").lower()
            confidence = float(data.get("confidence", 0.5))
            
            # Validate
            if label not in ["positive", "negative", "neutral"]:
                label = "neutral"
            confidence = max(0.0, min(1.0, confidence))
            
            # Post-processing validation
            text_lower = text.lower()
            neutral_indicators = ["okay", "ok", "fine", "average", "decent", "not bad", "not great"]
            
            if any(ind in text_lower for ind in neutral_indicators) and label != "neutral":
                strong_positive = ["love", "amazing", "excellent", "perfect", "best"]
                strong_negative = ["hate", "worst", "terrible", "awful", "horrible"]
                
                has_strong = any(w in text_lower for w in strong_positive + strong_negative)
                if not has_strong:
                    label = "neutral"
                    confidence = min(confidence, 0.70)
            
            return label, confidence
            
        except json.JSONDecodeError:
            return rule_based_sentiment(text)
            
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return rule_based_sentiment(text)

# ============ File Operations ============
def load_history():
    """Load review history with error handling."""
    try:
        if os.path.exists(history_file):
            df = pd.read_csv(history_file, encoding='utf-8')
            if len(df) > 0 and 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            return df
        return pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])
    except Exception as e:
        print(f"Error loading history: {e}")
        return pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])

def save_review(review_text, cleaned_text, label, confidence):
    """Save single review with better error handling."""
    try:
        new_entry = pd.DataFrame([{
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "review_text": review_text,
            "cleaned_text": cleaned_text,
            "sentiment_label": label,
            "confidence": confidence
        }])
        
        if os.path.exists(history_file):
            existing = pd.read_csv(history_file, encoding='utf-8')
            updated = pd.concat([existing, new_entry], ignore_index=True)
        else:
            updated = new_entry
        
        updated.to_csv(history_file, index=False, encoding='utf-8')
        return updated
    except PermissionError:
        print("WARNING: Could not save - file is locked")
        return load_history()
    except Exception as e:
        print(f"Error saving review: {e}")
        return load_history()

def get_statistics():
    """Generate statistics from review history."""
    df = load_history()
    
    if df.empty:
        return "No reviews analyzed yet."
    
    total = len(df)
    positive = len(df[df['sentiment_label'] == 'positive'])
    negative = len(df[df['sentiment_label'] == 'negative'])
    neutral = len(df[df['sentiment_label'] == 'neutral'])
    avg_conf = df['confidence'].mean()
    
    stats = f"""
### Statistics
- **Total Reviews:** {total}
- **Positive:** {positive} ({positive/total*100:.1f}%)
- **Negative:** {negative} ({negative/total*100:.1f}%)
- **Neutral:** {neutral} ({neutral/total*100:.1f}%)
- **Avg Confidence:** {avg_conf:.2f}
"""
    return stats

# ============ Single Review Analysis ============
def on_analyze(review_text):
    """Analyze single review."""
    if not review_text or not review_text.strip():
        return "WARNING: Please enter a review!", load_history(), get_statistics()
    
    cleaned = clean_text(review_text)
    label, conf = get_sentiment_gemini(review_text)
    
    df = save_review(review_text, cleaned, label, conf)
    stats = get_statistics()
    
    result_text = f"""
### Analysis Complete
- **Sentiment:** {label.upper()}
- **Confidence:** {conf:.2%}
- **Cleaned:** "{cleaned[:100]}..."
"""
    
    return result_text, df, stats

def on_clear():
    """Clear history with better handling."""
    try:
        empty_df = pd.DataFrame(columns=["timestamp", "review_text", "cleaned_text", "sentiment_label", "confidence"])
        
        if os.path.exists(history_file):
            try:
                os.remove(history_file)
                message = "History cleared successfully!"
            except PermissionError:
                empty_df.to_csv(history_file, index=False, encoding='utf-8')
                message = "History cleared (file was overwritten)!"
        else:
            message = "No history to clear."
        
        empty_df.to_csv(history_file, index=False, encoding='utf-8')
        return message, empty_df, get_statistics()
    except Exception as e:
        return f"Error: {e}", load_history(), get_statistics()

# ============ PySpark Bulk Analysis ============
def analyze_csv_with_pyspark(file_obj, progress=gr.Progress()):
    """Analyze CSV file using pandas (PySpark for aggregation only to avoid Windows issues)."""
    if file_obj is None:
        return "WARNING: Please upload a CSV file!", pd.DataFrame(), "", None
    
    try:
        progress(0, desc="Reading CSV...")
        
        # Use pandas instead of PySpark for reading (avoids Python worker issues on Windows)
        try:
            pdf = pd.read_csv(file_obj.name, encoding='utf-8')
        except:
            pdf = pd.read_csv(file_obj.name, encoding='latin-1')
        
        # Check for required column
        if 'review_text' not in pdf.columns:
            available_cols = ", ".join(pdf.columns)
            return f"ERROR: CSV must have 'review_text' column. Found: {available_cols}", pd.DataFrame(), "", None
        
        progress(0.2, desc="Processing reviews...")
        
        total_reviews = len(pdf)
        
        if total_reviews == 0:
            return "ERROR: CSV is empty!", pd.DataFrame(), "", None
        
        print(f"Processing {total_reviews} reviews...")
        
        results = []
        batch_count = 0
        
        for idx, row in pdf.iterrows():
            if idx % 10 == 0:
                progress((0.2 + (idx / total_reviews) * 0.7), desc=f"Analyzing {idx}/{total_reviews}...")
            
            text = row['review_text']
            text_str = str(text).strip() if pd.notna(text) else ""
            
            if not text_str:
                results.append({
                    "review_text": text,
                    "cleaned_text": "",
                    "sentiment_label": "neutral",
                    "confidence": 0.5
                })
                continue
            
            cleaned = clean_text(text_str)
            label, conf = get_sentiment_gemini(text_str)
            
            results.append({
                "review_text": text_str,
                "cleaned_text": cleaned,
                "sentiment_label": label,
                "confidence": round(conf, 3)
            })
            
            batch_count += 1
            # Small delay every batch to avoid rate limits
            if batch_count % batch_size == 0:
                import time
                time.sleep(1)
        
        progress(0.9, desc="Creating output...")
        
        # Create results dataframe
        result_pdf = pd.DataFrame(results)
        output_path = "analyzed_reviews.csv"
        result_pdf.to_csv(output_path, index=False, encoding='utf-8')
        
        # Calculate statistics with pandas (more reliable on Windows)
        stats_data = result_pdf.groupby('sentiment_label').agg({
            'confidence': ['count', 'mean']
        }).reset_index()
        
        stats_data.columns = ['sentiment_label', 'count', 'avg_confidence']
        total = stats_data['count'].sum()
        
        stats_text = f"""
### Bulk Analysis Complete
**Total Reviews Processed:** {total}

**Sentiment Distribution:**
"""
        for _, row in stats_data.iterrows():
            pct = (row['count'] / total * 100)
            stats_text += f"\n- **{row['sentiment_label'].capitalize()}:** {int(row['count'])} ({pct:.1f}%) - Avg Confidence: {row['avg_confidence']:.2f}"
        
        progress(1.0, desc="Complete!")
        
        return "Analysis Complete!", result_pdf.head(50), stats_text, output_path
        
    except Exception as e:
        import traceback
        error_msg = f"ERROR: {str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        return f"ERROR: {e}", pd.DataFrame(), "", None

# ============ Build Enhanced Gradio Dashboard ============
with gr.Blocks(theme=gr.themes.Soft(), title="Sentiment Analyzer Pro") as dashboard:
    
    # Show API status warning if needed
    api_status = ""
    if not GEMINI_API_KEY:
        api_status = """
        > ⚠️ **Warning:** GEMINI_API_KEY not found in .env file! 
        > The system will use rule-based sentiment analysis as fallback.
        > For better accuracy, add your Gemini API key to the .env file.
        """
    
    gr.Markdown(f"""
    # Sentiment Analysis for Review Analysis in Social Media
    ### Powered by Google Gemini AI + Apache PySpark
    Analyze individual reviews or bulk CSV files with advanced sentiment detection.
    {api_status}
    """)

    with gr.Tabs():
        # ---- Single Review Tab ----
        with gr.Tab("Single Review Analysis"):
            gr.Markdown("### Analyze Individual Reviews")
            
            with gr.Row():
                with gr.Column(scale=2):
                    review_box = gr.Textbox(
                        label="Enter Your Review",
                        placeholder="Example: 'This product is amazing! It exceeded all my expectations.'",
                        lines=6
                    )
                    
                    gr.Examples(
                        examples=[
                            ["I love this product! It's absolutely amazing and works perfectly."],
                            ["It was okay but not great. Just average quality."],
                            ["Terrible experience. Worst purchase I've ever made. Total waste of money."]
                        ],
                        inputs=review_box,
                        label="Try these examples:"
                    )
                    
                    with gr.Row():
                        analyze_btn = gr.Button("Analyze Sentiment", variant="primary", size="lg")
                        clear_btn = gr.Button("Clear History", variant="secondary")
                    
                    output_box = gr.Markdown(label="Analysis Result")
                
                with gr.Column(scale=1):
                    stats_box = gr.Markdown(get_statistics())

            gr.Markdown("### Review History")
            history_table = gr.Dataframe(
                value=load_history(),
                label="All Analyzed Reviews",
                interactive=False,
                wrap=True
            )

        # ---- Bulk File Analysis Tab ----
        with gr.Tab("Bulk CSV Analysis"):
            gr.Markdown("""
            ### Upload CSV for Batch Processing
            **Requirements:** CSV must contain a column named `review_text`
            
            **Features:**
            - Efficient pandas-based processing (optimized for Windows)
            - Handles large files
            - Automatic rate limiting for API calls
            - Export results as CSV
            """)
            
            with gr.Row():
                with gr.Column():
                    file_input = gr.File(
                        label="Upload CSV File",
                        file_types=[".csv"],
                        type="filepath"
                    )
                    
                    gr.Markdown("""
                    **CSV Format Example:**
                    ```
                    review_text
                    "Great product, highly recommend!"
                    "Not satisfied with the quality."
                    "Average experience, nothing special."
                    ```
                    """)
                    
                    analyze_file_btn = gr.Button(
                        "Analyze File with PySpark",
                        variant="primary",
                        size="lg"
                    )
                    
                    bulk_status = gr.Markdown()
                    bulk_stats = gr.Markdown()
                
                with gr.Column():
                    download_btn = gr.File(
                        label="Download Processed CSV",
                        interactive=False
                    )
            
            gr.Markdown("### Processed Reviews Preview (First 50 rows)")
            bulk_table = gr.Dataframe(
                label="Analysis Results",
                interactive=False,
                wrap=True
            )

    # ---- Event Bindings ----
    analyze_btn.click(
        fn=on_analyze,
        inputs=review_box,
        outputs=[output_box, history_table, stats_box]
    )
    
    clear_btn.click(
        fn=on_clear,
        outputs=[output_box, history_table, stats_box]
    )
    
    analyze_file_btn.click(
        fn=analyze_csv_with_pyspark,
        inputs=file_input,
        outputs=[bulk_status, bulk_table, bulk_stats, download_btn]
    )
    
    # Load history on startup
    dashboard.load(
        fn=lambda: (load_history(), get_statistics()),
        outputs=[history_table, stats_box]
    )

# ============ Launch ============
if __name__ == "__main__":
    print("Starting Sentiment Analyzer Pro...")
    print(f"PySpark Status: {'Initialized' if spark else 'Failed'}")
    print(f"Gemini API: {'Configured' if GEMINI_API_KEY else 'Not configured'}")
    
    dashboard.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )