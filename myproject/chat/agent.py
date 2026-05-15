# chat/agent.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

# دي عشان تخلي بايثون يقرا ملف الـ .env اللي إنت عملته
load_dotenv()

# سحب الـ API Key من الـ .env (أمان 100%)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

class SmartSignTalkAgent:
    def __init__(self):
        # Initialize the LLM (The Brain)
        self.llm = genai.GenerativeModel('gemini-2.5-flash')
        
        # The Dictionary and Ready Avatars
        self.ready_avatars = {
            "animal": "AnimalAvatar.glb",
            "answer": "AnswerAvatar.glb",
            "apple": "AppleAvatar.glb",
            "ask": "AskAvatar.glb",
            "aunt": "AuntAvatar.glb",
            "baby": "BabyAvatar.glb",
            "bad": "BadAvatar.glb",
            "balance": "BalanceAvatar.glb",
            "basketball": "BasketballAvatar.glb",
            "bathroom": "BathroomAvatar.glb",
            "bed": "bedAvatar.glb",
            "before": "BeforeAvatar.glb",
            "black": "BlackAvatar.glb",
            "blood": "BloodAvatar.glb",
            "book": "BookAvatar.glb",
            "bowling": "BowlingAvatar.glb",
            "brave": "BraveAvatar.glb",
            "brother": "BrotherAvatar.glb",
            "buy": "BuyAvatar.glb",
            "call": "CallAvatar.glb",
            "clean": "CleanAvatar.glb",
            "cold": "ColdAvatar.glb",
            "come": "ComeAvatar.glb",
            "computer": "ComputerAvatar.glb",
            "cook": "CookAvatar.glb",
            "cough": "CoughAvatar.glb",
            "cry": "CryAvatar.glb",
            "dad": "DadAvatar.glb",
            "danger": "DangerAvatar.glb",
            "day": "DayAvatar.glb",
            "deaf": "DeafAvatar.glb",
            "degree": "DegreeAvatar.glb",
            "delete": "DeleteAvatar.glb",
            "eclipse": "EclipseAvatar.glb",
            "equal": "EqualAvatar.glb",
            "everyone": "EveryoneAvatar.glb",
            "facecream": "FacecreamAvatar.glb",
            "future": "FutureAvatar.glb",
            "hello": "HelloAvatar.glb",
            "my_name_is": "My Name IsAvatar.glb", # ملحوظة: يفضل عدم استخدام مسافات في أسماء الملفات
            "my": "MyAvatar.glb",
            "new_year": "New YearAvatar.glb", # نفس الملحوظة
            "or": "OrAvatar.glb",
            "please": "PleaseAvatar.glb",
            "take": "TakeAvatar.glb",
            "this": "ThisAvatar.glb",
            "where": "WhereAvatar.glb",
            "which": "WhichAvatar.glb",
            "you": "YouAvatar.glb"
        }
        self.dictionary_keys = list(self.ready_avatars.keys())

# ==========================================
    # 1. Sign-to-Text (Processing SlowFast output)
    # ==========================================
    def process_slowfast_output(self, detected_words, confidence_score):
        if confidence_score < 0.50:
            return {
                "status": "warning",
                "message": "Sorry, the sign is unclear. Could you repeat it slowly?",
                "action": "request_retry"
            }

        # الـ Prompt الأكثر صرامة عشان نضمن جملة كاملة دايماً
        prompt = f"""
        You are a professional Sign Language to English interpreter.
        A deaf user just signed the following fragmented word(s): {detected_words}

        Your strict task:
        Convert these fragmented words into ONE complete, natural, and polite English sentence. 
        - You MUST add missing pronouns (I, you, he), verbs (am, is, want, need), or prepositions (to, in, on) to make it grammatically correct.
        - If it's a single word (e.g., 'apple'), make a logical sentence like 'I want an apple.' or 'I am eating an apple.'
        - If it's multiple words (e.g., 'theory, bed'), connect them logically: 'I am reading the theory in bed.' or 'I will study the theory in bed.'
        - DO NOT output any introductory text, DO NOT use quotes. JUST return the final sentence.
        """
        
        try:
            response = self.llm.generate_content(prompt)
            # تنظيف الرد من أي مسافات أو علامات تنصيص زيادة
            final_sentence = response.text.strip().replace('"', '').replace("'", "")
            
            return {
                "status": "success",
                "message": final_sentence,
                "confidence": confidence_score,
                "action": "display_text"
            }
        except Exception as e:
            # لو حصل أي خطأ في الاتصال بجوجل، هنرجع الكلمات كخطة بديلة
            return {
                "status": "success", 
                "message": " ".join(detected_words),
                "details": str(e)
            }

    # ==========================================
    # 2. Text-to-Sign (Reverse Translation)
    # ==========================================
    def process_text_to_sign(self, user_text):
        """
        Takes normal English text and converts it to a sequence of available avatar animations.
        """
        # --- إضافة أمر الـ Help هنا (عشان نرد بسرعة من غير ما نكلم Gemini) ---
        if user_text.strip().lower() in [r"\help", "/help", "help"]:
            words = ", ".join(self.dictionary_keys)
            return {
                "status": "success",
                "message": f"Here are the currently available sign language words: {words}",
                "animation_sequence": [] # بنبعتها فاضية عشان الفرونت إند ميعملش إيرور
            }
        # --
        prompt = f"""
        You are a smart Text-to-Sign-Language assistant. 
        The user entered the following English text: "{user_text}".
        You only have access to the following sign language dictionary: {self.dictionary_keys}.
        Extract the key words from the user's text that match or mean the same as the words in your dictionary.
        Return ONLY the matching words as a comma-separated list. If no words match, return the word "None".
        """
        
        try:
            response = self.llm.generate_content(prompt)
            # Clean the output and make it lowercase
            extracted_words = [word.strip().lower() for word in response.text.split(',')]
            
            # Filter words that have a ready avatar
            avatar_sequence = []
            for word in extracted_words:
                if word in self.ready_avatars:
                    avatar_sequence.append({
                        "word": word,
                        "url": f"/static/models/{self.ready_avatars[word]}"
                    })
            
            if not avatar_sequence:
                return {
                    "status": "failed",
                    "message": "Sorry, there are no avatars available for this text currently."
                }

            return {
                "status": "success",
                "message": "Animation sequence generated successfully.",
                "animation_sequence": avatar_sequence
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

# ==========================================
    # 3. Speech-to-Text (Voice Note Processing)
    # ==========================================
    def transcribe_audio(self, audio_bytes, mime_type="audio/webm"):
        prompt = "Listen to this audio and accurately transcribe it into English text. ONLY return the transcribed text, nothing else. If it's completely silent or unclear, return 'unclear'."
        try:
            # نبعت الصوت لـ Gemini عشان يفرغه
            response = self.llm.generate_content([
                prompt,
                {"mime_type": mime_type, "data": audio_bytes}
            ])
            text = response.text.strip()
            
            if "unclear" in text.lower() or not text:
                return {"status": "error", "message": "Audio is unclear"}
                
            return {"status": "success", "text": text}
        except Exception as e:
            return {"status": "error", "message": str(e)}
# ==========================================
# Quick Agent Testing
# ==========================================
if __name__ == "__main__":
    agent = SmartSignTalkAgent()
    
    print("\n--- Test 1: SlowFast Output (Sign to Text) ---")
    result1 = agent.process_slowfast_output(["I", "sick", "doctor"], 0.80)
    print(result1)
    
    print("\n--- Test 2: Low Confidence ---")
    result2 = agent.process_slowfast_output(["bed", "what"], 0.35)
    print(result2)

    print("\n--- Test 3: Normal User Input (Text to Sign) ---")
    result3 = agent.process_text_to_sign("I am a doctor, I need you to rest in bed and eat an apple.")
    print(result3)